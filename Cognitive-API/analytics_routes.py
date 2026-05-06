import matplotlib
matplotlib.use('Agg') # Importante: Define backend não-interativo para servidor
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import traceback
import re
from fastapi import APIRouter, HTTPException
import psycopg2
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

router = APIRouter()

# Configuração do Banco de Dados
DB_URL = os.environ.get("NEON_DB_URL", "postgres://user:password@localhost:5432/db").strip()

# --- MAPAS DE DEFINIÇÃO (GLOBAL) ---
# Mapeia o ID do banco para o Nome da Emoção
EMOCOES_MAP = {
    1: "Feliz",
    2: "Triste",
    3: "Medo",
    4: "Surpreso",
    5: "Raiva",
    6: "Envergonhado",
    7: "Constrangido",
    8: "Receoso",
    9: "Apático",
    10: "Deprimido",
    11: "Irritado"
}

# Mapeia o ID da Emoção para uma Nota de Bem-Estar (0 a 10) estimativa
# Usado quando o paciente não escreve "Bem-estar: X" no texto
SCORES_PADRAO = {
    1: 9.0,  # Feliz -> Muito Bom
    2: 3.0,  # Triste -> Ruim
    3: 3.0,  # Medo -> Ruim
    4: 6.0,  # Surpreso -> Neutro/Positivo
    5: 2.0,  # Raiva -> Muito Ruim
    6: 4.0,  # Envergonhado -> Baixo
    7: 4.0,  # Constrangido -> Baixo
    8: 4.0,  # Receoso -> Baixo
    9: 3.0,  # Apático -> Ruim
    10: 1.0, # Deprimido -> Crítico
    11: 2.0  # Irritado -> Muito Ruim
}

def get_db_connection():
    if not DB_URL or "user:password" in DB_URL:
        load_dotenv()
        url_retry = os.environ.get("NEON_DB_URL", "").strip()
        if not url_retry:
             raise Exception("NEON_DB_URL não configurada no arquivo .env!")
        return psycopg2.connect(url_retry)
    return psycopg2.connect(DB_URL)

def fig_to_base64():
    """Função auxiliar para converter o plot atual em Base64"""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return img

def extrair_bem_estar(texto):
    """
    Procura por 'Bem-estar: X' ou 'Bem-estar: X/10' no texto
    Retorna o valor inteiro ou None se não achar.
    """
    if not isinstance(texto, str):
        return None
    
    # Regex para capturar número após "Bem-estar:"
    # Aceita "Bem-estar: 2", "Bem-estar: 2/10", "Bem-estar:  05"
    match = re.search(r"Bem-estar:\s*(\d+)", texto, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except:
            return None
    return None

@router.get("/relatorios/analise/{paciente_id}")
def gerar_relatorio_paciente(paciente_id: int):
    print(f"--- [ROUTE FILE] Gerando relatório INTELIGENTE (Map fixo) para Paciente {paciente_id} ---")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Busca dados
        query = """
            SELECT data_hora_iso, sentimento_id, anotacao 
            FROM entradas_diario 
            WHERE paciente_id = %s 
            ORDER BY data_hora_iso ASC
        """
        cursor.execute(query, (paciente_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail="Paciente sem registros.")

        # 2. DataFrame
        df = pd.DataFrame(rows, columns=['data_hora_iso', 'sentimento_id', 'anotacao'])
        
        # 3. Tratamento de Datas
        df['data'] = pd.to_datetime(df['data_hora_iso'], errors='coerce')
        df = df.dropna(subset=['data'])
        df['data_simples'] = df['data'].dt.strftime('%d/%m')

        # 4. ALGORITMO DE SCORE BASEADO NO MAPA
        
        def calcular_score_real(row):
            humor_id = row['sentimento_id']
            texto = row['anotacao']
            
            # Pega o score base do mapa. Se não existir, assume neutro (5.0)
            score_humor = SCORES_PADRAO.get(humor_id, 5.0)
            
            # Busca 'Bem-estar' no texto para refinar
            bem_estar_txt = extrair_bem_estar(texto)
            
            if bem_estar_txt is not None:
                # Se o paciente escreveu a nota, fazemos uma média ponderada
                # Damos mais peso (2x) para o que ele escreveu do que para o ícone
                return (score_humor + (bem_estar_txt * 2)) / 3
            else:
                return score_humor

        df['score_final'] = df.apply(calcular_score_real, axis=1)

        # Labels corretas para o gráfico de barras usando EMOCOES_MAP
        def get_label(row):
            humor_id = row['sentimento_id']
            # Usa o mapa oficial, se não achar, usa "Outro"
            return EMOCOES_MAP.get(humor_id, f"Outro ({humor_id})")

        df['humor_label'] = df.apply(get_label, axis=1)

        # --- GERAÇÃO DOS GRÁFICOS ---
        
        # Gráfico 1: Evolução
        plt.figure(figsize=(10, 5))
        df_diario = df.groupby('data')['score_final'].mean()
        
        # Cor da linha muda conforme a média geral (Visualização dinâmica)
        media_geral = df['score_final'].mean()
        cor_linha = '#92C7A3' if media_geral >= 5 else '#FF6B6B' # Verde ou Vermelho
        
        plt.plot(df_diario.index, df_diario.values, marker='o', linestyle='-', color=cor_linha, linewidth=3)
        plt.title('Evolução do Bem-Estar (0 a 10)', color='#4a4939')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.ylim(0, 11) # Fixa eixo Y de 0 a 10
        plt.ylabel('Nível de Bem-Estar')
        plt.gcf().autofmt_xdate()
        grafico1 = fig_to_base64()

        # Gráfico 2: Barras
        plt.figure(figsize=(10, 5))
        contagem = df['humor_label'].value_counts()
        contagem.plot(kind='bar', color='#76a885')
        plt.title('Frequência de Emoções', color='#4a4939')
        plt.xticks(rotation=0)
        grafico2 = fig_to_base64()

        # Resumo Inteligente
        
        # Novas faixas de classificação
        if media_geral >= 7.5:
            status = "Positivo"
        elif media_geral >= 5.0:
            status = "Estável"
        elif media_geral >= 3.0:
            status = "Atenção"
        else:
            status = "Crítico"

        resumo = f"Baseado em {len(df)} registros. Pontuação Geral: {media_geral:.1f}/10 ({status})."
        
        # Verifica se a última entrada foi negativa
        ultima_nota = df.iloc[-1]['score_final']
        if ultima_nota < 4:
            resumo += " Atenção: O registro mais recente indica baixo bem-estar."

        return {
            "grafico_evolucao_base64": grafico1,
            "grafico_distribuicao_base64": grafico2,
            "resumo_texto": resumo
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print("ERRO NO ANALYTICS ROUTES:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
    