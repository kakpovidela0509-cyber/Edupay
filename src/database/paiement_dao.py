from contextlib import closing
from datetime import date
from src.database.connection import get_connection


def ajouter(eleve_id, montant, mode_paiement, date_paiement, numero_recu, solde_apres):
    """Insère un paiement et retourne son id."""
    with closing(get_connection()) as conn, conn:
        cur = conn.execute(
            """INSERT INTO paiement
               (eleve_id, montant, mode_paiement, date_paiement, numero_recu, solde_apres)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (eleve_id, montant, mode_paiement, date_paiement, numero_recu, solde_apres),
        )
        return cur.lastrowid


def get(paiement_id):
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT * FROM paiement WHERE id = ?", (paiement_id,)
        ).fetchone()


def lister_par_eleve(eleve_id):
    """Historique chronologique des paiements d'un élève."""
    with closing(get_connection()) as conn:
        return conn.execute(
            """SELECT * FROM paiement
               WHERE eleve_id = ?
               ORDER BY date_paiement, id""",
            (eleve_id,),
        ).fetchall()


def somme_par_eleve(eleve_id):
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(montant), 0) AS total FROM paiement WHERE eleve_id = ?",
            (eleve_id,),
        ).fetchone()
        return row["total"]


def total_encaisse():
    """Pour le tableau de bord."""
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(montant), 0) AS total FROM paiement"
        ).fetchone()
        return row["total"]


def prochain_numero_recu():
    """Format : REC-2026-00001."""
    annee = date.today().year
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM paiement WHERE numero_recu LIKE ?",
            (f"REC-{annee}-%",),
        ).fetchone()
        return f"REC-{annee}-{row['n'] + 1:05d}"