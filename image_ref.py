import os
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from skimage import io
import numpy as np

def get_image_coloree(chemin: str, color: str = None) -> np.ndarray | None:
    """Charge et colorie un masque, retourne un tableau numpy RGBA."""
    if not chemin or not os.path.exists(chemin):
        return None

    img = io.imread(chemin)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    elif img.ndim == 4:
        img = img[:, :, :3]

    couleur = None
    if color == "RED":
        couleur = np.array([255, 0, 0], dtype=np.uint8)
    elif color == "GREEN":
        couleur = np.array([0, 255, 0], dtype=np.uint8)
    elif color == "BLUE":
        couleur = np.array([0, 0, 255], dtype=np.uint8)

    if couleur is not None:
        gray = img.mean(axis=2)
        masque = gray > 120
        seg = img.copy()
        alpha = 0.45
        seg[masque] = np.clip(
            (1 - alpha) * seg[masque] + alpha * couleur, 0, 255
        ).astype(np.uint8)
        img = seg

    return img.copy()  # .copy() pour garantir la continuité mémoire


def composer_et_afficher(label, chemin_base: str, couches: list):
    """
    Compose l'image de base + toutes les couches en une seule passe.
    couches = [{"chemin": ..., "color": "RED"}, ...]
    Retourne le numpy array de l'image composée.
    """
    if not chemin_base or not os.path.exists(chemin_base):
        label.setText(f"Erreur : image introuvable\n{chemin_base}")
        label.setStyleSheet("color: red;")
        print(f"Erreur: chemin introuvable {chemin_base}")
        return None

    # 1. Image de base
    base = io.imread(chemin_base)
    if base.ndim == 2:
        base = np.stack([base, base, base], axis=-1)
    elif base.ndim == 4:
        base = base[:, :, :3]
    resultat = base.copy().astype(np.float32)

    # 2. Superposer chaque couche active
    for couche in couches:
        img_couche = get_image_coloree(couche["chemin"], couche["color"])
        if img_couche is None:
            print(f"Avertissement: couche introuvable {couche['chemin']}")
            continue

        # Redimensionner si nécessaire
        if img_couche.shape != base.shape:
            from skimage.transform import resize
            img_couche = (resize(img_couche, base.shape) * 255).astype(np.uint8)

        gray = img_couche.mean(axis=2)
        masque = gray > 120
        couleurs = {"RED": [255,0,0], "GREEN": [0,255,0], "BLUE": [0,0,255]}
        couleur = np.array(couleurs.get(couche["color"], [255,255,255]), dtype=np.float32)
        alpha = 0.45
        resultat[masque] = np.clip(
            (1 - alpha) * resultat[masque] + alpha * couleur, 0, 255
        )

    # 3. Afficher en une seule fois
    final = resultat.astype(np.uint8)
    final = np.ascontiguousarray(final)
    h, w, _ = final.shape
    qimg = QImage(final.data, w, h, 3 * w, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(qimg)

    if pixmap.isNull():
        label.setText("Erreur : impossible de composer l'image")
        label.setStyleSheet("color: red;")
        print("Erreur: pixmap est null")
        return None

    scaled = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    label.setPixmap(scaled)
    label.setText("")
    
    print(f"Succès: image composée retournée ({h}x{w})")
    return final


def charger_image_dans_label(label, chemin, color=None):
    """Fonction originale conservée pour compatibilité."""
    composer_et_afficher(label, chemin, [])