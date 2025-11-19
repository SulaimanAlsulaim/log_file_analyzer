from sqlmodel import SQLModel, Field, Relationship, create_engine
from datetime import datetime
from typing import Optional, List
import pandas as pd
import json


# ================================
# User Model
# ================================
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    password: str

    uploads: List["Upload"] = Relationship(back_populates="user")


# ================================
# Upload Model
# ================================
class Upload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    filename: str
    raw_log: str  # Raw uploaded file content
    structured_log: Optional[str] = None  # JSON string (for parsed logs)

    filesize: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="uploads")

    # -------------------------------
    # Human-readable file size
    # -------------------------------
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

    # -------------------------------
    # Save structured log (DataFrame → JSON)
    # -------------------------------
    def set_structured(self, df: pd.DataFrame):
        """
        Stores DataFrame as JSON list of records.
        Example:
        [
            {"LineId": 0, "Content": "...", ...},
            {"LineId": 1, "Content": "...", ...}
        ]
        """
        self.structured_log = df.to_json(orient="records")

    # -------------------------------
    # Load structured log (JSON → DataFrame)
    # -------------------------------
    def get_structured(self) -> Optional[pd.DataFrame]:
        """
        Reads structured_log JSON and returns a valid DataFrame.
        """
        if not self.structured_log:
            return None

        # Convert JSON string → Python list → DataFrame
        data_list = json.loads(self.structured_log)
        return pd.DataFrame(data_list)


# ================================
# Database Engine
# ================================
engine = create_engine("sqlite:///users.db")
