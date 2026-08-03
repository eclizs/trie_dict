from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr = Field(max_length=100)

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)

class Token(BaseModel):
    access_token: str
    token_type: str

