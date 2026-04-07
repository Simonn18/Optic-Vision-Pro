import measurements2 as m_script


#-------------travail avec measurements2 que j'ai modifiÃ©
#-------------il faut pip install cv2,  tqdm, scikit 


def mesure(self):
    if not self.chemin_image:
        print("Erreur : Aucune image chargÃ©e.")
        return

    nom_image = os.path.basename(self.chemin_image)
    
    nom_masque = nom_image.replace(".jpg", ".png")

    base_dir = "segmentation_masks"
    art_dir = os.path.join(base_dir, "arteries")
    vein_dir = os.path.join(base_dir, "veins")
    od_dir = os.path.join(base_dir, "od")
    output_csv = "test_mesures.csv"

    args = ["measurement2.py", art_dir, vein_dir, od_dir, output_csv, nom_masque]
    
    try:
        m_script.main(args)

    except Exception as e:
        self.lbl_affiche_mesures.setText(f"Erreur : {str(e)}")