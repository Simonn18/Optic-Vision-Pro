import csv
import os 
import json


def classer_donnees(row):
    """
    Organise la ligne CSV brute en un dictionnaire structuré :
    IMAGE_ID -> Racine (Arteries/Veins/AV) -> Région (A/B/C/Out/All) -> Bloc -> Mesures
    """
    if not isinstance(row, dict):
        print("Erreur : classer_donnees a reçu autre chose qu'un dictionnaire")
        return {}

    groupes = ["quality control", "vessel detection", "geometric metrics"]
    zones = ["A", "B", "C", "Out", "All"]
    organes = ["Arteries", "Veins", "AV"]

    # Initialisation avec IMAGE_ID à la racine
    classement = {
        "IMAGE_ID": row.get("image"),
        "Arteries": {z: {g: {} for g in groupes} for z in zones},
        "Veins": {z: {g: {} for g in groupes} for z in zones},
        "AV": {z: {g: {} for g in groupes} for z in zones}
    }

    for key, value in row.items():
        if key == "image": continue
        
        # convertir en float 
        try:
            val_convertie = float(value)
        except (ValueError, TypeError):
            val_convertie = value 

        # Racine
        if "Arteries" in key: racine = "Arteries"
        elif "Veins" in key: racine = "Veins"
        elif "_AV" in key: racine = "AV"
        else: continue

        # Region 
        if "_A_" in key: region = "A"
        elif "_B_" in key: region = "B"
        elif "_C_" in key: region = "C"
        elif "_Out_" in key: region = "Out"
        elif "_All_" in key: region = "All"
        else: continue

        # --- CLASSEMENT DANS LES NOUVEAUX BLOCS ---

        # 1. Quality Control (wpr et vzr)
        if key.startswith(("wpr", "vzr")):
            classement[racine][region]["quality control"][key] = val_convertie

        # 2. Vessel Detection (nbX)
        elif "nbX" in key:
            classement[racine][region]["vessel detection"][key] = val_convertie

        # 3. Geometric Metrics (Tout le reste : Caliber, fractal, Tort, area, etc.)
        else:
            # On met tout ce qui reste dans geometric metrics (calibres, points critiques, topologie, tortuosité)
            classement[racine][region]["geometric metrics"][key] = val_convertie

    return classement




def csv_to_jsons(csv_file, base_dir):
    """
    Crée un sous-dossier 'mesures_json' dans base_dir et y enregistre
    un JSON par image.
    """
    if not os.path.exists(csv_file):
        print(f"Erreur : {csv_file} introuvable.")
        return

    output_dir = os.path.join(base_dir, "mesures_json")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nom_image = row.get("image", "").strip()
            if not nom_image:
                continue

            data_structuree = classer_donnees(row)

            nom_base = os.path.splitext(nom_image)[0]
            # On enregistre DANS le sous-dossier
            chemin_json = os.path.join(output_dir, f"{nom_base}_data.json")

            with open(chemin_json, "w", encoding="utf-8") as json_f:
                json.dump(data_structuree, json_f, indent=4, ensure_ascii=False)
            
            print(f"JSON généré dans le sous-dossier : {chemin_json}")



def requete(data, organe=None, zone=None, groupe=None):
    """
    Explore le dictionnaire de données pour extraire des mesures spécifiques
    
    Cette fonction agit comme un filtre en trois étapes :
    1 : Organe (Ex: "Arteries" ou ["Arteries", "veins"])
    2 : Zone (Ex: 'A' ou ["A", "C"])
    3 : Groupe (Ex: "Calibre" ou ["Calibre", "Topologie"])

    Cette fonction returne un dictionnaire filtré contenant uniquement les "branches" demandées.
    """
    
    resultat = {}
    if "IMAGE_ID" in data:
        resultat["IMAGE_ID"] = data["IMAGE_ID"]

    for nom_organe, contenu_organe in data.items():
        if nom_organe == "IMAGE_ID": continue

        if organe is None or nom_organe in organe:
            
            # On crée un dictionnaire pour cet organe dans notre résultat
            resultat[nom_organe] = {}

            # On filtre ensuite les zones 
            for nom_zone, contenu_zone in contenu_organe.items():
                if zone is None or nom_zone in zone:
                    
                    # On crée un nouveau dictionnaire pour cette zone
                    resultat[nom_organe][nom_zone] = {}

                    # On Filtre finalement les groupes 
                    for nom_groupe, mesures in contenu_zone.items():
                        if groupe is None or nom_groupe in groupe:
                            
                            # On copie les mesures finales
                            resultat[nom_organe][nom_zone][nom_groupe] = mesures

    return resultat




def image_est_dans_csv(csv_file, nom_image):
    """Vérifie si une image est déjà dans le CSV."""
    if not os.path.exists(csv_file):
        return False
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("image", "").strip() == nom_image:
                return True
    return False


def export_txt(data, filename="rapport_mesures.txt"):
    """Génère le rapport .txt avec une vérification de type."""
    if not isinstance(data, dict):
        print(f"Erreur export_txt : 'data' est de type {type(data)} au lieu de dict.")
        return

    with open(filename, "w", encoding="utf-8") as f:
        # Écriture de l'ID de l'image
        nom_image = data.get("IMAGE_ID", "Inconnu")
        f.write(f"IMAGE ANALYSÉE : {nom_image}\n")
        f.write("="*60 + "\n\n")

        for organe, zones in data.items():
            if organe == "IMAGE_ID": 
                continue 
            
            # Autre sécurité : vérifier que 'zones' est bien un dictionnaire avant d'itérer
            if not isinstance(zones, dict):
                continue

            f.write(f"- ORGANE : {organe.upper()}\n")
            f.write("-" * 30 + "\n")
            
            for zone, groupes in zones.items():
                if not isinstance(groupes, dict): continue
                
                f.write(f"   - Zone {zone}\n")
                for groupe, mesures in groupes.items():
                    if not isinstance(mesures, dict): continue
                    
                    f.write(f"     - {groupe}:\n")
                    for nom_mesure, valeur in mesures.items():
                        if isinstance(valeur, dict):
                            f.write(f"      - {nom_mesure} :\n")
                            for sous_nom, sous_valeur in valeur.items():
                                f.write(f"          {sous_nom} : {sous_valeur}\n")
                        else:
                            f.write(f"      - {nom_mesure} : {valeur}\n")
            f.write("\n")
        f.write("="*60 + "\n")



if __name__ == "__main__":

    if os.path.exists('data.json'):
        with open('data.json', 'r') as f:
            data_test = json.load(f)
            print("Test local réussi")
