from contextlib import closing
from src.database.connection import get_connection


def ajouter(nom, prenom, classe, annee_scolaire, total_du):
    """Insère un élève et retourne son id."""
    with closing(get_connection()) as conn, conn:
        cur = conn.execute(
            """INSERT INTO eleve (nom, prenom, classe, annee_scolaire, total_du)
               VALUES (?, ?, ?, ?, ?)""",
            (nom, prenom, classe, annee_scolaire, total_du),
        )
        return cur.lastrowid


def modifier(eleve_id, nom, prenom, classe, annee_scolaire, total_du):
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """UPDATE eleve
               SET nom = ?, prenom = ?, classe = ?, annee_scolaire = ?, total_du = ?
               WHERE id = ?""",
            (nom, prenom, classe, annee_scolaire, total_du, eleve_id),
        )


def supprimer(eleve_id):
    """Lève sqlite3.IntegrityError si l'élève a des paiements (ON DELETE RESTRICT)."""
    with closing(get_connection()) as conn, conn:
        conn.execute("DELETE FROM eleve WHERE id = ?", (eleve_id,))


def get(eleve_id):
    with closing(get_connection()) as conn:
        return conn.execute(
            "SELECT * FROM eleve WHERE id = ?", (eleve_id,)
        ).fetchone()


def lister_classes():
    with closing(get_connection()) as conn:
        rows = conn.execute(
            "SELECT DISTINCT classe FROM eleve ORDER BY classe"
        ).fetchall()
        return [r["classe"] for r in rows]


def lister_avec_solde(texte="", classe=None):
    """Liste les élèves avec total payé et solde, filtrable par texte et par classe."""
    sql = """
        SELECT e.*,
               COALESCE(SUM(p.montant), 0) AS total_paye,
               e.total_du - COALESCE(SUM(p.montant), 0) AS solde
        FROM eleve e
        LEFT JOIN paiement p ON p.eleve_id = e.id
        WHERE (e.nom LIKE ? OR e.prenom LIKE ?)
    """
    motif = f"%{texte}%"
    params = [motif, motif]
    if classe:
        sql += " AND e.classe = ?"
        params.append(classe)
    sql += " GROUP BY e.id ORDER BY e.nom, e.prenom"
    with closing(get_connection()) as conn:
        return conn.execute(sql, params).fetchall()