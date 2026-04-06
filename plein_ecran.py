import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class PleinEcranWindow(QDialog):
    def __init__(self, parent=None, chemin: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Plein ecran")
        self.showMaximized()
        layout = QVBoxLayout(self)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        if chemin and os.path.exists(chemin):
            lbl.setPixmap(
                QPixmap(chemin).scaled(1200, 900, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            lbl.setText("Aucune image")
        layout.addWidget(lbl)
        btn = QPushButton("Fermer")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)