import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "edupay.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "data", "schema.sql")


def get_connection():
    """Établit la connexion avec la BDD SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialise les tables à partir de data/schema.sql."""
    if not os.path.exists(SCHEMA_PATH):
        print(f"Erreur : fichier introuvable : {SCHEMA_PATH}")
        return
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print("Base de données EduPay initialisée avec succès !")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()