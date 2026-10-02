import os
import shutil
import sqlite3
import tempfile
import unittest

from src.database import connection, eleve_dao, paiement_dao
from src.services import calcul_service, pdf_service


class EduPayCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="edupay_test_")
        self.db_path = os.path.join(self.temp_dir, "edupay.db")
        connection.DB_PATH = self.db_path
        connection.SCHEMA_PATH = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "schema.sql"
        )
        connection.init_db()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_student_and_payment_flow(self):
        eleve_id = eleve_dao.create(
            "MAT-001",
            "Moussa",
            "Diop",
            "Terminale A",
            300000,
        )
        self.assertIsNotNone(eleve_id)

        paiement_id = paiement_dao.ajouter(
            eleve_id,
            150000,
            "Espèces",
            "2026-10-01",
            "REC-2026-00001",
            150000,
        )
        self.assertIsNotNone(paiement_id)

        rows = calcul_service.lister_eleves()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["total_du"], 300000)
        self.assertEqual(rows[0]["total_paye"], 150000)
        self.assertEqual(rows[0]["solde"], 150000)
        self.assertEqual(calcul_service.solde(eleve_id), 150000)
        history = calcul_service.historique(eleve_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["numero_recu"], "REC-2026-00001")

        receipts_dir = os.path.join(self.temp_dir, "recus")
        receipt_path = pdf_service.generer_recu(paiement_id, dossier=receipts_dir)
        self.assertTrue(os.path.isfile(receipt_path))

    def test_connection_auto_creates_missing_schema(self):
        sqlite3.connect(self.db_path).close()
        conn = connection.get_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('eleve', 'paiement')"
        ).fetchall()
        self.assertGreaterEqual(len(tables), 2)
        conn.close()


if __name__ == "__main__":
    unittest.main()
