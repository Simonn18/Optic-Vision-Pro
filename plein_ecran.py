import os
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

class PleinEcranWindow(QDialog):
    def __init__(self, parent=None, chemin: str = "", image_composite: np.ndarray = None):
        super().__init__(parent)
        self.setWindowTitle("Plein ecran")

        # ✅ Assigner les attributs AVANT showMaximized()
        self.chemin = chemin
        self.image_composite = image_composite

        self.showMaximized()  # ← déplacé APRÈS les assignations

        layout = QVBoxLayout(self)
        self.lbl = QLabel()
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.lbl)

        self._afficher_image()

    def _afficher_image(self):
        # ✅ Garde-fou si appelé trop tôt
        if not hasattr(self, "image_composite") or not hasattr(self, "lbl"):
            return

        ecran = QApplication.primaryScreen().availableGeometry()
        largeur = ecran.width()
        hauteur = ecran.height()

        try:
            pixmap = None
            
            if self.image_composite is not None and isinstance(self.image_composite, np.ndarray):
                # Afficher l'image composée (priorité)
                h, w = self.image_composite.shape[:2]
                
                # Vérifier le nombre de canaux
                if len(self.image_composite.shape) == 3:
                    channels = self.image_composite.shape[2]
                else:
                    # Image en niveaux de gris - la convertir en RGB
                    img_gray = self.image_composite
                    self.image_composite = np.stack([img_gray, img_gray, img_gray], axis=-1)
                    channels = 3
                
                # Copier l'image pour éviter les problèmes de pointeurs
                img = np.ascontiguousarray(self.image_composite)
                
                if channels == 3:
                    # Créer QImage et le copier pour éviter les problèmes mémoire
                    qimg = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888).copy()
                else:
                    qimg = QImage(img.data, w, h, 4 * w, QImage.Format_RGBA8888).copy()
                
                pixmap = QPixmap.fromImage(qimg)
                
                if pixmap.isNull():
                    print("Erreur : pixmap est null pour image_composite")
                    raise Exception("Impossible de créer le pixmap de l'image composée")
                    
            elif self.chemin and os.path.exists(self.chemin):
                # Sinon afficher l'image du chemin
                pixmap = QPixmap(self.chemin)
            else:
                self.lbl.setText("Aucune image disponible\n(Appliquez les segmentations d'abord)")
                return

            if pixmap and not pixmap.isNull():
                self.lbl.setPixmap(
                    pixmap.scaled(largeur, hauteur, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.lbl.setText("Erreur : impossible d'afficher l'image")
                
        except Exception as e:
            print(f"Erreur affichage plein écran : {str(e)}")
            self.lbl.setText(f"Erreur affichage : {str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._afficher_image()