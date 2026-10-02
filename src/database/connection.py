import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUNDLE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
SCHEMA_PATH = os.path.join(BUNDLE_DIR, "data", "schema.sql")

if getattr(sys, "frozen", False):
    executable_dir = os.path.dirname(sys.executable)
    project_data_dir = os.path.abspath(os.path.join(executable_dir, "..", "data"))
    if os.path.isfile(os.path.join(project_data_dir, "edupay.db")):
        DATA_DIR = project_data_dir
    else:
        DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "EduPay")
else:
    DATA_DIR = os.path.join(BASE_DIR, "data")

DB_PATH = os.path.join(DATA_DIR, "edupay.db")


def _table_exists(conn, table_name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def init_db():
    """Initialise les tables et applique les migrations SQLite nécessaires."""
    if not os.path.exists(SCHEMA_PATH):
        print(f"Erreur : fichier introuvable : {SCHEMA_PATH}")
        return

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(schema_sql)

        if _table_exists(conn, "eleve"):
            columns = [row["name"] for row in conn.execute("PRAGMA table_info('eleve')").fetchall()]
            if "matricule" not in columns:
                conn.execute("ALTER TABLE eleve ADD COLUMN matricule TEXT")
            if "annee_scolaire" not in columns:
                conn.execute("ALTER TABLE eleve ADD COLUMN annee_scolaire TEXT NOT NULL DEFAULT '2025-2026'")
            if "total_du" not in columns:
                conn.execute("ALTER TABLE eleve ADD COLUMN total_du REAL NOT NULL DEFAULT 0")

            conn.execute(
                "UPDATE eleve SET annee_scolaire = '2025-2026' WHERE annee_scolaire IS NULL OR annee_scolaire = ''"
            )
            conn.execute("UPDATE eleve SET total_du = 0 WHERE total_du IS NULL")

        conn.commit()
        print("Base de données EduPay initialisée avec succès !")
    finally:
        conn.close()


def get_connection():
    """Établit la connexion avec la BDD SQLite et initialise le schéma si nécessaire."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row

    if not _table_exists(conn, "eleve") or not _table_exists(conn, "paiement"):
        conn.close()
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

    return conn


if __name__ == "__main__":
    init_db()