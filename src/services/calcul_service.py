import sqlite3
from datetime import date

from src.database import eleve_dao, paiement_dao

MODES_PAIEMENT = ("Espèces", "Chèque", "Virement", "Mobile Money")


class ScolariteError(Exception):
    """Erreur de règle métier, à afficher à l'utilisateur dans un QMessageBox."""


# ---------- Validation ----------

def _nombre(valeur, champ, strictement_positif=True):
    """Convertit une saisie en float et vérifie qu'elle est valide."""
    try:
        nombre = float(str(valeur).replace(" ", "").replace(",", "."))
    except ValueError:
        raise ScolariteError(f"{champ} doit être un nombre.")
    if strictement_positif and nombre <= 0:
        raise ScolariteError(f"{champ} doit être supérieur à 0.")
    if nombre < 0:
        raise ScolariteError(f"{champ} ne peut pas être négatif.")
    return nombre


def _texte(valeur, champ):
    valeur = (valeur or "").strip()
    if not valeur:
        raise ScolariteError(f"Le champ « {champ} » est obligatoire.")
    return valeur


# ---------- Solde et statut ----------

def calculer_statut(total_du, total_paye):
    if total_paye <= 0:
        return "Non payé"
    if total_paye >= total_du:
        return "Soldé"
    return "Partiellement payé"


def solde(eleve_id):
    eleve = eleve_dao.get(eleve_id)
    if eleve is None:
        raise ScolariteError("Élève introuvable.")
    return eleve["total_du"] - paiement_dao.somme_par_eleve(eleve_id)


def statut(eleve_id):
    eleve = eleve_dao.get(eleve_id)
    if eleve is None:
        raise ScolariteError("Élève introuvable.")
    return calculer_statut(eleve["total_du"], paiement_dao.somme_par_eleve(eleve_id))


def lister_eleves(texte="", classe=None, statut_filtre=None):
    """Liste les élèves avec total payé, solde et statut (filtrable)."""
    resultat = []
    for row in eleve_dao.lister_avec_solde(texte, classe):
        eleve = dict(row)
        eleve["statut"] = calculer_statut(eleve["total_du"], eleve["total_paye"])
        if statut_filtre and eleve["statut"] != statut_filtre:
            continue
        resultat.append(eleve)
    return resultat


# ---------- Élèves ----------

def ajouter_eleve(nom, prenom, classe, annee_scolaire, total_du, matricule=None):
    return eleve_dao.ajouter(
        _texte(nom, "Nom"),
        _texte(prenom, "Prénom"),
        _texte(classe, "Classe"),
        _texte(annee_scolaire, "Année scolaire"),
        _nombre(total_du, "Le montant total dû", strictement_positif=False),
        matricule=(matricule or None),
    )


def modifier_eleve(eleve_id, nom, prenom, classe, annee_scolaire, total_du, matricule=None):
    total_du = _nombre(total_du, "Le montant total dû", strictement_positif=False)
    deja_paye = paiement_dao.somme_par_eleve(eleve_id)
    if total_du < deja_paye:
        raise ScolariteError(
            f"Le total dû ne peut pas être inférieur aux paiements déjà reçus ({deja_paye:.0f})."
        )
    eleve_dao.modifier(
        eleve_id,
        _texte(nom, "Nom"),
        _texte(prenom, "Prénom"),
        _texte(classe, "Classe"),
        _texte(annee_scolaire, "Année scolaire"),
        total_du,
        matricule=(matricule or None),
    )


def supprimer_eleve(eleve_id):
    try:
        eleve_dao.supprimer(eleve_id)
    except sqlite3.IntegrityError:
        raise ScolariteError(
            "Impossible de supprimer cet élève : il a des paiements enregistrés."
        )


# ---------- Paiements ----------

def enregistrer_paiement(eleve_id, montant, mode, date_paiement=None):
    """Valide, calcule le nouveau solde, génère le n° de reçu et enregistre."""
    montant = _nombre(montant, "Le montant")
    if mode not in MODES_PAIEMENT:
        raise ScolariteError("Mode de paiement invalide.")

    if date_paiement:
        try:
            date.fromisoformat(date_paiement)
        except ValueError:
            raise ScolariteError("Date invalide (format attendu : AAAA-MM-JJ).")
    else:
        date_paiement = date.today().isoformat()

    solde_actuel = solde(eleve_id)
    if montant > solde_actuel + 0.001:
        raise ScolariteError(
            f"Le montant saisi dépasse le solde restant ({solde_actuel:.0f})."
        )

    solde_apres = solde_actuel - montant
    numero_recu = paiement_dao.prochain_numero_recu()
    paiement_id = paiement_dao.ajouter(
        eleve_id, montant, mode, date_paiement, numero_recu, solde_apres
    )
    return {"id": paiement_id, "numero_recu": numero_recu, "solde_apres": solde_apres}


def historique(eleve_id):
    return [dict(p) for p in paiement_dao.lister_par_eleve(eleve_id)]


# ---------- Tableau de bord ----------

def tableau_de_bord():
    eleves = lister_eleves()
    return {
        "nb_eleves": len(eleves),
        "total_encaisse": paiement_dao.total_encaisse(),
        "total_restant": sum(e["solde"] for e in eleves),
        "nb_non_soldes": sum(1 for e in eleves if e["statut"] != "Soldé"),
    }