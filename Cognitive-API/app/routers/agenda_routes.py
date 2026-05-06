from fastapi import APIRouter
from ..core.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/agenda/psicologo/{id}")
def get_agenda(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, data_hora, paciente_id FROM agenda WHERE psicologo_id = %s AND data_hora >= NOW() ORDER BY data_hora ASC",
        (id,))
    agenda = cursor.fetchall()
    conn.close()
    return {"agenda": agenda}


@router.post("/agenda/disponibilidade")
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
            data_fmt = data.data_hora_iso  # Se der erro, usa a original

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

@router.delete("/agenda/{agenda_id}")
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


@router.put("/agenda/{agenda_id}/reservar")
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
