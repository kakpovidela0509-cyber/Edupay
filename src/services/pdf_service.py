import os
from datetime import date

from fpdf import FPDF

from src.database import eleve_dao, paiement_dao
from src.database.connection import BASE_DIR
from src.services.calcul_service import ScolariteError

DOSSIER_RECUS = os.path.join(BASE_DIR, "data", "recus")
NOM_ETABLISSEMENT = "Lycée de Tokoin"  # à remplacer par le nom de ton établissement


def _montant(valeur):
    """Formate un montant : 150000 -> '150 000 FCFA'."""
    return f"{valeur:,.0f}".replace(",", " ") + " FCFA"


def _date_fr(date_iso):
    """'2026-10-01' -> '01/10/2026'."""
    try:
        return date.fromisoformat(date_iso).strftime("%d/%m/%Y")
    except ValueError:
        return date_iso


def _ligne(pdf, libelle, valeur):
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(55, 9, libelle)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 9, str(valeur), new_x="LMARGIN", new_y="NEXT")


def generer_recu(paiement_id, dossier=None):
    """Génère le reçu PDF d'un paiement et retourne le chemin du fichier."""
    paiement = paiement_dao.get(paiement_id)
    if paiement is None:
        raise ScolariteError("Paiement introuvable.")
    eleve = eleve_dao.get(paiement["eleve_id"])
    if eleve is None:
        raise ScolariteError("Élève introuvable.")

    dossier = dossier or DOSSIER_RECUS
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, f"{paiement['numero_recu']}.pdf")

    pdf = FPDF(format="A5")
    pdf.set_margins(15, 15, 15)
    pdf.add_page()

    # En-tête
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, NOM_ETABLISSEMENT, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "REÇU DE PAIEMENT", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"N° {paiement['numero_recu']}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    pdf.line(15, pdf.get_y(), pdf.w - 15, pdf.get_y())
    pdf.ln(6)

    # Informations de l'élève
    _ligne(pdf, "Élève :", f"{eleve['nom']} {eleve['prenom']}")
    _ligne(pdf, "Classe :", eleve["classe"])
    _ligne(pdf, "Année scolaire :", eleve["annee_scolaire"])
    pdf.ln(3)

    # Informations du paiement
    _ligne(pdf, "Date :", _date_fr(paiement["date_paiement"]))
    _ligne(pdf, "Mode de paiement :", paiement["mode_paiement"])
    _ligne(pdf, "Montant payé :", _montant(paiement["montant"]))
    _ligne(pdf, "Solde restant :", _montant(paiement["solde_apres"]))

    # Pied de page
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "Merci pour votre paiement.", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.output(chemin)
    return chemin