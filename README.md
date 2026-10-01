# EduPay

Application de gestion des frais scolaires, développée en Python avec SQLite et PySide6.

## Objectif

Cette application aide à gérer les élèves, suivre les paiements, calculer les soldes restants et générer des reçus PDF.

## Contributeur principal

- SAMVICdev

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
