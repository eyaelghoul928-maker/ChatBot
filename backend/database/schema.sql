CREATE DATABASE IF NOT EXISTS chatbot_db_test
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE chatbot_db_test;

CREATE TABLE IF NOT EXISTS societes (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nom             VARCHAR(200) NOT NULL,
    secteur         ENUM('ecommerce','retail','pharma','alimentaire','mode','electronique','autre') DEFAULT 'ecommerce',
    ville           VARCHAR(100),
    gouvernorat     VARCHAR(100),
    telephone       VARCHAR(20),
    email           VARCHAR(200),
    contrat         ENUM('standard','premium','entreprise') DEFAULT 'standard',
    tarif_base      DECIMAL(8,3) DEFAULT 7.000,
    nb_colis_total  INT DEFAULT 0,
    actif           BOOLEAN DEFAULT TRUE,
    date_creation   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ville    (ville),
    INDEX idx_contrat  (contrat),
    INDEX idx_secteur  (secteur)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS livreurs (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    telephone       VARCHAR(20),
    email           VARCHAR(200),
    zone_principale VARCHAR(100),
    gouvernorat     VARCHAR(100),
    vehicule        ENUM('moto','voiture','camionnette','velo') DEFAULT 'moto',
    statut          ENUM('disponible','en_livraison','indisponible','conge') DEFAULT 'disponible',
    nb_livraisons   INT DEFAULT 0,
    note_moyenne    DECIMAL(3,2) DEFAULT 0.00,
    actif           BOOLEAN DEFAULT TRUE,
    date_embauche   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_zone    (zone_principale),
    INDEX idx_statut  (statut),
    INDEX idx_vehicule (vehicule)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS clients (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100),
    telephone       VARCHAR(20),
    adresse         TEXT,
    ville           VARCHAR(100),
    gouvernorat     VARCHAR(100),
    nb_commandes    INT DEFAULT 0,
    nb_refus        INT DEFAULT 0,
    actif           BOOLEAN DEFAULT TRUE,
    date_creation   DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ville       (ville),
    INDEX idx_gouvernorat (gouvernorat),
    INDEX idx_telephone   (telephone),
    FULLTEXT idx_nom      (nom, prenom)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS colis (
    id                    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reference             VARCHAR(30) UNIQUE NOT NULL,
    societe_id            INT UNSIGNED NOT NULL,
    client_id             INT UNSIGNED NOT NULL,
    livreur_id            INT UNSIGNED,
    description           VARCHAR(300),
    poids_kg              DECIMAL(6,3),
    valeur_declaree       DECIMAL(10,3) DEFAULT 0,
    nb_articles           SMALLINT DEFAULT 1,
    fragile               BOOLEAN DEFAULT FALSE,
    statut                ENUM('en_attente','pris_en_charge','en_transit','en_cours_livraison','livre','tente_echoue','retourne','annule') DEFAULT 'en_attente',
    tentatives            TINYINT DEFAULT 0,
    motif_echec           VARCHAR(200),
    prix_livraison        DECIMAL(8,3) DEFAULT 7.000,
    montant_cod           DECIMAL(10,3) DEFAULT 0,
    cod_collecte          BOOLEAN DEFAULT FALSE,
    date_creation         DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_prise_charge     DATETIME,
    date_livraison_prev   DATETIME,
    date_livraison_eff    DATETIME,
    adresse_livraison     TEXT,
    ville_livraison       VARCHAR(100),
    gouvernorat_livraison VARCHAR(100),
    INDEX idx_societe          (societe_id),
    INDEX idx_client           (client_id),
    INDEX idx_livreur          (livreur_id),
    INDEX idx_statut           (statut),
    INDEX idx_date             (date_creation),
    INDEX idx_ville_liv        (ville_livraison),
    INDEX idx_statut_date      (statut, date_creation),
    INDEX idx_livreur_statut   (livreur_id, statut),
    INDEX idx_societe_statut   (societe_id, statut)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;