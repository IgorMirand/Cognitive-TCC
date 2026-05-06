from ..core.security import hash_password, verify_password

def register_user(data):

    password_hash = hash_password(data.password)

    return create_user(
        data.username,
        password_hash,
        data.user_type,
        data.email,
        data.data_nascimento
    )


def login_user(data):

    user = get_user_by_email(data.email)

    if not user:
        return {"error": "Usuário não encontrado"}

    if not verify_password(data.password, user["password_hash"]):
        return {"error": "Senha incorreta"}

    return {
        "success": True,
        "user_id": user["id"]
    }