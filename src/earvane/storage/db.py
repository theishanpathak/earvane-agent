import psycopg

from earvane.config import settings

def get_connection() -> psycopg.Connection:
    """Open a new Postgres connection using the configured DATABASE_URL."""
    return psycopg.connect(settings.DATABASE_URL)

def run_schema() -> None:
    """Apply schema.sql against the database. Safe to run repeatedly —
    every statement uses CREATE ... IF NOT EXISTS."""
    
    schema_path = __file__.replace("db.py", "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()

    
if __name__ == "__main__":
    run_schema()
    print("Schema applied successfully.")