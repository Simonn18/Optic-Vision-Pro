import os
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
            # Remplace l'extension réelle (.jpg, .jpeg, .png…) par celle du masque,
            # quelle que soit l'extension de l'image source.
            ch = os.path.splitext(ch)[0] + ext
        return ch

    couches = []
    if sel.get("veines", {}).get("visible"):
        self.chemin_veines = construire_chemin("veins")
        opacity = sel["veines"]["opacity"] / 100
        couches.append({"chemin": self.chemin_veines, "color": "BLUE", "opacity": opacity})

    if sel.get("arteres", {}).get("visible"):
        self.chemin_arteres = construire_chemin("arteries")
        opacity = sel["arteres"]["opacity"] / 100
        couches.append({"chemin": self.chemin_arteres, "color": "RED", "opacity": opacity})

    if sel.get("disque", {}).get("visible"):
        self.chemin_disque = construire_chemin("od")
        opacity = sel["disque"]["opacity"] / 100
        couches.append({"chemin": self.chemin_disque, "color": "GREEN", "opacity": opacity})

    # ✅ return du résultat de composer_et_afficher
    return ir.composer_et_afficher(self.lbl_import, self.chemin_image, couches)