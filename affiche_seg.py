import image_ref as ir

def affiche_seg(self, sel: dict, chemin=None):
    if self.chemin_image is None:
        return None  # ← return None explicite

    if chemin is not None:
        self.chemin_image = chemin

    def construire_chemin(sous_dossier, ext=".png"):
        ch = self.chemin_image
        if "fundus_images" in ch:
            ch = ch.rsplit("fundus_images", 1)
            ch = f"segmentation_masks/{sous_dossier}".join(ch)
            ch = ch.replace(".jpg", ext)
        return ch

    couches = []
    if sel.get("veines"):
        self.chemin_veines = construire_chemin("veins")
        couches.append({"chemin": self.chemin_veines, "color": "BLUE"})
    if sel.get("arteres"):
        self.chemin_arteres = construire_chemin("arteries")
        couches.append({"chemin": self.chemin_arteres, "color": "RED"})
    if sel.get("disque"):
        self.chemin_disque = construire_chemin("od")
        couches.append({"chemin": self.chemin_disque, "color": "GREEN"})

    # ✅ return du résultat de composer_et_afficher
    return ir.composer_et_afficher(self.lbl_import, self.chemin_image, couches)