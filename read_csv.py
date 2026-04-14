import csv
# import measurements2 as m_script
import os 
import json

# def mesure(self):
#     if not self.chemin_image:
#         print("Erreur : Aucune image chargée.")
#         return

#     nom_image = os.path.basename(self.chemin_image)
    
#     nom_masque = nom_image.replace(".jpg", ".png")

#     base_dir = "segmentation_masks"
#     art_dir = os.path.join(base_dir, "arteries")
#     vein_dir = os.path.join(base_dir, "veins")
#     od_dir = os.path.join(base_dir, "od")
#     output_csv = "mesures.csv"

#     args = ["measurement.py", art_dir, vein_dir, od_dir, output_csv, nom_masque]
    
#     try:
#         m_script.main(args)
#         self.lbl_affiche_mesures.setText(f"Analyse de {nom_masque} terminée !")
#     except Exception as e:
#         self.lbl_affiche_mesures.setText(f"Erreur : {str(e)}")


    


def read_first_row(file):
    with open(file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        try:
            first_row = next(reader)
            
            return first_row
        except StopIteration:
            return None 
        



def classer_donnees(row):
    """
    Organise la ligne CSV brute en un dictionnaire structuré :
    Racine (Arteries/Veins/AV) -> Région (A/B/C/Out/All) -> Groupe -> Mesures
    """
    if not row: return {}

    groupes = ["Secteurs", "Calibre", "Topologie", "Points_critiques", "Tortuosite"]
    zones = ["A", "B", "C", "Out", "All"]
    organes = ["Arteries", "Veins", "AV"]

    classement = {o: {z: {g: {} for g in groupes} for z in zones} for o in organes}

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

        #Region 
        if "_A_" in key: region = "A"
        elif "_B_" in key: region = "B"
        elif "_C_" in key: region = "C"
        elif "_Out_" in key: region = "Out"
        elif "_All_" in key: region = "All"
        else: continue

        # Secteurs
        if key.startswith(("wpr", "vzr")):
            famille, secteur = key[:3], key[3]
            if famille not in classement[racine][region]["Secteurs"]:
                classement[racine][region]["Secteurs"][famille] = {}
            classement[racine][region]["Secteurs"][famille][secteur] = val_convertie

        #Calibre       
        elif "Caliber" in key or "nbX" in key or "avr" in key:
            classement[racine][region]["Calibre"][key] = val_convertie

        #Topologie
        elif "fractal" in key or "nbCC" in key or "area" in key or "Depth" in key or "State" in key:
            classement[racine][region]["Topologie"][key] = val_convertie

        #Point
        elif "EndP" in key or "CrossP" in key or "OverlapP" in key:
            classement[racine][region]["Points_critiques"][key] = val_convertie

        #Tortuosité 

        elif "Tort" in key:
            classement[racine][region]["Tortuosite"][key] = val_convertie

    return classement


def write_json(data, filename="data.json"):
    """
    Sauvegarde le dictionnaire classé dans un fichier JSON.
    """
    with open(filename, "w", encoding="utf-8") as f:
        # On utilise le module json pour écrire le dictionnaire
        json.dump(data, f, indent=4, ensure_ascii=False)



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

    # On filtre d'abord les organes (Arteries, Veins, AV)
    for nom_organe, contenu_organe in data.items():
        # Si on ne précise pas d'organe, on les garde tous
        # Si on précise, on ne garde que ceux qui correspondent
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


def export_txt(data, filename="rapport_mesures.txt"):
        
        """Génère un rapport lisible à partir du dictionnaire de résultats."""

        with open(filename, "w", encoding="utf-8") as f:

            if not data:
                f.write("Aucune donnée sélectionnée.\n")
                return

            for organe, zones in data.items():
                f.write(f"- ORGANE : {organe.upper()}\n")
                f.write("-" * 30 + "\n")
                
                for zone, groupes in zones.items():
                    f.write(f"   - Zone {zone}\n")
                    
                    for groupe, mesures in groupes.items():
                        f.write(f"     - {groupe}:\n")
                        
                        # On regarde chaque mesure dans le groupe
                        for nom_mesure, valeur in mesures.items():
                            
                            if type(valeur) is dict:
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

