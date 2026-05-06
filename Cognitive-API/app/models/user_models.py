from pydantic import BaseModel

class UserRegister(BaseModel):
    username: str
    password: str
    user_type: str
    email: str
    data_nascimento: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    username: str
    email: str
    data_nascimento: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str