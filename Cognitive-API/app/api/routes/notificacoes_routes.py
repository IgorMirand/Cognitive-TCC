from datetime import datetime
from fastapi import APIRouter, HTTPException
import pytz

from app.core.database import get_db_connection

router = APIRouter(tags=["Notificações"])


@router.get("/notificacoes/{user_id}")
def get_notificacoes(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, titulo, mensagem, lida
            FROM notificacoes
            WHERE user_id = %s
            ORDER BY data_criacao DESC
            """,
            (user_id,),
        )
        res = cursor.fetchall()
        lista = [{"id": r[0], "titulo": r[1], "mensagem": r[2], "lida": r[3]} for r in res]
        return {"notificacoes": lista}
    finally:
        conn.close()


@router.delete("/notificacoes/{notificacao_id}")
def deletar_notificacao(notificacao_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM notificacoes WHERE id = %s", (notificacao_id,))
        conn.commit()
        return {"success": True}
    finally:
        conn.close()


@router.put("/notificacoes/marcar_lida/{user_id}")
def marcar_todas_lidas(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE notificacoes SET lida = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/cron/enviar_lembretes_diarios")
def enviar_lembretes_diarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username FROM users WHERE user_type = 'Paciente'")
        pacientes = cursor.fetchall()

        count = 0
        for pid, nome in pacientes:
            cursor.execute(
                "INSERT INTO notificacoes (user_id, titulo, mensagem) VALUES (%s, %s, %s)",
                (
                    pid,
                    "Bom dia! ☀️",
                    f"Olá {nome}, como você está se sentindo hoje? Não esqueça de registrar no seu diário.",
                ),
            )
            count += 1

        conn.commit()
        return {"success": True, "message": f"Lembretes enviados para {count} pacientes."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
