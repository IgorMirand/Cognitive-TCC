from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import execute_values

from app.core.database import get_db_connection
from app.core.security import get_current_user, require_paciente
from app.models.diario_models import DiarioEntry

router = APIRouter(tags=["Diário"])


@router.post("/diario")
def salvar_diario(data: DiarioEntry, current_user: dict = Depends(require_paciente)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO entradas_diario (paciente_id, data_hora_iso, sentimento_id, anotacao) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (data.paciente_id, data.data_hora_iso, data.sentimento_id, data.anotacao),
        )
        diario_id = cursor.fetchone()[0]

        if data.atividades_ids:
            vals = [(diario_id, aid) for aid in data.atividades_ids]
            execute_values(
                cursor,
                "INSERT INTO registros_atividades_diario (entrada_diario_id, atividade_template_id) VALUES %s",
                vals,
            )

        conn.commit()
        return {"success": True, "id": diario_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/diario/historico/{paciente_id}")
def get_historico(paciente_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
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
