import sqlite3
from pathlib import Path

DB_PATH = Path("contact_discovery.db")

SCHEMA_PATH = Path("schema.sql")

def init_database():
    conn = sqlite3.connect(DB_PATH)

    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        conn.commit()

        print(f"Database initialized successfully: {DB_PATH}")

    except sqlite3.Error as e:
        print(f"Database initialization failed: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()