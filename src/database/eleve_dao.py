from src.database.connection import get_connection


class EleveDAO:
    @staticmethod
    def create(matricule, nom, prenom, classe, frais, annee_scolaire="2025-2026"):
        return EleveDAO.ajouter(
            nom,
            prenom,
            classe,
            annee_scolaire,
            frais,
            matricule=matricule,
        )

    @staticmethod
    def ajouter(nom, prenom, classe, annee_scolaire, total_du, matricule=None):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO eleve (matricule, nom, prenom, classe, annee_scolaire, total_du)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (matricule, nom, prenom, classe, annee_scolaire, total_du),
            )
            return cursor.lastrowid

    @staticmethod
    def get(eleve_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, matricule, nom, prenom, classe, annee_scolaire, total_du
                FROM eleve
                WHERE id = ?
                """,
                (eleve_id,),
            )
            return cursor.fetchone()

    @staticmethod
    def get_all():
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, matricule, nom, prenom, classe, annee_scolaire, total_du
                FROM eleve
                ORDER BY nom, prenom
                """
            )
            return cursor.fetchall()

    @staticmethod
    def lister_avec_solde(texte="", classe=None):
        query = """
            SELECT e.id, e.matricule, e.nom, e.prenom, e.classe, e.annee_scolaire,
                   e.total_du,
                   COALESCE(SUM(p.montant), 0) AS total_paye,
                   e.total_du - COALESCE(SUM(p.montant), 0) AS solde
            FROM eleve e
            LEFT JOIN paiement p ON p.eleve_id = e.id
        """
        params = []
        conditions = []

        if texte:
            conditions.append("(LOWER(e.nom) LIKE ? OR LOWER(e.prenom) LIKE ? OR LOWER(COALESCE(e.matricule, '')) LIKE ?)")
            mot = f"%{texte.lower()}%"
            params.extend([mot, mot, mot])

        if classe:
            conditions.append("LOWER(e.classe) = ?")
            params.append(classe.lower())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY e.id ORDER BY e.nom, e.prenom"

        with get_connection() as conn:
            cursor = conn.cursor()
            return cursor.execute(query, params).fetchall()

    @staticmethod
    def modifier(eleve_id, nom, prenom, classe, annee_scolaire, total_du, matricule=None):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE eleve
                SET matricule = ?, nom = ?, prenom = ?, classe = ?, annee_scolaire = ?, total_du = ?
                WHERE id = ?
                """,
                (matricule, nom, prenom, classe, annee_scolaire, total_du, eleve_id),
            )

    @staticmethod
    def update(eleve_id, nom, prenom, classe, frais, annee_scolaire="2025-2026", matricule=None):
        EleveDAO.modifier(
            eleve_id,
            nom,
            prenom,
            classe,
            annee_scolaire,
            frais,
            matricule=matricule,
        )

    @staticmethod
    def delete(eleve_id):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM eleve WHERE id = ?", (eleve_id,))

    @staticmethod
    def supprimer(eleve_id):
        EleveDAO.delete(eleve_id)


def create(matricule, nom, prenom, classe, frais, annee_scolaire="2025-2026"):
    return EleveDAO.create(matricule, nom, prenom, classe, frais, annee_scolaire)


def ajouter(nom, prenom, classe, annee_scolaire, total_du, matricule=None):
    return EleveDAO.ajouter(nom, prenom, classe, annee_scolaire, total_du, matricule)


def get(eleve_id):
    return EleveDAO.get(eleve_id)


def get_all():
    return EleveDAO.get_all()


def lister_avec_solde(texte="", classe=None):
    return EleveDAO.lister_avec_solde(texte, classe)


def modifier(eleve_id, nom, prenom, classe, annee_scolaire, total_du, matricule=None):
    return EleveDAO.modifier(eleve_id, nom, prenom, classe, annee_scolaire, total_du, matricule)


def update(eleve_id, nom, prenom, classe, frais, annee_scolaire="2025-2026", matricule=None):
    return EleveDAO.update(eleve_id, nom, prenom, classe, frais, annee_scolaire, matricule)


def delete(eleve_id):
    return EleveDAO.delete(eleve_id)


def supprimer(eleve_id):
    return EleveDAO.supprimer(eleve_id)

