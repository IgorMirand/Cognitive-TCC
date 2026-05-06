from fastapi import APIRouter
from ..models.user_models import UserRegister, UserLogin
from ..services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
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


@router.post("/login")
def login(data: UserLogin):
    try:  # Adicione um try/except grande se não tiver
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
        traceback.print_exc()  # Isso mostra a linha exata do erro
        # --------------------------------
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
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

@router.put("/users/{user_id}/password")
def change_password(user_id: int, data: PasswordChange):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Busca a senha atual do usuário no banco
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        current_hash_db = result[0].encode('utf-8')  # Converte para bytes

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

@router.get("/users/{user_id}")
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