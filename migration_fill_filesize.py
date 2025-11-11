from sqlmodel import Session, select, create_engine
from models import Log
import os

DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)

# Only run if database exists
if not os.path.exists("users.db"):
    print("Database not found.")
    exit()

with Session(engine) as db:
    logs = db.exec(select(Log)).all()
    for log in logs:
        if log.raw_log and not log.filesize:
            log.filesize = len(log.raw_log.encode('utf-8'))
            print(f"Updated log {log.id} ({log.filename}) with filesize {log.filesize} bytes")
    db.commit()

print("✅ Filesize values filled successfully.")