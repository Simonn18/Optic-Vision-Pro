import os
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from skimage import io
import numpy as np


def charger_image_dans_label(label, chemin, color=None):
    """Charge une image dans QLabel et applique une segmentation colorée si demandé."""
    if not chemin:
        label.setText("Erreur : chemin vide")
        label.setStyleSheet("color: red;")
        return

    if not os.path.exists(chemin):
        label.setText(f"Erreur : image introuvable\n{chemin}")
        label.setStyleSheet("color: red;")
        return

    # Charge l'image pour segmentation
    img = io.imread(chemin)
    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)
    elif img.ndim == 4:
        img = img[:, :, :3]

    # Segmentation simple : on veut colorier les zones sombres/structures.
    # On calcule un masque par seuil sur l'intensité moyenne.
    gray = img.mean(axis=2)
    masque = gray > 120

    couleur = None
    if color == "RED":
        couleur = np.array([255, 0, 0], dtype=np.uint8)
    elif color == "GREEN":
        couleur = np.array([0, 255, 0], dtype=np.uint8)
    elif color == "BLUE":
        couleur = np.array([0, 0, 255], dtype=np.uint8)

    if couleur is not None:
        seg = img.copy()
        alpha = 0.45
        seg[masque] = np.clip((1 - alpha) * seg[masque] + alpha * couleur, 0, 255).astype(np.uint8)
        img = seg

    h, w, _ = img.shape
    qimg = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(qimg)
    if pixmap.isNull():
        label.setText(f"Erreur : impossible de charger l'image\n{chemin}")
        label.setStyleSheet("color: red;")
        return

    scaled = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    label.setPixmap(scaled)
    label.setText("")

    return img

