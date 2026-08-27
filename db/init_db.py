import sqlite3
from pathlib import Path


DB_DIR = Path(__file__).resolve().parent

DB_PATH = DB_DIR / "contact_discovery.db"

SCHEMA_PATH = DB_DIR / "schema.sql"


def _ensure_schema_compatibility(conn):
    """Apply additive migrations that CREATE TABLE IF NOT EXISTS cannot make."""
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(companies)").fetchall()
    }
    required = {
        "industry": "TEXT",
        "employee_count": "INTEGER",
        "revenue": "TEXT",
    }
    for column, column_type in required.items():
        if column not in existing:
            conn.execute(
                f"ALTER TABLE companies ADD COLUMN {column} {column_type}"
            )

    # Older databases created before the current schema lack this uniqueness
    # constraint, which the repository's company upsert relies on.
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_companies_normalized_name "
        "ON companies(normalized_name)"
    )

    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_people_normalized_company "
        "ON people(normalized_name, company_id)"
    )

    # Ensure existing databases can support contact upserts safely.
    conn.execute(
        """
        DELETE FROM contact_points
        WHERE contact_id IN (
            SELECT cp.contact_id
            FROM contact_points cp
            JOIN (
                SELECT
                    person_id,
                    contact_type,
                    contact_value,
                    MIN(contact_id) AS keep_contact_id
                FROM contact_points
                GROUP BY person_id, contact_type, contact_value
                HAVING COUNT(*) > 1
            ) duplicates
                ON cp.person_id = duplicates.person_id
               AND cp.contact_type = duplicates.contact_type
               AND cp.contact_value = duplicates.contact_value
            WHERE cp.contact_id <> duplicates.keep_contact_id
        )
        """
    )

    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_points_identity "
        "ON contact_points(person_id, contact_type, contact_value)"
    )


def init_database():
    """
    Initialize (or re-initialize) the SQLite database
    using the project schema.

    Existing tables are preserved (CREATE IF NOT EXISTS).
    New tables and indexes are added.
    """
    conn = sqlite3.connect(DB_PATH)

    try:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema)
        _ensure_schema_compatibility(conn)
        conn.commit()

        print(f"[DB] Database initialized: {DB_PATH}")

    except sqlite3.Error as e:
        print(f"[DB] Database initialization failed: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
