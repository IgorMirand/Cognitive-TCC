from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db_connection
from app.core.security import get_current_user, require_psicologo, require_paciente
from app.models.agenda_models import AgendaSlot, ReservaData

router = APIRouter(tags=["Agenda"])


@router.get("/agenda/psicologo/{psicologo_id}")
def get_agenda(psicologo_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, data_hora, paciente_id FROM agenda "
        "WHERE psicologo_id = %s AND data_hora >= NOW() ORDER BY data_hora ASC",
        (psicologo_id,),
    )
    agenda = cursor.fetchall()
    conn.close()
    return {"agenda": agenda}


@router.post("/agenda/disponibilidade")
def add_agenda(data: AgendaSlot, current_user: dict = Depends(require_psicologo)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO agenda (psicologo_id, data_hora, paciente_id) VALUES (%s, %s, NULL)",
            (data.psicologo_id, data.data_hora_iso),
        )

        cursor.execute("SELECT username FROM users WHERE id = %s", (data.psicologo_id,))
        psi_result = cursor.fetchone()
        nome_psi = psi_result[0] if psi_result else "Seu Psicólogo"

        try:
            data_limpa = data.data_hora_iso.replace("Z", "")
            dt_obj = (
                datetime.fromisoformat(data_limpa)
                if "T" in data_limpa
                else datetime.strptime(data_limpa, "%Y-%m-%d %H:%M:%S")
            )
            data_fmt = dt_obj.strftime("%d/%m às %H:%M")
        except Exception:
            data_fmt = data.data_hora_iso

        cursor.execute(
            "SELECT paciente_user_id FROM paciente_psicologo_link WHERE psicologo_user_id = %s",
            (data.psicologo_id,),
        )
        pacientes = cursor.fetchall()

        if pacientes:
            titulo = "Novo Horário Disponível 📅"
            mensagem = (
                f"O Dr(a). {nome_psi} acabou de abrir um horário para {data_fmt}. "
                "Acesse a agenda para marcar!"
            )
            for (paciente_id,) in pacientes:
                cursor.execute(
                    "INSERT INTO notificacoes (user_id, titulo, mensagem) VALUES (%s, %s, %s)",
                    (paciente_id, titulo, mensagem),
                )

        conn.commit()
        return {"success": True, "message": "Horário criado e pacientes notificados!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/agenda/{agenda_id}")
def delete_agenda_slot(agenda_id: int, current_user: dict = Depends(require_psicologo)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM agenda WHERE id = %s", (agenda_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Horário não encontrado.")

        cursor.execute("DELETE FROM agenda WHERE id = %s", (agenda_id,))
        conn.commit()
        return {"success": True, "message": "Horário removido."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put("/agenda/{agenda_id}/reservar")
def reservar_horario(agenda_id: int, data: ReservaData, current_user: dict = Depends(require_paciente)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT paciente_id FROM agenda WHERE id = %s", (agenda_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Horário não encontrado")
        if row[0] is not None:
            raise HTTPException(status_code=400, detail="Este horário já foi reservado por outra pessoa.")

        cursor.execute(
            "UPDATE agenda SET paciente_id = %s WHERE id = %s", (data.paciente_id, agenda_id)
        )
        conn.commit()
        return {"success": True, "message": "Agendado com sucesso!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
