from datetime import date

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.database.connection import init_db
from src.services import calcul_service, pdf_service


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.setWindowTitle("EduPay - Gestion des frais scolaires")
        self.resize(1200, 700)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom, prénom ou matricule")
        self.search_input.textChanged.connect(self.refresh_table)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Matricule",
                "Nom",
                "Prénom",
                "Classe",
                "Année",
                "Total dû",
                "Payé",
                "Solde",
                "Statut",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)

        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.matricule_input = QLineEdit()
        self.classe_input = QLineEdit()
        self.annee_input = QLineEdit("2025-2026")
        self.total_du_input = QLineEdit()

        self.payment_amount_input = QLineEdit()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Espèces", "Chèque", "Virement", "Mobile Money"])
        self.date_input = QLineEdit(date.today().isoformat())

        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        central_widget = QWidget()
        root_layout = QVBoxLayout(central_widget)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Recherche :"))
        search_layout.addWidget(self.search_input)
        root_layout.addLayout(search_layout)

        root_layout.addWidget(self.table)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.addRow("Matricule", self.matricule_input)
        form_layout.addRow("Nom", self.nom_input)
        form_layout.addRow("Prénom", self.prenom_input)
        form_layout.addRow("Classe", self.classe_input)
        form_layout.addRow("Année scolaire", self.annee_input)
        form_layout.addRow("Montant total dû", self.total_du_input)

        add_student_btn = QPushButton("Ajouter l'élève")
        add_student_btn.clicked.connect(self.on_add_student)
        form_layout.addRow(add_student_btn)

        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("Montant payé :"))
        payment_layout.addWidget(self.payment_amount_input)
        payment_layout.addWidget(QLabel("Mode :"))
        payment_layout.addWidget(self.mode_combo)
        payment_layout.addWidget(QLabel("Date :"))
        payment_layout.addWidget(self.date_input)

        payment_btn = QPushButton("Enregistrer le paiement")
        payment_btn.clicked.connect(self.on_add_payment)
        payment_layout.addWidget(payment_btn)

        root_layout.addWidget(form_widget)
        root_layout.addLayout(payment_layout)

        self.setCentralWidget(central_widget)

    def refresh_table(self):
        try:
            rows = calcul_service.lister_eleves(self.search_input.text())
        except Exception as exc:  # pragma: no cover - safety net
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Base de données indisponible", f"Erreur de chargement : {exc}")
            return

        self.table.setRowCount(0)

        for row_index, row in enumerate(rows):
            self.table.insertRow(row_index)
            values = [
                str(row["id"]),
                row.get("matricule") or "-",
                row["nom"],
                row["prenom"],
                row["classe"],
                row["annee_scolaire"],
                f"{float(row['total_du']):,.0f} FCFA",
                f"{float(row['total_paye']):,.0f} FCFA",
                f"{float(row['solde']):,.0f} FCFA",
                row["statut"],
            ]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.table.setItem(row_index, column_index, item)

    def on_add_student(self):
        try:
            calcul_service.ajouter_eleve(
                self.nom_input.text(),
                self.prenom_input.text(),
                self.classe_input.text(),
                self.annee_input.text(),
                self.total_du_input.text(),
                matricule=self.matricule_input.text() or None,
            )
            self.nom_input.clear()
            self.prenom_input.clear()
            self.matricule_input.clear()
            self.classe_input.clear()
            self.annee_input.setText("2025-2026")
            self.total_du_input.clear()
            self.refresh_table()
            QMessageBox.information(self, "Succès", "Élève ajouté avec succès.")
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Erreur", str(exc))

    def on_add_payment(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Sélection requise", "Sélectionnez un élève dans le tableau.")
            return

        eleve_id = int(self.table.item(selected_rows[0].row(), 0).text())
        try:
            paiement = calcul_service.enregistrer_paiement(
                eleve_id,
                self.payment_amount_input.text(),
                self.mode_combo.currentText(),
                self.date_input.text(),
            )
            pdf_service.generer_recu(paiement["id"])
            self.payment_amount_input.clear()
            self.refresh_table()
            QMessageBox.information(
                self,
                "Paiement enregistré",
                f"Paiement ajouté avec succès.\nReçu N° {paiement['numero_recu']}",
            )
        except Exception as exc:  # pragma: no cover - UI feedback only
            QMessageBox.critical(self, "Erreur", str(exc))


if __name__ == "__main__":
    init_db()
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
