import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "edupaie.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "data", "schema.sql")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn = get_connection()
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        print("Base de données EduPaie initialisée avec succès !")
    else:
        print(f"Erreur : Fichier introuvable à {SCHEMA_PATH}")

if __name__ == "__main__":
    init_db()
