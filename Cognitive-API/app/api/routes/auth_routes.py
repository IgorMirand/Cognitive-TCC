import traceback
import psycopg2
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db_connection
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user_models import UserRegister, UserLogin, UserUpdate, PasswordChange

router = APIRouter(tags=["Auth"])


@router.post("/register")
def register_user(data: UserRegister):
    if any(char.isdigit() for char in data.username):
        raise HTTPException(status_code=400, detail="O nome não pode conter números.")
    try:
        data_obj = datetime.strptime(data.data_nascimento, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")

        conn = get_db_connection()
        cursor = conn.cursor()

        password_hash = hash_password(data.password)

        cursor.execute(
            "INSERT INTO users (username, password_hash, user_type, email, data_nacimento) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (data.username, password_hash, data.user_type, data.email, data_iso),
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, user_type, id, username FROM users WHERE email=%s",
            (data.email,),
        )
        user = cursor.fetchone()
        conn.close()

        if user and verify_password(data.password, user[0]):
            token = create_access_token(user_id=user[2], user_type=user[1])
            return {
                "success": True,
                "user_type": user[1],
                "id": user[2],
                "username": user[3],
                "access_token": token,
                "token_type": "bearer",
            }

        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERRO NO LOGIN: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}")
def get_user_details(user_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, username, email, user_type, data_nacimento FROM users WHERE id = %s",
            (user_id,),
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "user_type": user[3],
                "data_nascimento": str(user[4]) if user[4] else "",
            }
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    except Exception as e:
        if conn:
            conn.close()
        print(f"Erro no GET User: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        try:
            dt_obj = datetime.strptime(data.data_nascimento, "%d/%m/%Y")
            data_iso = dt_obj.strftime("%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Data inválida.")

        cursor.execute(
            "UPDATE users SET username = %s, email = %s, data_nacimento = %s WHERE id = %s",
            (data.username, data.email, data_iso, user_id),
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
def change_password(user_id: int, data: PasswordChange, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        if not verify_password(data.old_password, result[0]):
            raise HTTPException(status_code=400, detail="A senha atual está incorreta.")

        new_hash = hash_password(data.new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        conn.commit()
        return {"success": True, "message": "Senha alterada com sucesso!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
