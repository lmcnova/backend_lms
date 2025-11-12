from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email_id: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    user_data: dict

class TokenData(BaseModel):
    email_id: str
    role: str
