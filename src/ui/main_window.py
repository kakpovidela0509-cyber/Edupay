from datetime import date

from PySide6.QtCore import QDate, QUrl, Qt
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.database.connection import init_db
from src.services import calcul_service, pdf_service


def _montant(valeur):
    return f"{float(valeur):,.0f} FCFA"


def _ouvrir_pdf(parent, chemin):
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(chemin)):
        QMessageBox.warning(parent, "Ouverture impossible", f"Le reçu est enregistré ici :\n{chemin}")


class StudentFormDialog(QDialog):
    def __init__(self, student=None, parent=None):
        super().__init__(parent)
        self.student_id = student["id"] if student else None
        self.setWindowTitle("Modifier l'élève" if student else "Ajouter un élève")
        self.setMinimumWidth(460)

        self.matricule_input = QLineEdit()
        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.classe_input = QLineEdit()
        self.annee_input = QLineEdit("2025-2026")
        self.total_du_input = QDoubleSpinBox()
        self.total_du_input.setRange(0, 1_000_000_000_000)
        self.total_du_input.setDecimals(0)
        self.total_du_input.setGroupSeparatorShown(True)
        self.total_du_input.setSuffix(" FCFA")

        if student:
            self.matricule_input.setText(student["matricule"] or "")
            self.nom_input.setText(student["nom"])
            self.prenom_input.setText(student["prenom"])
            self.classe_input.setText(student["classe"])
            self.annee_input.setText(student["annee_scolaire"])
            self.total_du_input.setValue(float(student["total_du"]))

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Matricule", self.matricule_input)
        form.addRow("Nom", self.nom_input)
        form.addRow("Prénom", self.prenom_input)
        form.addRow("Classe", self.classe_input)
        form.addRow("Année scolaire", self.annee_input)
        form.addRow("Montant total dû", self.total_du_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        try:
            values = (
                self.nom_input.text(),
                self.prenom_input.text(),
                self.classe_input.text(),
                self.annee_input.text(),
                self.total_du_input.value(),
            )
            matricule = self.matricule_input.text().strip() or None
            if self.student_id is None:
                calcul_service.ajouter_eleve(*values, matricule=matricule)
            else:
                calcul_service.modifier_eleve(self.student_id, *values, matricule=matricule)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Vérification des informations", str(exc))


class PaymentDialog(QDialog):
    def __init__(self, student, parent=None):
        super().__init__(parent)
        self.student = student
        self.payment = None
        self.setWindowTitle("Enregistrer un paiement")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        identity = QLabel(
            f"{student['nom']} {student['prenom']} · {student['classe']}\n"
            f"Total dû : {_montant(student['total_du'])}    "
            f"Déjà payé : {_montant(student['total_paye'])}    "
            f"Reste : {_montant(student['solde'])}"
        )
        identity.setObjectName("summaryPanel")
        layout.addWidget(identity)

        form = QFormLayout()
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, max(0, float(student["solde"])))
        self.amount_input.setDecimals(0)
        self.amount_input.setGroupSeparatorShown(True)
        self.amount_input.setSuffix(" FCFA")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Espèces", "Chèque", "Virement", "Mobile Money"])
        self.date_input = QDateEdit(QDate.currentDate())
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        self.date_input.setCalendarPopup(True)
        form.addRow("Montant versé", self.amount_input)
        form.addRow("Mode de paiement", self.mode_combo)
        form.addRow("Date", self.date_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setEnabled(float(student["solde"]) > 0)
        self.amount_input.valueChanged.connect(
            lambda amount: self.save_button.setEnabled(amount > 0)
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        try:
            self.payment = calcul_service.enregistrer_paiement(
                self.student["id"],
                self.amount_input.value(),
                self.mode_combo.currentText(),
                self.date_input.date().toString("yyyy-MM-dd"),
            )
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Paiement non enregistré", str(exc))


class StudentDetailDialog(QDialog):
    def __init__(self, student, parent=None):
        super().__init__(parent)
        self.student = student
        self.setWindowTitle(f"Fiche élève - {student['nom']} {student['prenom']}")
        self.setMinimumSize(850, 480)

        layout = QVBoxLayout(self)
        balance = QLabel(
            f"{student['nom']} {student['prenom']}  ·  {student['classe']}  ·  "
            f"Année {student['annee_scolaire']}\n"
            f"Total dû : {_montant(student['total_du'])}    "
            f"Payé : {_montant(student['total_paye'])}    "
            f"Solde restant : {_montant(student['solde'])}"
        )
        balance.setObjectName("summaryPanel")
        layout.addWidget(balance)

        payments = calcul_service.historique(student["id"])
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(
            ["Date", "N° reçu", "Mode de paiement", "Montant payé", "Solde après paiement"]
        )
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payment_ids = []
        for row_index, payment in enumerate(payments):
            self.payment_ids.append(payment["id"])
            self.history_table.insertRow(row_index)
            values = [
                date.fromisoformat(payment["date_paiement"]).strftime("%d/%m/%Y"),
                payment["numero_recu"],
                payment["mode_paiement"],
                _montant(payment["montant"]),
                _montant(payment["solde_apres"]),
            ]
            for column, value in enumerate(values):
                self.history_table.setItem(row_index, column, QTableWidgetItem(value))
        if payments:
            self.history_table.selectRow(len(payments) - 1)
        layout.addWidget(self.history_table)

        actions = QHBoxLayout()
        self.open_receipt_button = QPushButton("Ouvrir le reçu PDF")
        self.open_receipt_button.setEnabled(bool(payments))
        self.open_receipt_button.clicked.connect(self._open_selected_receipt)
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        actions.addWidget(self.open_receipt_button)
        actions.addStretch()
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def _open_selected_receipt(self):
        selected = self.history_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Sélection requise", "Sélectionnez un paiement.")
            return
        payment_id = self.payment_ids[selected[0].row()]
        try:
            receipt_path = pdf_service.generer_recu(payment_id)
            _ouvrir_pdf(self, receipt_path)
        except Exception as exc:
            QMessageBox.critical(self, "Reçu indisponible", str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.setWindowTitle("EduPay - Gestion des frais scolaires")
        self.resize(1280, 780)
        self._student_rows = {}
        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget#contentArea { background: #f3f6fa; color: #243247; }
            QLabel { color: #34445a; }
            QLabel#pageTitle { color: #172b4d; font-size: 20pt; font-weight: 700; }
            QLabel#summaryPanel {
                background: #ffffff; border: 1px solid #dce4ee;
                border-left: 4px solid #1672b8; border-radius: 6px;
                color: #26364a; font-weight: 600; padding: 12px;
            }
            QLabel#metricValue { color: #172b4d; font-size: 19pt; font-weight: 700; }
            QFrame#sidebar { background: #173c54; }
            QFrame#sidebar QLabel { color: #ffffff; }
            QPushButton#navButton {
                background: transparent; border: 0; border-radius: 5px;
                color: #e1edf5; padding: 11px 12px; text-align: left;
            }
            QPushButton#navButton:hover, QPushButton#navButton:checked { background: #285c78; color: #ffffff; }
            QPushButton#sidebarAction { background: #285c78; color: #ffffff; text-align: left; }
            QPushButton#sidebarAction:hover { background: #347493; }
            QPushButton#sidebarAction:disabled { background: #203f53; color: #91a9b7; }
            QWidget#panel, QFrame#metricCard {
                background: #ffffff; border: 1px solid #dce4ee; border-radius: 6px;
            }
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px;
                color: #1f2937; min-height: 22px; padding: 6px 8px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus { border: 1px solid #1672b8; }
            QPushButton {
                background: #1672b8; border: 0; border-radius: 5px; color: #ffffff;
                font-weight: 600; min-height: 22px; padding: 8px 13px;
            }
            QPushButton:hover { background: #0d5f9e; }
            QPushButton#secondaryButton { background: #e8eef5; color: #26415d; }
            QPushButton#secondaryButton:hover { background: #d8e3ef; }
            QPushButton#addButton { background: #168477; }
            QPushButton#addButton:hover { background: #116c62; }
            QTableWidget {
                background: #ffffff; alternate-background-color: #f7f9fc;
                border: 1px solid #dce4ee; border-radius: 6px;
                gridline-color: #e7edf4; selection-background-color: #dceeff;
                selection-color: #163b5c;
            }
            QHeaderView::section {
                background: #eaf0f6; border: 0; border-bottom: 1px solid #d6e0ea;
                color: #34445a; font-weight: 700; padding: 9px 7px;
            }
            """
        )
        central = QWidget()
        central.setObjectName("contentArea")
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 18, 14, 14)
        brand = QLabel("EduPay")
        brand.setStyleSheet("font-size: 19pt; font-weight: 700; padding: 8px 4px 22px;")
        sidebar_layout.addWidget(brand)
        self.dashboard_nav = self._nav_button("Tableau de bord")
        self.students_nav = self._nav_button("Élèves")
        sidebar_layout.addWidget(self.dashboard_nav)
        sidebar_layout.addWidget(self.students_nav)
        sidebar_layout.addSpacing(20)
        actions_title = QLabel("ACTIONS ÉLÈVE")
        actions_title.setStyleSheet("color: #a8bfce; font-size: 8pt; font-weight: 700; padding: 4px 8px;")
        sidebar_layout.addWidget(actions_title)
        self.edit_button = self._sidebar_action("Modifier l'élève", self.edit_student)
        self.detail_button = self._sidebar_action("Fiche / historique", self.open_student_record)
        self.payment_button = self._sidebar_action("Enregistrer paiement", self.record_payment)
        sidebar_layout.addWidget(self.edit_button)
        sidebar_layout.addWidget(self.detail_button)
        sidebar_layout.addWidget(self.payment_button)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(QLabel("Gestion des frais scolaires"))

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_dashboard_page())
        self.pages.addWidget(self._build_students_page())
        self.dashboard_nav.clicked.connect(lambda: self._show_page(0))
        self.students_nav.clicked.connect(lambda: self._show_page(1))
        self.dashboard_nav.setChecked(True)
        root.addWidget(sidebar)
        root.addWidget(self.pages, 1)
        self.setCentralWidget(central)

    def _nav_button(self, text):
        button = QPushButton(text)
        button.setObjectName("navButton")
        button.setCheckable(True)
        return button

    def _sidebar_action(self, text, callback):
        button = QPushButton(text)
        button.setObjectName("sidebarAction")
        button.setEnabled(False)
        button.clicked.connect(callback)
        return button

    def _show_page(self, index):
        self.pages.setCurrentIndex(index)
        self.dashboard_nav.setChecked(index == 0)
        self.students_nav.setChecked(index == 1)
        self._update_actions()
        if index == 0:
            self.refresh_dashboard()

    def _build_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        title = QLabel("Tableau de bord")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.dashboard_metrics = {}
        grid = QGridLayout()
        grid.setSpacing(12)
        for index, (key, label) in enumerate(
            (("students", "Élèves inscrits"), ("due", "Total dû"),
             ("paid", "Total encaissé"), ("remaining", "Total restant"))
        ):
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.addWidget(QLabel(label))
            value = QLabel("0")
            value.setObjectName("metricValue")
            card_layout.addWidget(value)
            grid.addWidget(card, index // 2, index % 2)
            self.dashboard_metrics[key] = value
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def _build_students_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        title = QLabel("Élèves")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        tools = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom, prénom ou matricule")
        self.search_input.textChanged.connect(self.refresh_students)
        tools.addWidget(self.search_input, 1)
        self.add_button = QPushButton("Ajouter un élève")
        self.add_button.setObjectName("addButton")
        self.add_button.clicked.connect(self.add_student)
        tools.addWidget(self.add_button)
        layout.addLayout(tools)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("summaryPanel")
        layout.addWidget(self.summary_label)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Matricule", "Nom", "Prénom", "Classe", "Année", "Total dû", "Payé", "Solde restant", "Statut"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemDoubleClicked.connect(lambda _item: self.open_student_record())
        layout.addWidget(self.table, 1)

        self.table.itemSelectionChanged.connect(self._update_actions)
        return page

    def _selected_student(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        student_id = int(self.table.item(selected[0].row(), 0).text())
        return self._student_rows.get(student_id)

    def _update_actions(self):
        enabled = self.pages.currentIndex() == 1 and self._selected_student() is not None
        self.edit_button.setEnabled(enabled)
        self.detail_button.setEnabled(enabled)
        self.payment_button.setEnabled(enabled)

    def refresh_all(self):
        self.refresh_students()
        self.refresh_dashboard()

    def refresh_students(self):
        try:
            students = calcul_service.lister_eleves(self.search_input.text())
        except Exception as exc:
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Base de données indisponible", f"Erreur de chargement : {exc}")
            return

        self._student_rows = {student["id"]: student for student in students}
        self.table.setRowCount(0)
        totals = (
            sum(float(student["total_du"]) for student in students),
            sum(float(student["total_paye"]) for student in students),
            sum(float(student["solde"]) for student in students),
        )
        self.summary_label.setText(
            f"{len(students)} élève(s)    Total dû : {_montant(totals[0])}    "
            f"Payé : {_montant(totals[1])}    Restant : {_montant(totals[2])}"
        )
        status_colors = {
            "Soldé": ("#d9f3e7", "#176b45"),
            "Partiellement payé": ("#fff0cf", "#875b08"),
            "Non payé": ("#fde2e2", "#9b3030"),
        }
        for row_index, student in enumerate(students):
            self.table.insertRow(row_index)
            values = [
                str(student["id"]), student.get("matricule") or "-", student["nom"],
                student["prenom"], student["classe"], student["annee_scolaire"],
                _montant(student["total_du"]), _montant(student["total_paye"]),
                _montant(student["solde"]), student["statut"],
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 9:
                    background, foreground = status_colors[student["statut"]]
                    item.setBackground(QColor(background))
                    item.setForeground(QColor(foreground))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, column, item)
        self._update_actions()

    def refresh_dashboard(self):
        dashboard = calcul_service.tableau_de_bord()
        students = calcul_service.lister_eleves()
        total_due = sum(float(student["total_du"]) for student in students)
        self.dashboard_metrics["students"].setText(str(dashboard["nb_eleves"]))
        self.dashboard_metrics["due"].setText(_montant(total_due))
        self.dashboard_metrics["paid"].setText(_montant(dashboard["total_encaisse"]))
        self.dashboard_metrics["remaining"].setText(_montant(dashboard["total_restant"]))

    def add_student(self):
        dialog = StudentFormDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()

    def edit_student(self):
        student = self._selected_student()
        if student is None:
            return
        dialog = StudentFormDialog(student, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()

    def open_student_record(self):
        student = self._selected_student()
        if student is not None:
            StudentDetailDialog(student, self).exec()

    def record_payment(self):
        student = self._selected_student()
        if student is None:
            return
        dialog = PaymentDialog(student, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.refresh_all()
        try:
            receipt_path = pdf_service.generer_recu(dialog.payment["id"])
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Paiement enregistré",
                f"Le paiement est enregistré, mais le reçu PDF n'a pas pu être créé :\n{exc}",
            )
            return
        answer = QMessageBox.question(
            self,
            "Paiement enregistré",
            f"Paiement enregistré. Reçu N° {dialog.payment['numero_recu']}.\n\n"
            "Ouvrir le reçu PDF maintenant ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            _ouvrir_pdf(self, receipt_path)


if __name__ == "__main__":
    init_db()
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
