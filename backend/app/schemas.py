from pydantic import BaseModel
from datetime import datetime
from pydantic import Field

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., max_length=72, description="密码不能超过72字符")

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class RoomCreate(BaseModel):
    name: str

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_type: str
    sender_name: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
        

class RoomOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True