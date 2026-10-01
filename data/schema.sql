-- Table des élèves
CREATE TABLE IF NOT EXISTS eleve (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    classe TEXT NOT NULL,
    annee_scolaire TEXT NOT NULL,
    total_du REAL NOT NULL CHECK (total_du >= 0),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Met à jour updated_at à chaque modification d'un élève
CREATE TRIGGER IF NOT EXISTS trg_eleve_updated
AFTER UPDATE ON eleve
BEGIN
    UPDATE eleve SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Table des paiements
CREATE TABLE IF NOT EXISTS paiement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eleve_id INTEGER NOT NULL,
    montant REAL NOT NULL CHECK (montant > 0),
    mode_paiement TEXT NOT NULL CHECK (mode_paiement IN ('Espèces', 'Chèque', 'Virement', 'Mobile Money')),
    date_paiement TEXT NOT NULL,
    numero_recu TEXT NOT NULL UNIQUE,
    solde_apres REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (eleve_id) REFERENCES eleve(id) ON DELETE RESTRICT
);

-- Index pour accélérer la recherche des paiements d'un élève
CREATE INDEX IF NOT EXISTS idx_paiement_eleve ON paiement(eleve_id);