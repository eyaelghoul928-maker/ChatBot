CREATE DATABASE IF NOT EXISTS chatbot_db_test
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE chatbot_db_test;

-- 1) Sociétés
CREATE TABLE IF NOT EXISTS societes (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    nom            VARCHAR(255) NOT NULL,
    secteur        VARCHAR(255) NULL,
    adresse        VARCHAR(255) NULL,
    ville          VARCHAR(100) NULL,
    pays           VARCHAR(100) NULL,
    date_creation  DATE NULL
) ENGINE=InnoDB;

-- 2) Clients
CREATE TABLE IF NOT EXISTS clients (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nom          VARCHAR(255) NOT NULL,
    email        VARCHAR(255) NULL,
    telephone    VARCHAR(50) NULL,
    adresse      VARCHAR(255) NULL,
    ville        VARCHAR(100) NULL,
    pays         VARCHAR(100) NULL,
    societe_id   INT NULL,
    CONSTRAINT fk_clients_societe
      FOREIGN KEY (societe_id) REFERENCES societes(id)
) ENGINE=InnoDB;

-- 3) Livreurs
CREATE TABLE IF NOT EXISTS livreurs (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    nom            VARCHAR(255) NOT NULL,
    telephone      VARCHAR(50) NULL,
    vehicule       VARCHAR(100) NULL,
    date_embauche  DATE NULL,
    actif          TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

-- 4) Colis
CREATE TABLE IF NOT EXISTS colis (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    code_colis      VARCHAR(100) NOT NULL,
    description     VARCHAR(255) NULL,
    poids_kg        DECIMAL(10,2) NULL,
    statut          ENUM('en_cours','livre','retour','annule') NOT NULL DEFAULT 'en_cours',
    date_creation   DATETIME NOT NULL,
    date_livraison  DATETIME NULL,
    client_id       INT NULL,
    livreur_id      INT NULL,
    societe_id      INT NULL,
    CONSTRAINT fk_colis_client
      FOREIGN KEY (client_id) REFERENCES clients(id),
    CONSTRAINT fk_colis_livreur
      FOREIGN KEY (livreur_id) REFERENCES livreurs(id),
    CONSTRAINT fk_colis_societe
      FOREIGN KEY (societe_id) REFERENCES societes(id),
    INDEX idx_colis_date_livraison (date_livraison),
    INDEX idx_colis_statut (statut)
) ENGINE=InnoDB;

