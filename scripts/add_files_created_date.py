from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS created_date TIMESTAMP NULL"))
    conn.execute(text("UPDATE files SET created_date = NOW() AT TIME ZONE 'UTC' WHERE created_date IS NULL"))
    conn.commit()
    print("files.created_date ok")
