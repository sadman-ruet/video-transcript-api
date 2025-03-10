from pydantic import BaseModel, EmailStr

class User(BaseModel):
        name: str
        username: str
        email: EmailStr  # Automatically validates email format

class UserInfo(BaseModel):
    username: str
    email: EmailStr
    class Config():
        from_attributes = True


class ChatHistory(BaseModel):
    username: str
    message: str
    response: str
    class Config():
        from_attributes = True