"""
seed.py — Données de test pour système de livraison tunisien
Usage : python database/seed.py --fast
"""
import asyncio, sys, random
from datetime import datetime, timedelta
import aiomysql
from config import settings

NOMS = ["Ben Ali","Chaabane","Maatoug","Trabelsi","Hammami","Jebali",
        "Nasri","Bouzid","Chebbi","Dridi","Fenniche","Rhouma","Ayari",
        "Oueslati","Zouari","Aloui","Mansour","Karray","Haddad","Slim"]
PRENOMS = ["Mohamed","Ahmed","Fatma","Sarra","Youssef","Nadia","Khalil",
           "Amira","Rami","Ines","Bilel","Meryem","Hatem","Dorra","Karim"]
VILLES = ["Tunis","Sfax","Sousse","Kairouan","Monastir","Gabes",
          "Nabeul","Gafsa","Bizerte","Ariana","Ben Arous","Manouba",
          "Medenine","Beja","Mahdia","Sidi Bouzid","Le Kef"]
SOCIETES = [
    ("Tunisie Shop","ecommerce","standard",7.0),
    ("Carthage Store","ecommerce","premium",8.5),
    ("Medina Market","retail","standard",7.0),
    ("Pharma Direct","pharma","entreprise",12.0),
    ("Mode Tunisie","mode","premium",8.5),
    ("Tech Express","electronique","entreprise",10.0),
    ("Jumia TN","ecommerce","entreprise",10.0),
    ("Mabrouk Shop","ecommerce","standard",7.0),
    ("Sfax Commerce","retail","premium",8.5),
    ("Bio Tunis","alimentaire","standard",7.0),
]
VEHICULES = ["moto","moto","moto","voiture","camionnette"]
DESCRIPTIONS = ["Vetements","Electronique","Cosmetiques","Alimentation",
                "Livres","Chaussures","Accessoires","Medicaments","Divers"]
STATUTS = ["en_attente","pris_en_charge","en_transit","en_cours_livraison",
           "livre","livre","livre","tente_echoue","retourne","annule"]
POIDS_ST = [5,8,10,10,40,40,40,8,6,3]
MOTIFS   = ["Client absent","Adresse introuvable","Client a refuse",
            "Telephone ne repond pas","Acces impossible"]
RUES     = ["Habib Bourguiba","de la Republique","Ibn Khaldoun",
            "Farhat Hached","du Commerce","de la Paix"]


async def get_conn():
    return await aiomysql.connect(
        host=settings.db_host, port=settings.db_port,
        user=settings.db_user, password=settings.db_password,
        db=settings.db_name, charset="utf8mb4", autocommit=True,
    )


async def seed_societes(conn):
    async with conn.cursor() as cur:
        for nom, secteur, contrat, tarif in SOCIETES:
            ville = random.choice(VILLES)
            await cur.execute(
                "INSERT IGNORE INTO societes (nom,secteur,ville,gouvernorat,telephone,email,contrat,tarif_base) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (nom, secteur, ville, ville,
                 f"+216 {random.randint(70,99)} {random.randint(100,999)} {random.randint(100,999)}",
                 f"contact@{nom.lower().replace(' ','')}.tn",
                 contrat, tarif)
            )
    print(f"  OK {len(SOCIETES)} societes")


async def seed_livreurs(conn, n=50):
    async with conn.cursor() as cur:
        for i in range(n):
            ville = random.choice(VILLES)
            await cur.execute(
                "INSERT IGNORE INTO livreurs (nom,prenom,telephone,email,zone_principale,gouvernorat,vehicule,statut,nb_livraisons,note_moyenne) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (random.choice(NOMS), random.choice(PRENOMS),
                 f"+216 {random.randint(20,59)} {random.randint(100,999)} {random.randint(100,999)}",
                 f"livreur{i}@livraison.tn", ville, ville,
                 random.choice(VEHICULES),
                 random.choices(["disponible","en_livraison","indisponible"],weights=[50,35,15])[0],
                 random.randint(10,2000), round(random.uniform(3.0,5.0),2))
            )
    print(f"  OK {n} livreurs")


async def seed_clients(conn, n=2000):
    async with conn.cursor() as cur:
        batch = []
        for i in range(n):
            ville = random.choice(VILLES)
            batch.append((
                random.choice(NOMS), random.choice(PRENOMS),
                f"+216 {random.randint(20,99)} {random.randint(100,999)} {random.randint(100,999)}",
                f"{random.randint(1,200)} Rue {random.choice(RUES)}",
                ville, ville,
            ))
            if len(batch) == 500:
                await cur.executemany(
                    "INSERT IGNORE INTO clients (nom,prenom,telephone,adresse,ville,gouvernorat) VALUES (%s,%s,%s,%s,%s,%s)",
                    batch)
                batch = []
        if batch:
            await cur.executemany(
                "INSERT IGNORE INTO clients (nom,prenom,telephone,adresse,ville,gouvernorat) VALUES (%s,%s,%s,%s,%s,%s)",
                batch)
    print(f"  OK {n} clients")


async def seed_colis(conn, n=10000):
    async with conn.cursor() as cur:
        await cur.execute("SELECT id FROM societes")
        soc_ids = [r[0] for r in await cur.fetchall()]
        await cur.execute("SELECT id FROM livreurs")
        liv_ids = [r[0] for r in await cur.fetchall()]
        await cur.execute("SELECT id,ville,gouvernorat FROM clients LIMIT 3000")
        clients = await cur.fetchall()

    batch = []
    ref = 10000
    async with conn.cursor() as cur:
        for i in range(n):
            cl = random.choice(clients)
            statut = random.choices(STATUTS, weights=POIDS_ST)[0]
            days   = random.randint(0, 365)
            date_c = datetime.now() - timedelta(days=days, hours=random.randint(7,20))
            date_l = date_c + timedelta(hours=random.randint(6,72)) if statut == "livre" else None
            motif  = random.choice(MOTIFS) if statut in ["tente_echoue","retourne"] else None
            batch.append((
                f"COL{ref:08d}",
                random.choice(soc_ids), cl[0], random.choice(liv_ids),
                random.choice(DESCRIPTIONS),
                round(random.uniform(0.1,15.0),3),
                round(random.uniform(10.0,500.0),3),
                random.randint(1,5),
                random.choice([True,False,False,False]),
                statut,
                random.randint(1,3) if statut in ["tente_echoue","retourne"] else 0,
                motif,
                round(random.choice([7.0,8.5,10.0,12.0]),3),
                round(random.uniform(0,300.0),3),
                statut == "livre",
                date_c, date_l,
                f"{random.randint(1,200)} Rue {random.choice(RUES)}",
                cl[1], cl[2],
            ))
            ref += 1
            if len(batch) == 500:
                await cur.executemany("""
                    INSERT INTO colis
                    (reference,societe_id,client_id,livreur_id,description,poids_kg,
                     valeur_declaree,nb_articles,fragile,statut,tentatives,motif_echec,
                     prix_livraison,montant_cod,cod_collecte,date_creation,
                     date_livraison_eff,adresse_livraison,ville_livraison,gouvernorat_livraison)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, batch)
                print(f"    {i+1}/{n} colis...", end="\r")
                batch = []
        if batch:
            await cur.executemany("""
                INSERT INTO colis
                (reference,societe_id,client_id,livreur_id,description,poids_kg,
                 valeur_declaree,nb_articles,fragile,statut,tentatives,motif_echec,
                 prix_livraison,montant_cod,cod_collecte,date_creation,
                 date_livraison_eff,adresse_livraison,ville_livraison,gouvernorat_livraison)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, batch)
    print(f"  OK {n} colis")


async def main():
    fast = "--fast" in sys.argv
    print(f"\nSeed livraison - {'rapide' if fast else 'complet'}")
    conn = await get_conn()
    try:
        await seed_societes(conn)
        await seed_livreurs(conn)
        await seed_clients(conn, 2000 if fast else 10000)
        await seed_colis(conn, 10000 if fast else 50000)
        print("\nSeed termine !")
    finally:
        conn.close()

asyncio.run(main())