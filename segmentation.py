from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QGroupBox,
    QCheckBox, QPushButton, QHBoxLayout, QScrollArea, QFrame)
from PySide6.QtCore import Qt



class SegmentationToolbox(QDockWidget):
    """Panneau lateral pour afficher/masquer les couches de segmentation."""

    TOOLBOX_STYLE = """
    QDockWidget::title {
        background: #2e4a3a;
        color: #ffffff;
        padding: 6px 10px;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    QGroupBox {
        font-weight: bold;
        font-size: 11px;
        color: #2e4a3a;
        border: 1px solid #b0d0b8;
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 6px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
        color: #2e8a5a;
    }
    QCheckBox {
        font-size: 12px;
        color: #222233;
        padding: 3px 2px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 15px;
        height: 15px;
        border: 1.5px solid #6a9a7a;
        border-radius: 3px;
        background: #ffffff;
    }
    QCheckBox::indicator:checked {
        background: #2e8a5a;
        border-color: #1a6a3a;
    }
    QCheckBox:disabled {
        color: #aaaaaa;
    }
    QCheckBox::indicator:disabled {
        border-color: #cccccc;
        background: #eeeeee;
    }
    QPushButton {
        background: #2e8a5a;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 0;
        font-size: 13px;
        font-weight: bold;
        margin-top: 6px;
    }
    QPushButton:hover    { background: #1a6a3a; }
    QPushButton:disabled { background: #aaccbb; color: #eeeeee; }
    
    """

    def __init__(self, parent=None):
        super().__init__("  SEGMENTATION", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        self.setMinimumWidth(210)
        self.setStyleSheet(self.TOOLBOX_STYLE)

        root = QWidget()
        root.setStyleSheet("background: #f4fbf6;")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(root)
        self.setWidget(scroll)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ── Groupe Couches ──
        self.cb_veines  = QCheckBox("Veines")
        self.cb_veines.clicked.connect(self.appliquer)

        self.cb_arteres = QCheckBox("Arteres")
        self.cb_arteres.clicked.connect(self.appliquer)

        self.cb_disque  = QCheckBox("Disque optique")
        self.cb_disque.clicked.connect(self.appliquer)

        couches_cbs = [self.cb_veines, self.cb_arteres, self.cb_disque]


        layout.addWidget(self._groupe(
            "Disponibles", couches_cbs))
        
        layout.addStretch()

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _groupe(self, titre: str, checkboxes: list):
        box = QGroupBox(titre)
        vbox = QVBoxLayout(box)
        vbox.setSpacing(2)
        for cb in checkboxes:
            vbox.addWidget(cb)
        return box


    def selections(self) -> dict:
        """Retourne l'etat de chaque couche."""
        return {
            "veines":  self.cb_veines.isChecked(),
            "arteres": self.cb_arteres.isChecked(),
            "disque":  self.cb_disque.isChecked(),
        }

    def appliquer(self):
        """
        Emet les selections vers la fenetre principale.
        Connecte le signal 'applique' dans MyWindow, ou surcharge cette methode.
        """
        sel = self.selections()
        # Remonte les selections au parent (MyWindow)
        parent = self.parent()
        if parent and hasattr(parent, "on_segmentation_appliquee"):
            parent.on_segmentation_appliquee(sel)
            
    
   