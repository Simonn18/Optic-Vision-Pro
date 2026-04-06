import image_ref as ir

def affiche_seg(self, type, chemin=None):
        if self.chemin_image is None:
            return
        
        if chemin is not None:
            self.chemin_image = chemin

        if type == "veines":
                self.chemin_veines = self.chemin_image
                if "fundus_images" in self.chemin_veines:
                    # Remplace uniquement la dernière occurrence
                    self.chemin_veines = self.chemin_veines.rsplit("fundus_images", 1)
                    self.chemin_veines = "segmentation_masks/veins".join(self.chemin_veines)
                self.chemin_veines = self.chemin_veines.replace(".jpg", ".png")
                ir.charger_image_dans_label(self.lbl_import, self.chemin_veines, color="BLUE")

        elif type == "arteres":
            self.chemin_arteres = self.chemin_image
            if "fundus_images" in self.chemin_arteres:
                self.chemin_arteres = self.chemin_arteres.rsplit("fundus_images", 1)
                self.chemin_arteres = "segmentation_masks/arteries".join(self.chemin_arteres)
            self.chemin_arteres = self.chemin_arteres.replace(".jpg", ".png")
            ir.charger_image_dans_label(self.lbl_import, self.chemin_arteres, color="RED")
       
        elif type == "disque":
            self.chemin_disque = self.chemin_image
            if "fundus_images" in self.chemin_disque:
                self.chemin_disque = self.chemin_disque.rsplit("fundus_images", 1)
                self.chemin_disque = "segmentation_masks/od".join(self.chemin_disque)
            self.chemin_disque = self.chemin_disque.replace(".jpg", ".png")
            ir.charger_image_dans_label(self.lbl_import, self.chemin_disque, color="GREEN")
            self.statusBar().showMessage("Vérifiez le disque optique et valider sa position (configuration/valider le disque optique)")
                