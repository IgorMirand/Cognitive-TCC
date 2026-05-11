import random
import string
from fastapi import APIRouter, HTTPException

from app.core.database import get_db_connection
from app.models.psicologo_models import VinculoData, ConviteEmail, AtividadeTemplate, ConsultaNota

router = APIRouter(tags=["Psicólogo"])


# --- Vínculo e Códigos ---

@router.post("/codigos/gerar/{psicologo_id}")
def gerar_codigo(psicologo_id: int):
    alfanumerico = string.ascii_uppercase + string.digits
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for _ in range(5):
            p1 = "".join(random.choices(alfanumerico, k=3))
            p2 = "".join(random.choices(alfanumerico, k=3))
            codigo = f"{p1}-{p2}"
            try:
                cursor.execute(
                    "INSERT INTO codigos_paciente (codigo, gerado_por_psicologo_id) VALUES (%s, %s)",
                    (codigo, psicologo_id),
                )
                conn.commit()
                return {"codigo": codigo}
            except Exception:
                conn.rollback()
                continue
        raise HTTPException(status_code=500, detail="Falha ao gerar código único.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/vincular")
def vincular_paciente(data: VinculoData):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM paciente_psicologo_link WHERE paciente_user_id = %s", (data.paciente_id,)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Paciente já vinculado.")

        cursor.execute(
            "SELECT gerado_por_psicologo_id FROM codigos_paciente "
            "WHERE codigo=%s AND usado_por_paciente_id IS NULL",
            (data.codigo,),
        )
        res = cursor.fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Código inválido.")

        psicologo_id = res[0]
        cursor.execute(
            "INSERT INTO paciente_psicologo_link (paciente_user_id, psicologo_user_id) VALUES (%s, %s)",
            (data.paciente_id, psicologo_id),
        )
        cursor.execute(
            "UPDATE codigos_paciente SET usado_por_paciente_id = %s WHERE codigo = %s",
            (data.paciente_id, data.codigo),
        )
        conn.commit()
        return {"success": True, "message": "Vinculado com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/codigos/master/validar/{codigo}")
def validar_codigo_master(codigo: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM codigos_master WHERE codigo = %s AND usado_por_user_id IS NULL", (codigo,)
        )
        resultado = cursor.fetchone()
        conn.close()
        return {"valid": bool(resultado), "id": resultado[0] if resultado else None}
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/codigos/master/usar")
def usar_codigo_master(data: dict):
    codigo_id = data.get("codigo_id")
    user_id = data.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE codigos_master SET usado_por_user_id = %s WHERE id = %s", (user_id, codigo_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# --- Dashboard ---

@router.get("/psicologo/{psicologo_id}/stats")
def get_stats(psicologo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM paciente_psicologo_link WHERE psicologo_user_id = %s", (psicologo_id,)
        )
        count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT A.data_hora, U.username
            FROM agenda A
            JOIN users U ON A.paciente_id = U.id
            WHERE A.psicologo_id = %s
              AND A.paciente_id IS NOT NULL
              AND CAST(A.data_hora AS TIMESTAMP) > NOW()
            ORDER BY A.data_hora ASC
            LIMIT 1
            """,
            (psicologo_id,),
        )
        row = cursor.fetchone()

        proxima = None
        if row:
            data_str = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
            proxima = [data_str, row[1]]

        return {"pacientes_count": count, "proxima_consulta": proxima}
    except Exception as e:
        print(f"Erro no Stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/psicologo/{psicologo_id}/pacientes")
def get_pacientes(psicologo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT U.id, U.username
        FROM paciente_psicologo_link L
        JOIN users U ON L.paciente_user_id = U.id
        WHERE L.psicologo_user_id = %s
        """,
        (psicologo_id,),
    )
    pacientes = cursor.fetchall()
    conn.close()
    return {"pacientes": pacientes}


@router.get("/paciente/{paciente_id}/psicologo")
def get_psicologo_do_paciente(paciente_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT psicologo_user_id FROM paciente_psicologo_link WHERE paciente_user_id = %s",
            (paciente_id,),
        )
        result = cursor.fetchone()
        conn.close()
        return {"psicologo_id": result[0] if result else None}
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# --- Atividades ---

@router.get("/atividades")
def listar_atividades():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, atividade_texto FROM atividades_template")
    atividades = cursor.fetchall()
    conn.close()
    return {"atividades": atividades}


@router.post("/atividades")
def criar_atividade(data: AtividadeTemplate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM atividades_template WHERE atividade_texto = %s", (data.texto,)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Atividade já existe")
        cursor.execute(
            "INSERT INTO atividades_template (atividade_texto, criado_por_psicologo_id) VALUES (%s, %s)",
            (data.texto, data.psicologo_id),
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.delete("/atividades/{atividade_id}")
def deletar_atividade(atividade_id: int):
    import psycopg2
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM atividades_template WHERE id = %s", (atividade_id,))
        conn.commit()
        return {"success": True}
    except psycopg2.errors.IntegrityError:
        raise HTTPException(status_code=400, detail="Não pode excluir: atividade em uso.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.put("/atividades/{atividade_id}")
def atualizar_atividade(atividade_id: int, novo_texto: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE atividades_template SET atividade_texto = %s WHERE id = %s",
            (novo_texto, atividade_id),
        )
        conn.commit()
        return {"success": True}
    finally:
        conn.close()


# --- Consultas ---

@router.get("/consultas/{psicologo_id}/{paciente_id}")
def get_anotacoes_paciente(psicologo_id: int, paciente_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, data_hora_iso, anotacao
            FROM consultas_psicologo
            WHERE psicologo_id = %s AND paciente_id = %s
            ORDER BY data_hora_iso DESC
            """,
            (psicologo_id, paciente_id),
        )
        notas = cursor.fetchall()
        conn.close()
        return {"anotacoes": notas}
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consultas")
def salvar_consulta(data: ConsultaNota):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO consultas_psicologo (psicologo_id, paciente_id, anotacao, data_hora_iso) "
            "VALUES (%s, %s, %s, %s)",
            (data.psicologo_id, data.paciente_id, data.anotacao, data.data_hora_iso),
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# --- Email / Convite ---

@router.post("/email/enviar_convite")
def enviar_convite_email(data: ConviteEmail):
    import random
    import string

    alfanumerico = string.ascii_uppercase + string.digits
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        codigo = ""
        for _ in range(5):
            p1 = "".join(random.choices(alfanumerico, k=3))
            p2 = "".join(random.choices(alfanumerico, k=3))
            temp = f"{p1}-{p2}"
            cursor.execute("SELECT id FROM codigos_paciente WHERE codigo = %s", (temp,))
            if not cursor.fetchone():
                codigo = temp
                break

        if not codigo:
            raise HTTPException(status_code=500, detail="Erro ao gerar código.")

        cursor.execute(
            "INSERT INTO codigos_paciente (codigo, gerado_por_psicologo_id) VALUES (%s, %s)",
            (codigo, data.psicologo_id),
        )

        cursor.execute("SELECT id, username FROM users WHERE email = %s", (data.email_paciente,))
        paciente_existente = cursor.fetchone()

        notificacao_enviada = False
        if paciente_existente:
            paciente_id = paciente_existente[0]
            cursor.execute(
                "INSERT INTO notificacoes (user_id, titulo, mensagem) VALUES (%s, %s, %s)",
                (
                    paciente_id,
                    "Convite de Vínculo",
                    f"Seu código de vínculo é: {codigo}. Insira este código na tela inicial.",
                ),
            )
            notificacao_enviada = True

        conn.commit()

        msg = f"Convite enviado para {data.email_paciente}"
        if notificacao_enviada:
            msg += " (Notificação enviada para o App)"
        return {"success": True, "message": msg}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# --- Config ---

@router.get("/config/powerbi")
def get_powerbi_link():
    link_real = (
        "https://app.powerbi.com/view?r=eyJrIjoiMGUzYTIxMzktYTExZi00OGY2LThkM2ItMGVlYjk4ZTU5NzAzIiwidCI6ImRlZjQ0ZjhmLWFlM2EtNDA4MS1iY2EzLWYwODBhZDkzYTUxYyJ9"
    )
    return {"url": link_real}
