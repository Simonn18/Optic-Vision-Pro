from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QGroupBox,
    QCheckBox, QPushButton, QHBoxLayout, QScrollArea, QFrame, QSlider, QLabel, QMessageBox)
from PySide6.QtCore import Qt

BLUE  = "#2a6496"
RED   = "#e74c3c"
GREEN = "#27ae60"
ORANGE = "#e67e22"

class SegmentationToolbox(QDockWidget):
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
        border: 1.5px solid #222233;
        border-radius: 3px;
        background: #ffffff;
    }
    QCheckBox::indicator:checked {
        background: #2e8a5a;
        border-color: #222233;
    }
    QCheckBox:disabled {
        color: #aaaaaa;
    }
    QCheckBox::indicator:disabled {
        border-color: #cccccc;
        background: #eeeeee;
    }
     QPushButton{
        background: #222233;
        border-radius: 6px;
        padding: 8px 0;
        font-size: 13px;
        font-weight: bold;
        margin-top: 6px;
    }
    QPushButton { background: #222233; }
    QPushButton:disabled { background: #bbbbcc; }
    QPushButton {
        background: #222233;
        color: #000000;
        border: 1px solid #c0c0d8;
        border-radius: 4px;
        padding: 3px 10px;
        font-size: 11px;   
        }   
    """

    def __init__(self, parent=None):
        super().__init__("  SEGMENTATION", parent)
        
        self.setMinimumWidth(250)
        self.setStyleSheet(self.TOOLBOX_STYLE)

        # Widget principal et Layout
        root = QWidget()
        root.setStyleSheet("background: #f4fbf6; color: #000000;")
        self.main_layout = QVBoxLayout(root)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(root)
        self.setWidget(scroll)

        # 1. Section Couches (Checkboxes)
        self.cb_veines  = QCheckBox("Veines")
        self.cb_arteres = QCheckBox("Artères")
        self.cb_disque  = QCheckBox("Disque optique")
        self.cb_veines.setChecked(True)
        self.cb_arteres.setChecked(True)
        self.cb_disque.setChecked(True)
        self.editer_disque = QPushButton("Editer le disque")
        self.valide_disque_optique = QPushButton("Valider le disque")
        self.lancer_mesures = QPushButton("Lancer les mesures")
        self.lancer_mesures.setEnabled(False)

        
        self.main_layout.addWidget(self._groupe("Couches Disponibles", 
                                  [self.cb_veines, self.cb_arteres, self.cb_disque,self.editer_disque,self.valide_disque_optique]))
        
        self.main_layout.addWidget(self.lancer_mesures)

        # 2. Section Opacité (Sliders)
        self.sliders = {}
        self.labels = {}
        self.groups = {}

        # Création des sliders de contrôle
        self._setup_slider_group("image", "Opacité Image", ORANGE)
        self._setup_slider_group("veines", "Opacité Veines", BLUE)
        self._setup_slider_group("arteres", "Opacité Artères", RED)
        self._setup_slider_group("disque", "Opacité Disque", GREEN)

        # Connexions
        self.cb_veines.toggled.connect(self.update_ui)
        self.cb_arteres.toggled.connect(self.update_ui)
        self.cb_disque.toggled.connect(self.update_ui)
        
        self.editer_disque.clicked.connect(self.on_editer_disque_optique)
        self.valide_disque_optique.clicked.connect(self.valider_disque_clicked)
        self.lancer_mesures.clicked.connect(self.on_lancer_mesures)

        self.main_layout.addStretch()
        self.update_ui() # Initialisation de la visibilité

    def _setup_slider_group(self, key, label_text, color):
        """Crée un slider, son label et son groupe parent."""
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        self.forme_slider(slider, color=color)
        
        val_label = QLabel("50")
        val_label.setStyleSheet("color: #000000;")  # Noir avec gras
        slider.valueChanged.connect(lambda v: val_label.setText(f"{v}"))
        slider.valueChanged.connect(self.appliquer)

        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(5, 5, 5, 5)
        lay.addWidget(slider)
        lay.addWidget(val_label, alignment=Qt.AlignCenter)

        group = self._groupe(label_text, [container])
        
        # Cacher par défaut, sauf l'image qui est toujours visible
        if key != "image":
            group.setVisible(False)
        
        self.main_layout.addWidget(group)
        
        self.sliders[key] = slider
        self.groups[key] = group

    def _groupe(self, titre: str, checkboxes: list,
                extra_buttons: list = None) -> QGroupBox:
        box = QGroupBox(titre)
        vbox = QVBoxLayout(box)
        vbox.setSpacing(2)
        for cb in checkboxes:
            vbox.addWidget(cb)
        if extra_buttons:
            row = QHBoxLayout()
            row.setContentsMargins(0, 4, 0, 0)
            for btn in extra_buttons:
                row.addWidget(btn)
            vbox.addLayout(row)
        return box

    def forme_slider(self, slider, color=ORANGE, back_color="#d0d0d0"):
        handle_size = 13
        margin = -(handle_size - 8) // 2
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ border: 1px solid #bbb; height: 8px; background: {back_color} }}
            QSlider::handle:horizontal {{ background: {color}; border: 1px solid #5c5c5c; width: {handle_size}px; 
                                        height: {handle_size}px; margin: {margin} 0px; border-radius: {handle_size//2}px; }}
            QSlider::sub-page:horizontal {{ background: {color}; border-radius: 4px; }}
        """)
    
    def update_ui(self):
        """Gère la visibilité des groupes de sliders selon les cases cochées."""
        self.groups["veines"].setVisible(self.cb_veines.isChecked())
        self.groups["arteres"].setVisible(self.cb_arteres.isChecked())
        self.groups["disque"].setVisible(self.cb_disque.isChecked())
        self.appliquer()
    
    def appliquer(self):
        """Récupère les données et prévient le parent."""
        data = {
            "veines": {"visible": self.cb_veines.isChecked(), "opacity": self.sliders["veines"].value()},
            "arteres": {"visible": self.cb_arteres.isChecked(), "opacity": self.sliders["arteres"].value()},
            "disque": {"visible": self.cb_disque.isChecked(), "opacity": self.sliders["disque"].value()},
            "image_opacity": self.sliders["image"].value()
        }
        
        parent = self.parent()
        if parent and hasattr(parent, "on_segmentation_appliquee"):
            parent.on_segmentation_appliquee(data)
                 
            
    def on_editer_disque_optique(self):
        parent = self.parent()
        if parent and hasattr(parent, "edit_disque_optique"):
            parent.edit_disque_optique()
        else:
            print("Erreur : le parent ne peut pas modifer le disque")
    
    def valider_disque_clicked(self):

        rep = QMessageBox.question(self, "Validation", 
            "Confirmez-vous le placement du Disque Optique ?")
        if rep == QMessageBox.Yes:            
            self.lancer_mesures.setEnabled(True) 
            
    def on_lancer_mesures(self):
        parent = self.parent()
        if parent and hasattr(parent, "mesure"):
            parent.mesure()
        else:
            print("Erreur lors de lancement de mesures dans le main")

    


