from sqlmodel import SQLModel, Field, create_engine
from typing import Optional
from datetime import datetime

DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str

class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: Optional[str] = Field()
    raw_log: Optional[str] = Field()
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
