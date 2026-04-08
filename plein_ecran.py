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

        btn = QPushButton("Fermer")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)

        self._afficher_image()

    def _afficher_image(self):
        # ✅ Garde-fou si appelé trop tôt
        if not hasattr(self, "image_composite") or not hasattr(self, "lbl"):
            return

        ecran = QApplication.primaryScreen().availableGeometry()
        largeur = ecran.width()
        hauteur = ecran.height()

        if self.image_composite is not None:
            h, w, _ = self.image_composite.shape
            img = np.ascontiguousarray(self.image_composite)
            qimg = QImage(img.data, w, h, 3 * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
        elif self.chemin and os.path.exists(self.chemin):
            pixmap = QPixmap(self.chemin)
        else:
            self.lbl.setText("Aucune image")
            return

        self.lbl.setPixmap(
            pixmap.scaled(largeur, hauteur, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._afficher_image()