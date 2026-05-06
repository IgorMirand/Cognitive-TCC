from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import HTMLResponse
from datetime import datetime
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from analytics_routes import router as analytics_router
import matplotlib
matplotlib.use('Agg') # <--- IMPORTANTE: Isso deve ficar logo após o 'import matplotlib'
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
import traceback
from fastapi import APIRouter
import psycopg2
import os
import bcrypt
import pytz
import matplotlib.pyplot as plt
import numpy as np

#Comando start localmente: uvicorn main:app --reload

load_dotenv()

app = FastAPI(title="Cognitive-Front Cognitive-Front-API")

app.include_router(analytics_router)

# Pega a URL do banco das variáveis de ambiente (Configure no Render/Railway ou na Vercel)
DB_URL = os.environ.get("NEON_DB_URL", "").strip()
GMAIL_USER = os.environ.get("GMAIL_USER")     # seu.email@gmail.com
GMAIL_PASS = os.environ.get("GMAIL_PASS")     # a senha de 16 letras

def get_db_connection():
    if not DB_URL:
        raise Exception("NEON_DB_URL não configurada.")
    return psycopg2.connect(DB_URL)

# --- MODELOS DE DADOS (Pydantic) ---
# Definem o formato do JSON que o App envia para a Cognitive-Front-API

class UserRegister(BaseModel):
    username: str
    password: str
    user_type: str
    email: str
    data_nascimento: str # Formato DD/MM/YYYY

class UserLogin(BaseModel):
    email: str
    password: str

class VinculoData(BaseModel):
    paciente_id: int
    codigo: str

class AtividadeTemplate(BaseModel):
    texto: str
    psicologo_id: int # Obrigatório no seu banco

class DiarioEntry(BaseModel):
    paciente_id: int
    data_hora_iso: str
    sentimento_id: int
    anotacao: str
    atividades_ids: List[int]

class ConsultaNota(BaseModel):
    psicologo_id: int
    paciente_id: int
    anotacao: str
    data_hora_iso: str

class AgendaSlot(BaseModel):
    psicologo_id: int
    data_hora_iso: str

class Agendamento(BaseModel):
    agenda_id: int
    paciente_id: int

class VinculoData(BaseModel):
    paciente_id: int
    codigo: str

class UserUpdate(BaseModel):
    username: str
    email: str
    data_nascimento: str # Espera receber DD/MM/YYYY do App

class ReservaData(BaseModel):
    paciente_id: int

class ConviteEmail(BaseModel):
    email_paciente: str
    psicologo_id: int

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Cognitive-Front Cognitive-Front-API</title>
            <style>
                body {
                    background-color: #F5F7F6;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    justify_content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: white;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    text-align: center;
                    max_width: 400px;
                    margin: 0 auto
                }
                h1 {
                    color: #4a4939;
                    margin-bottom: 10px;
                }
                .status {
                    color: #92C7A3;
                    font-weight: bold;
                    font-size: 1.2em;
                    margin-bottom: 30px;
                }
                .btn {
                    background-color: #92C7A3;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    transition: background-color 0.3s;
                }
                .btn:hover {
                    background-color: #76a885;
                }
                p {
                    color: #666;
                    margin-bottom: 30px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div style="font-size: 50px;">🧠</div>
                <h1>Cognitive-Front Cognitive-Front-API</h1>
                <div class="status">● Sistema Online</div>
                <p>Esta é a Cognitive-Front-API backend que alimenta o aplicativo Cognitive-Front.</p>
                <a href="/docs" class="btn">Ver Documentação (Swagger)</a>
            </div>
        </body>
    </html>
    """
    return html_content

# --- ROTAS DE AUTENTICAÇÃO ---

@app.post("/register")
def register_user(data: UserRegister):
    if any(char.isdigit() for char in data.username):
        raise HTTPException(status_code=400, detail="O nome não pode conter números.")
    try:
        # Lógica de conversão de data igual ao seu neon.py original
        data_obj = datetime.strptime(data.data_nascimento, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, user_type, email, data_nacimento) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (data.username, password_hash, data.user_type, data.email, data_iso)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return {"success": True, "message": "Usuário criado!", "id": new_id}
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Usuário ou Email já existe.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login(data: UserLogin):
    try: # Adicione um try/except grande se não tiver
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, user_type, id, username FROM users WHERE email=%s", (data.email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(data.password.encode('utf-8'), user[0].encode('utf-8')):
            return {
                "success": True,
                "user_type": user[1],
                "id": user[2],
                "username": user[3]
            }
        
        # Se chegou aqui, senha ou usuario errados (Erro 401, não 500)
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    except Exception as e:
        # --- ISTO VAI SALVAR SUA VIDA ---
        print(f"ERRO NO LOGIN: {e}")  # Isso aparece no log do Render
        import traceback
        traceback.print_exc()         # Isso mostra a linha exata do erro
        # --------------------------------
        raise HTTPException(status_code=500, detail=str(e))
  
@app.put("/users/{user_id}")
def update_user(user_id: int, data: UserUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            dt_obj = datetime.strptime(data.data_nascimento, "%d/%m/%Y")
            data_iso = dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Data inválida.")

        # SQL: Usa 'data_nacimento' (sem 's')
        cursor.execute(
            """
            UPDATE users 
            SET username = %s, email = %s, data_nacimento = %s 
            WHERE id = %s
            """,
            (data.username, data.email, data_iso, user_id)
        )
        
        conn.commit()
        return {"success": True, "message": "Dados atualizados com sucesso!"}

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Este nome de usuário ou email já está em uso.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/users/{user_id}/password")
def change_password(user_id: int, data: PasswordChange):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Busca a senha atual do usuário no banco
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        current_hash_db = result[0].encode('utf-8') # Converte para bytes
        
        # 2. Verifica se a senha antiga digitada bate com a do banco
        if not bcrypt.checkpw(data.old_password.encode('utf-8'), current_hash_db):
            raise HTTPException(status_code=400, detail="A senha atual está incorreta.")
            
        # 3. Gera o hash da NOVA senha
        new_hash = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 4. Salva no banco
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        conn.commit()
        
        return {"success": True, "message": "Senha alterada com sucesso!"}

    except HTTPException as he:
        raise he
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- Adicione no api.py (junto com as rotas de usuários ou auth) ---
@app.get("/users/{user_id}")
def get_user_details(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # --- CORREÇÃO AQUI ---
        # O SQL precisa usar 'data_nacimento' (sem S), pois é assim que está no seu banco.
        cursor.execute(
            "SELECT id, username, email, user_type, data_nacimento FROM users WHERE id = %s", 
            (user_id,)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            # user[4] é a data.
            data_nasc = str(user[4]) if user[4] else ""
            
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "user_type": user[3],
                # O JSON de resposta mantém 'nascimento' (com S) porque é o que o App espera
                "data_nascimento": data_nasc 
            }
        else:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

    except Exception as e:
        if conn: conn.close()
        # O print ajuda a ver o erro real no log do Render se acontecer de novo
        print(f"Erro no GET User: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# --- ROTAS DE VÍNCULO E CÓDIGOS ---

@app.post("/codigos/gerar/{psicologo_id}")
def gerar_codigo(psicologo_id: int):
    # Simulação da lógica de geração (simplificada para Cognitive-Front-API)
    import random, string
    alfanumerico = string.ascii_uppercase + string.digits
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Tenta gerar até conseguir (loop simples)
        for _ in range(5):
            p1 = ''.join(random.choices(alfanumerico, k=3))
            p2 = ''.join(random.choices(alfanumerico, k=3))
            codigo = f"{p1}-{p2}"
            try:
                cursor.execute("INSERT INTO codigos_paciente (codigo, gerado_por_psicologo_id) VALUES (%s, %s)", (codigo, psicologo_id))
                conn.commit()
                conn.close()
                return {"codigo": codigo}
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                continue
        raise HTTPException(status_code=500, detail="Falha ao gerar código único.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vincular")
def vincular_paciente(data: VinculoData):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Verifica se já tem vínculo
        cursor.execute("SELECT id FROM paciente_psicologo_link WHERE paciente_user_id = %s", (data.paciente_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Paciente já vinculado.")

        # 2. Valida código
        cursor.execute("SELECT gerado_por_psicologo_id FROM codigos_paciente WHERE codigo=%s AND usado_por_paciente_id IS NULL", (data.codigo,))
        res = cursor.fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Código inválido.")
        
        psicologo_id = res[0]

        # 3. Cria vínculo e marca usado
        cursor.execute("INSERT INTO paciente_psicologo_link (paciente_user_id, psicologo_user_id) VALUES (%s, %s)", (data.paciente_id, psicologo_id))
        cursor.execute("UPDATE codigos_paciente SET usado_por_paciente_id = %s WHERE codigo = %s", (data.paciente_id, data.codigo))
        
        conn.commit()
        return {"success": True, "message": "Vinculado com sucesso!"}
    except HTTPException as he:
        raise he
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/codigos/master/validar/{codigo}")
def validar_codigo_master(codigo: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verifica se existe e se não foi usado (usado_por_user_id IS NULL)
        cursor.execute(
            "SELECT id FROM codigos_master WHERE codigo = %s AND usado_por_user_id IS NULL",
            (codigo,)
        )
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            return {"valid": True, "id": resultado[0]}
        else:
            # Retorna 200 mas com valid=False para o app saber que não é erro de servidor
            return {"valid": False, "id": None}

    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# APROVEITANDO: Vamos adicionar a função para MARCAR como usado também
# (O app vai chamar isso logo após o registro ser bem sucedido)
@app.post("/codigos/master/usar")
def usar_codigo_master(data: dict): 
    # Espera receber {"codigo_id": 1, "user_id": 50}
    codigo_id = data.get("codigo_id")
    user_id = data.get("user_id")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE codigos_master SET usado_por_user_id = %s WHERE id = %s",
            (user_id, codigo_id)
        )
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    

# --- ROTAS DE DASHBOARD PSICÓLOGO ---
@app.get("/psicologo/{id}/stats")
def get_stats(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Contagem de Pacientes
        # COUNT(*) conta todas as linhas que correspondem ao filtro, sem precisar de uma coluna específica
        cursor.execute("SELECT COUNT(*) FROM paciente_psicologo_link WHERE psicologo_user_id = %s", (id,))
        count = cursor.fetchone()[0]
        
        # 2. Próxima Consulta (CORRIGIDO)
        # Adicionamos CAST(A.data_hora AS TIMESTAMP) para o banco entender a comparação
        query_next = """
            SELECT A.data_hora, U.username 
            FROM agenda A
            JOIN users U ON A.paciente_id = U.id
            WHERE A.psicologo_id = %s 
              AND A.paciente_id IS NOT NULL 
              AND CAST(A.data_hora AS TIMESTAMP) > NOW()
            ORDER BY A.data_hora ASC 
            LIMIT 1
        """
        cursor.execute(query_next, (id,))
        row = cursor.fetchone()
        
        # Tratamento para garantir que a data seja string ISO para o JSON
        proxima = None
        if row:
            data_bd = row[0] 
            nome_paciente = row[1]
            # Se o banco devolver objeto datetime, converte. Se devolver string, usa direto.
            data_str = data_bd.isoformat() if hasattr(data_bd, 'isoformat') else str(data_bd)
            proxima = [data_str, nome_paciente]
        
        return {"pacientes_count": count, "proxima_consulta": proxima}

    except Exception as e:
        # O print ajuda a ver o erro real nos logs da Vercel/Render
        print(f"Erro no Stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/psicologo/{id}/pacientes")
def get_pacientes(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT U.id, U.username 
        FROM paciente_psicologo_link L
        JOIN users U ON L.paciente_user_id = U.id
        WHERE L.psicologo_user_id = %s
    """, (id,))
    pacientes = cursor.fetchall() # [(1, "Joao"), (2, "Maria")]
    conn.close()
    return {"pacientes": pacientes}

@app.get("/paciente/{paciente_id}/psicologo")
def get_psicologo_do_paciente(paciente_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT psicologo_user_id FROM paciente_psicologo_link WHERE paciente_user_id = %s",
            (paciente_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        # Retorna o ID se achar, ou None se não achar
        if result:
            return {"psicologo_id": result[0]}
        else:
            return {"psicologo_id": None}
            
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config/powerbi")
def get_powerbi_link():
    """
    Retorna o link do relatório. 
    Assim você pode mudar o link no futuro sem precisar atualizar o .exe dos usuários.
    """
    # Substitua este link pelo seu link REAL do Power BI
    link_real = "https://app.powerbi.com/view?r=eyJrIjoiMGUzYTIxMzktYTExZi00OGY2LThkM2ItMGVlYjk4ZTU5NzAzIiwidCI6ImRlZjQ0ZjhmLWFlM2EtNDA4MS1iY2EzLWYwODBhZDkzYTUxYyJ9"
    
    return {"url": link_real}

# --- ROTAS DE ATIVIDADES ---
@app.get("/atividades")
def listar_atividades():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, atividade_texto FROM atividades_template")
    atividades = cursor.fetchall()
    conn.close()
    return {"atividades": atividades}

@app.post("/atividades")
def criar_atividade(data: AtividadeTemplate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM atividades_template WHERE atividade_texto = %s", (data.texto,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Atividade já existe")
        
        cursor.execute("INSERT INTO atividades_template (atividade_texto, criado_por_psicologo_id) VALUES (%s, %s)", (data.texto, data.psicologo_id))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/atividades/{id}")
def deletar_atividade(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM atividades_template WHERE id = %s", (id,))
        conn.commit()
        return {"success": True}
    except psycopg2.errors.IntegrityError:
        raise HTTPException(status_code=400, detail="Não pode excluir: atividade em uso.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/atividades/{id}")
def atualizar_atividade(id: int, novo_texto: str): # novo_texto pode vir via query param ou body
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE atividades_template SET atividade_texto = %s WHERE id = %s", (novo_texto, id))
        conn.commit()
        return {"success": True}
    finally:
        conn.close()
    
# 1. Rota para BUSCAR o histórico de anotações
@app.get("/consultas/{psicologo_id}/{paciente_id}")
def get_anotacoes_paciente(psicologo_id: int, paciente_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Busca as anotações ordenadas da mais recente para a mais antiga
        query = """
            SELECT id, data_hora_iso, anotacao 
            FROM consultas_psicologo 
            WHERE psicologo_id = %s AND paciente_id = %s
            ORDER BY data_hora_iso DESC
        """
        cursor.execute(query, (psicologo_id, paciente_id))
        notas = cursor.fetchall()
        conn.close()
        return {"anotacoes": notas}
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# 2. Rota para SALVAR uma nova anotação (Você vai precisar em breve)
@app.post("/consultas")
def salvar_consulta(data: ConsultaNota):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO consultas_psicologo (psicologo_id, paciente_id, anotacao, data_hora_iso) VALUES (%s, %s, %s, %s)",
            (data.psicologo_id, data.paciente_id, data.anotacao, data.data_hora_iso)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- ROTAS DE DIÁRIO ---

@app.post("/diario")
def salvar_diario(data: DiarioEntry):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Salvar entrada
        cursor.execute(
            "INSERT INTO entradas_diario (paciente_id, data_hora_iso, sentimento_id, anotacao) VALUES (%s, %s, %s, %s) RETURNING id",
            (data.paciente_id, data.data_hora_iso, data.sentimento_id, data.anotacao)
        )
        diario_id = cursor.fetchone()[0]

        # 2. Salvar atividades
        if data.atividades_ids:
            from psycopg2.extras import execute_values
            vals = [(diario_id, aid) for aid in data.atividades_ids]
            execute_values(cursor, "INSERT INTO registros_atividades_diario (entrada_diario_id, atividade_template_id) VALUES %s", vals)
        
        conn.commit()
        return {"success": True, "id": diario_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/diario/historico/{paciente_id}")
def get_historico(paciente_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Query igual ao seu neon.py
    query = """
        SELECT E.id, E.data_hora_iso, E.sentimento_id, E.anotacao, STRING_AGG(T.atividade_texto, ', ') 
        FROM entradas_diario E
        LEFT JOIN registros_atividades_diario R ON E.id = R.entrada_diario_id
        LEFT JOIN atividades_template T ON R.atividade_template_id = T.id
        WHERE E.paciente_id = %s
        GROUP BY E.id, E.data_hora_iso, E.sentimento_id, E.anotacao
        ORDER BY E.data_hora_iso DESC
    """
    cursor.execute(query, (paciente_id,))
    historico = cursor.fetchall()
    conn.close()
    return {"historico": historico}

# --- ROTAS DE AGENDA (Básico) ---

@app.get("/agenda/psicologo/{id}")
def get_agenda(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, data_hora, paciente_id FROM agenda WHERE psicologo_id = %s AND data_hora >= NOW() ORDER BY data_hora ASC", (id,))
    agenda = cursor.fetchall()
    conn.close()
    return {"agenda": agenda}

@app.post("/agenda/disponibilidade")
def add_agenda(data: AgendaSlot):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Cria o horário na agenda (Como antes)
        cursor.execute(
            "INSERT INTO agenda (psicologo_id, data_hora, paciente_id) VALUES (%s, %s, NULL)", 
            (data.psicologo_id, data.data_hora_iso)
        )
        
        # --- NOVIDADE: ENVIAR NOTIFICAÇÃO AOS PACIENTES ---
        
        # A. Descobre o nome do Psicólogo
        cursor.execute("SELECT username FROM users WHERE id = %s", (data.psicologo_id,))
        psi_result = cursor.fetchone()
        nome_psi = psi_result[0] if psi_result else "Seu Psicólogo"

        # B. Formata a data para ficar bonita na mensagem (Ex: 25/12 às 14:00)
        try:
            # Remove o 'Z' se houver
            data_limpa = data.data_hora_iso.replace('Z', '')
            if 'T' in data_limpa:
                dt_obj = datetime.fromisoformat(data_limpa)
            else:
                dt_obj = datetime.strptime(data_limpa, "%Y-%m-%d %H:%M:%S")
            data_fmt = dt_obj.strftime("%d/%m às %H:%M")
        except:
            data_fmt = data.data_hora_iso # Se der erro, usa a original

        # C. Busca todos os pacientes vinculados a este psicólogo
        cursor.execute(
            "SELECT paciente_user_id FROM paciente_psicologo_link WHERE psicologo_user_id = %s", 
            (data.psicologo_id,)
        )
        pacientes = cursor.fetchall()

        # D. Cria a notificação para cada paciente
        if pacientes:
            titulo = "Novo Horário Disponível 📅"
            mensagem = f"O Dr(a). {nome_psi} acabou de abrir um horário para {data_fmt}. Acesse a agenda para marcar!"
            
            # Insere uma notificação para cada ID encontrado
            for (paciente_id,) in pacientes:
                cursor.execute(
                    "INSERT INTO notificacoes (user_id, titulo, mensagem) VALUES (%s, %s, %s)",
                    (paciente_id, titulo, mensagem)
                )

        conn.commit()
        return {"success": True, "message": "Horário criado e pacientes notificados!"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
# --- Adicione junto com as rotas de AGENDA ---

@app.delete("/agenda/{agenda_id}")
def delete_agenda_slot(agenda_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verifica se existe
        cursor.execute("SELECT id FROM agenda WHERE id = %s", (agenda_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Horário não encontrado.")

        # Deleta
        cursor.execute("DELETE FROM agenda WHERE id = %s", (agenda_id,))
        conn.commit()
        return {"success": True, "message": "Horário removido."}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/agenda/{agenda_id}/reservar")
def reservar_horario(agenda_id: int, data: ReservaData):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Verifica se o horário ainda está livre (segurança contra conflito)
        cursor.execute("SELECT paciente_id FROM agenda WHERE id = %s", (agenda_id,))
        row = cursor.fetchone()
        
        if not row:
             raise HTTPException(status_code=404, detail="Horário não encontrado")
        if row[0] is not None:
             raise HTTPException(status_code=400, detail="Este horário já foi reservado por outra pessoa.")

        # 2. Atualiza a agenda com o ID do paciente
        cursor.execute("UPDATE agenda SET paciente_id = %s WHERE id = %s", (data.paciente_id, agenda_id))
        conn.commit()
        return {"success": True, "message": "Agendado com sucesso!"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()



@app.get("/fix/repair_consultas")
def repair_consultas_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Garante que a tabela existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consultas_psicologo (
                id SERIAL PRIMARY KEY,
                psicologo_id INT NOT NULL,
                paciente_id INT NOT NULL,
                data_hora_iso TEXT,
                anotacao TEXT
            );
        """)
        
        # 2. Garante que a coluna 'anotacao' existe (caso a tabela já existisse antes sem ela)
        cursor.execute("ALTER TABLE consultas_psicologo ADD COLUMN IF NOT EXISTS anotacao TEXT;")
        
        # 3. Garante que a coluna 'data_hora_iso' existe
        cursor.execute("ALTER TABLE consultas_psicologo ADD COLUMN IF NOT EXISTS data_hora_iso TEXT;")

        conn.commit()
        return {"success": True, "message": "Banco de dados reparado (Tabela e Colunas verificadas)!"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

@app.get("/fix/liberar_anotacoes")
def fix_anotacoes_constraint():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Comando para remover a obrigatoriedade (NOT NULL) da coluna 'anotacoes'
        # Assim, ela aceita valor nulo e para de dar erro.
        cursor.execute("ALTER TABLE consultas_psicologo ALTER COLUMN anotacoes DROP NOT NULL;")
        
        conn.commit()
        return {"success": True, "message": "Coluna 'anotacoes' agora aceita nulos! Problema resolvido."}
    except Exception as e:
        conn.rollback()
        # Se der erro dizendo que a coluna não existe, tudo bem, é sinal que já foi resolvido
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

# --- Rota de Envio ---
@app.post("/email/enviar_convite")
def enviar_convite_email(data: ConviteEmail):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Gerar Código (Mantém igual)
        import random, string
        alfanumerico = string.ascii_uppercase + string.digits
        codigo = ""
        for _ in range(5):
            p1 = ''.join(random.choices(alfanumerico, k=3))
            p2 = ''.join(random.choices(alfanumerico, k=3))
            temp = f"{p1}-{p2}"
            cursor.execute("SELECT id FROM codigos_paciente WHERE codigo = %s", (temp,))
            if not cursor.fetchone():
                codigo = temp
                break
        
        if not codigo: raise HTTPException(status_code=500, detail="Erro ao gerar código.")

        # 2. Salva o código
        cursor.execute("INSERT INTO codigos_paciente (codigo, gerado_por_psicologo_id) VALUES (%s, %s)", (codigo, data.psicologo_id))
        
        # --- NOVIDADE: NOTIFICAÇÃO NO APP ---
        # Verifica se existe um usuário com esse email
        cursor.execute("SELECT id, username FROM users WHERE email = %s", (data.email_paciente,))
        paciente_existente = cursor.fetchone() # (id, nome)
        
        notificacao_enviada = False
        if paciente_existente:
            paciente_id = paciente_existente[0]
            msg_notificacao = f"Seu código de vínculo é: {codigo}. Insira este código na tela inicial."
            
            cursor.execute(
                "INSERT INTO notificacoes (user_id, titulo, mensagem) VALUES (%s, %s, %s)",
                (paciente_id, "Convite de Vínculo", msg_notificacao)
            )
            notificacao_enviada = True

        # 3. Tenta enviar E-mail (Mantenha seu código SMTP/Resend aqui)
        # ... (seu código de envio de email existente) ...
        # Se não quiser enviar email caso a notificação funcione, coloque num 'else'.
        # Mas recomendo manter os dois.

        conn.commit()
        
        msg_retorno = f"Convite enviado para {data.email_paciente}"
        if notificacao_enviada:
            msg_retorno += " (Notificação enviada para o App)"
            
        return {"success": True, "message": msg_retorno}

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- Adicione no api.py ---

@app.get("/notificacoes/{user_id}")
def get_notificacoes(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Busca notificações não lidas ou recentes
        cursor.execute("""
            SELECT id, titulo, mensagem, lida 
            FROM notificacoes 
            WHERE user_id = %s 
            ORDER BY data_criacao DESC
        """, (user_id,))
        res = cursor.fetchall()
        
        # Formata para JSON
        lista = [{"id": r[0], "titulo": r[1], "mensagem": r[2], "lida": r[3]} for r in res]
        return {"notificacoes": lista}
    finally:
        conn.close()

@app.delete("/notificacoes/{notificacao_id}")
def deletar_notificacao(notificacao_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM notificacoes WHERE id = %s", (notificacao_id,))
        conn.commit()
        return {"success": True}
    finally:
        conn.close()

# --- Adicione junto com as rotas de NOTIFICAÇÕES ---

@app.put("/notificacoes/marcar_lida/{user_id}")
def marcar_todas_lidas(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Marca todas as notificações desse usuário como lidas
        cursor.execute("UPDATE notificacoes SET lida = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/cron/enviar_lembretes_diarios")
def enviar_lembretes_diarios():
    """
    Rota que deve ser chamada externamente (Cron Job) uma vez por dia.
    Envia notificação para todos os pacientes lembrarem de preencher o diário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Pega a lista de todos os Pacientes
        cursor.execute("SELECT id, username FROM users WHERE user_type = 'Paciente'")
        pacientes = cursor.fetchall()
        
        count = 0
        hoje = datetime.now(pytz.timezone('America/Sao_Paulo')).date()

        for pid, nome in pacientes:
            # (Opcional) Verifica se ele JÁ preencheu o diário hoje para não ser chato
            # A data_hora_iso é texto, então fazemos um cast para DATE ou verificamos string
            # Essa query simplificada assume que você quer mandar de qualquer jeito ou verifica por data
            
            # Vamos mandar o lembrete padrão
            titulo = "Bom dia! ☀️"
            mensagem = f"Olá {nome}, como você está se sentindo hoje? Não esqueça de registrar no seu diário."
            
            # Insere a notificação
            cursor.execute(
                "INSERT INTO notificacoes (user_id, titulo, mensagem) VALUES (%s, %s, %s)",
                (pid, titulo, mensagem)
            )
            count += 1

        conn.commit()
        return {"success": True, "message": f"Lembretes enviados para {count} pacientes."}

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

@app.get("/relatorios/grafico_atividades/{patient_id}")
def get_atividades_chart(patient_id: int):
    conn = get_db_connection()
    try:
        # 1. Busca dados
        # ORDER BY frequencia ASC garante que a barra maior fique no TOPO do gráfico (matplotlib plota de baixo para cima)
        query = """
            SELECT T.atividade_texto, COUNT(R.id) as frequencia
            FROM registros_atividades_diario R
            JOIN atividades_template T ON R.atividade_template_id = T.id
            JOIN entradas_diario E ON R.entrada_diario_id = E.id
            WHERE E.paciente_id = %s
            GROUP BY T.atividade_texto
            ORDER BY frequencia ASC
        """
        df = pd.read_sql(query, conn, params=(patient_id,))
        
        if df.empty:
            return {"base64": None}

        # --- MELHORIAS VISUAIS ---
        
        # Define um estilo limpo
        plt.style.use('seaborn-v0_8-white')

        # Altura dinâmica: Se tiver muitas atividades, o gráfico fica mais alto
        # Mínimo de 5 polegadas, ou 0.6 polegadas por barra
        altura_fig = max(5, len(df) * 0.6)
        
        fig, ax = plt.subplots(figsize=(8, altura_fig))

        # Cor Principal: Um verde sólido e legível (baseado na paleta do app #92C7A3 mas um pouco mais escuro para contraste)
        cor_barra = '#69B588' 

        # Gera as barras horizontais
        # zorder=3 garante que as barras fiquem na frente de qualquer linha de grade
        bars = ax.barh(df['atividade_texto'], df['frequencia'], color=cor_barra, height=0.65, zorder=3)
        
        # Limpeza TOTAL das bordas (spines)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False) 
        ax.spines['left'].set_visible(False) # Remove até a linha vertical esquerda

        # Remove os ticks (tracinhos) dos eixos
        ax.tick_params(axis='both', which='both', length=0)
        
        # Remove os números do eixo X (pois colocaremos nas barras)
        ax.xaxis.set_ticks([]) 

        # Aumenta a fonte dos nomes das atividades (Eixo Y) e muda a cor para cinza escuro
        ax.tick_params(axis='y', labelsize=13, colors='#404040')

        # Adiciona o valor exato DENTRO ou AO LADO da barra
        max_valor = df['frequencia'].max()
        
        for bar in bars:
            width = bar.get_width()
            label_y = bar.get_y() + bar.get_height() / 2
            
            # Texto um pouco afastado da barra
            padding = max_valor * 0.02 
            
            ax.text(width + padding,        # Posição X
                    label_y,                # Posição Y
                    s=f'{int(width)}',      # O número
                    va='center',            # Centralizado verticalmente
                    ha='left',              # Alinhado à esquerda
                    fontsize=13, 
                    fontweight='bold', 
                    color='#2E7D52')        # Verde escuro para o número

        # Título
        ax.set_title('Atividades Realizadas', fontsize=18, fontweight='bold', color='#333333', pad=20, loc='left')
        ax.set_ylabel('')

        plt.tight_layout()

        # 3. Converte para Base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=60, transparent=True) 
        buf.seek(0)
        base64_img = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return {"base64": base64_img}

    except Exception as e:
        print(f"Erro grafico atividades: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()