from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    password: str

    uploads: List["Upload"] = Relationship(back_populates="user")


class Upload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    raw_log: str
    filesize: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="uploads")

    @property
    def size_readable(self):
        if not self.filesize:
            return "N/A"
        size = self.filesize
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

from sqlmodel import create_engine
engine = create_engine("sqlite:///users.db")
