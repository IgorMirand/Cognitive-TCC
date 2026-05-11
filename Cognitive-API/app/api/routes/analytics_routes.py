import io
import re
import base64
import traceback

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db_connection
from app.core.security import get_current_user, require_psicologo

router = APIRouter(tags=["Analytics"])

EMOCOES_MAP = {
    1: "Feliz", 2: "Triste", 3: "Medo", 4: "Surpreso",
    5: "Raiva", 6: "Envergonhado", 7: "Constrangido", 8: "Receoso",
    9: "Apático", 10: "Deprimido", 11: "Irritado",
}

SCORES_PADRAO = {
    1: 9.0, 2: 3.0, 3: 3.0, 4: 6.0, 5: 2.0,
    6: 4.0, 7: 4.0, 8: 4.0, 9: 3.0, 10: 1.0, 11: 2.0,
}


def _fig_to_base64() -> str:
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode("utf-8")
    plt.close()
    return img


def _extrair_bem_estar(texto) -> int | None:
    if not isinstance(texto, str):
        return None
    match = re.search(r"Bem-estar:\s*(\d+)", texto, re.IGNORECASE)
    return int(match.group(1)) if match else None


@router.get("/relatorios/analise/{paciente_id}")
def gerar_relatorio_paciente(paciente_id: int, current_user: dict = Depends(require_psicologo)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data_hora_iso, sentimento_id, anotacao FROM entradas_diario "
            "WHERE paciente_id = %s ORDER BY data_hora_iso ASC",
            (paciente_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(status_code=404, detail="Paciente sem registros.")

        df = pd.DataFrame(rows, columns=["data_hora_iso", "sentimento_id", "anotacao"])
        df["data"] = pd.to_datetime(df["data_hora_iso"], errors="coerce")
        df = df.dropna(subset=["data"])

        def calcular_score(row):
            score_base = SCORES_PADRAO.get(row["sentimento_id"], 5.0)
            bem_estar = _extrair_bem_estar(row["anotacao"])
            return (score_base + bem_estar * 2) / 3 if bem_estar is not None else score_base

        df["score_final"] = df.apply(calcular_score, axis=1)
        df["humor_label"] = df["sentimento_id"].map(lambda x: EMOCOES_MAP.get(x, f"Outro ({x})"))

        media_geral = df["score_final"].mean()
        cor_linha = "#92C7A3" if media_geral >= 5 else "#FF6B6B"

        # Gráfico 1 — Evolução
        plt.figure(figsize=(10, 5))
        df_diario = df.groupby("data")["score_final"].mean()
        plt.plot(df_diario.index, df_diario.values, marker="o", linestyle="-", color=cor_linha, linewidth=3)
        plt.title("Evolução do Bem-Estar (0 a 10)", color="#4a4939")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.ylim(0, 11)
        plt.ylabel("Nível de Bem-Estar")
        plt.gcf().autofmt_xdate()
        grafico1 = _fig_to_base64()

        # Gráfico 2 — Distribuição
        plt.figure(figsize=(10, 5))
        df["humor_label"].value_counts().plot(kind="bar", color="#76a885")
        plt.title("Frequência de Emoções", color="#4a4939")
        plt.xticks(rotation=0)
        grafico2 = _fig_to_base64()

        if media_geral >= 7.5:
            status = "Positivo"
        elif media_geral >= 5.0:
            status = "Estável"
        elif media_geral >= 3.0:
            status = "Atenção"
        else:
            status = "Crítico"

        resumo = f"Baseado em {len(df)} registros. Pontuação Geral: {media_geral:.1f}/10 ({status})."
        if df.iloc[-1]["score_final"] < 4:
            resumo += " Atenção: O registro mais recente indica baixo bem-estar."

        return {
            "grafico_evolucao_base64": grafico1,
            "grafico_distribuicao_base64": grafico2,
            "resumo_texto": resumo,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/relatorios/grafico_atividades/{paciente_id}")
def get_atividades_chart(paciente_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        query = """
            SELECT T.atividade_texto, COUNT(R.id) as frequencia
            FROM registros_atividades_diario R
            JOIN atividades_template T ON R.atividade_template_id = T.id
            JOIN entradas_diario E ON R.entrada_diario_id = E.id
            WHERE E.paciente_id = %s
            GROUP BY T.atividade_texto
            ORDER BY frequencia ASC
        """
        df = pd.read_sql(query, conn, params=(paciente_id,))

        if df.empty:
            return {"base64": None}

        plt.style.use("seaborn-v0_8-white")
        altura_fig = max(5, len(df) * 0.6)
        fig, ax = plt.subplots(figsize=(8, altura_fig))

        bars = ax.barh(df["atividade_texto"], df["frequencia"], color="#69B588", height=0.65, zorder=3)

        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis="both", which="both", length=0)
        ax.xaxis.set_ticks([])
        ax.tick_params(axis="y", labelsize=13, colors="#404040")

        max_valor = df["frequencia"].max()
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + max_valor * 0.02,
                bar.get_y() + bar.get_height() / 2,
                s=f"{int(width)}",
                va="center", ha="left",
                fontsize=13, fontweight="bold", color="#2E7D52",
            )

        ax.set_title("Atividades Realizadas", fontsize=18, fontweight="bold", color="#333333", pad=20, loc="left")
        ax.set_ylabel("")
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=60, transparent=True)
        buf.seek(0)
        base64_img = base64.b64encode(buf.read()).decode("utf-8")
        plt.close()

        return {"base64": base64_img}
    except Exception as e:
        print(f"Erro grafico atividades: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
