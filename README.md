# EduPay

## EduPay

EduPay est une application de bureau de gestion des frais de scolarité, développée en Python avec PySide6 et SQLite. Elle permet à un établissement scolaire d'enregistrer ses élèves, de suivre les paiements, de calculer automatiquement le solde et le statut de chacun (non payé, partiellement payé, payé), de consulter l'historique des versements et d'éditer des reçus. Un tableau de bord donne en un coup d'œil le nombre d'élèves inscrits, le total dû, le total encaissé et le total restant.

## Objectif

Offrir aux établissements scolaires un outil simple et fiable pour suivre les frais de scolarité. EduPay remplace le suivi sur cahier ou tableur par une application qui centralise les élèves et leurs paiements. Elle calcule automatiquement les soldes et les statuts, évite les erreurs de calcul et permet de retrouver rapidement l'historique de chaque élève. Elle produit aussi des reçus pour les parents et donne à la direction une vue claire de l'argent encaissé et de ce qui reste à recouvrer.

## Contributeur principal

-Kakpovidela

## Prérequis

- Python 3.10+
- pip

## Installation

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
```

## Démarrage

```bash
python main.py
```

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

## Commandes GitHub / push

```bash
git status
git add .
git commit -m "feat: mise a jour application"
git push origin main
```

Pour ne pousser que les fichiers modifiés sur le reçu PDF :

```bash
git add src/services/pdf_service.py tests/test_core.py
git commit -m "feat: mise a jour branding reçu PDF"
git push origin main
```

## Fonctionnalités

- Ajout et suivi des élèves
- Enregistrement des paiements
- Calcul du solde restant
- Génération de reçus PDF
- Recherche rapide des élèves

## Structure du projet

- src/database : couche SQLite et DAO
- src/services : logique métier et génération PDF
- src/ui : interface graphique PySide6
- data : base SQLite et schéma
