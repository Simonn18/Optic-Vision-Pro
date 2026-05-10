from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QGroupBox,
    QCheckBox, QPushButton, QHBoxLayout, QScrollArea,
    QSlider, QLabel, QMessageBox, QColorDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


BLUE   = "#2a6496"
RED    = "#e74c3c"
GREEN  = "#27ae60"
ORANGE = "#e67e22"

# Config des dialogues couleur : clé → (titre, couleur par défaut Qt)
COLOR_CONFIG = {
    "veines":  ("Choisir la couleur des veines",         Qt.blue),
    "arteres": ("Choisir la couleur des artères",        Qt.red),
    "disque":  ("Choisir la couleur du disque optique",  Qt.green),
}

MSG_STYLE = """
    QMessageBox {
        background-color: #1e1e2e;
        border: 1px solid #3a3a5a;
        border-radius: 10px;
        color: #ffffff;
    }
    QMessageBox QLabel {
        color: #e0e0f0;
        font-size: 13px;
        padding: 6px;
        background: transparent;
    }
    QMessageBox QPushButton {
        background-color: #2e2e4e;
        color: #c8c8ff;
        border: 1px solid #5555aa;
        border-radius: 6px;
        padding: 6px 18px;
        font-size: 12px;
        font-weight: bold;
        min-width: 80px;
    }
    QMessageBox QPushButton:hover {
        background-color: #3e3e6e;
        color: #ffffff;
        border-color: #8888cc;
    }
    QMessageBox QPushButton:pressed {
        background-color: #5555aa;
    }
"""


class StyledMessageBox(QMessageBox):
    """QMessageBox avec style personnalisé appliqué automatiquement."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(MSG_STYLE)

    @staticmethod
    def information(parent, titre, texte, buttons=QMessageBox.Ok):
        mb = StyledMessageBox(parent)
        mb.setWindowTitle(titre)
        mb.setText(texte)
        mb.setStandardButtons(buttons)
        mb.setIcon(QMessageBox.Information)
        return mb.exec()

    @staticmethod
    def warning(parent, titre, texte, buttons=QMessageBox.Ok):
        mb = StyledMessageBox(parent)
        mb.setWindowTitle(titre)
        mb.setText(texte)
        mb.setStandardButtons(buttons)
        mb.setIcon(QMessageBox.Warning)
        return mb.exec()

    @staticmethod
    def critical(parent, titre, texte, buttons=QMessageBox.Ok):
        mb = StyledMessageBox(parent)
        mb.setWindowTitle(titre)
        mb.setText(texte)
        mb.setStandardButtons(buttons)
        mb.setIcon(QMessageBox.Critical)
        return mb.exec()



class SegmentationToolbox(QDockWidget):

    TOOLBOX_STYLE = """
    QDockWidget {
        background: #f4fbf6;
    }
    QScrollArea {
        background: #f4fbf6;
        border: none;
    }
    QScrollArea > QWidget > QWidget {
        background: #f4fbf6;
    }
    QSlider {
        background: #f4fbf6;
    }
    QLabel {
        background: #f4fbf6;
        color: #000000;
    }
    QDockWidget::title {
        background: #2e4a3a;
        color: #ffffff;
        padding: 6px 10px;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    QGroupBox {
        background: #f4fbf6;
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
        background: #f4fbf6;
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
    QCheckBox:disabled           { color: #aaaaaa; }
    QCheckBox::indicator:disabled { border-color: #cccccc; background: #eeeeee; }

    QPushButton {
        background: #f4fbf6;
        border: 1px solid #c0c0d8;
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 11px;
        font-weight: bold;
        color: #aaaacc;        /* couleur par défaut (grisée) */
        margin-top: 4px;
    }
    QPushButton:disabled { background: #bbbbcc; color: #888899; }

    /* Couleurs individuelles par objectName */
    QPushButton#btn_editer         { color: #000000; }
    QPushButton#btn_editer:disabled { background: #bbbbcc; color: #888899; }

    QPushButton#btn_valider        { color: #000000;
}
    QPushButton#btn_valider:disabled { background: #bbbbcc; color: #888899; }
    QPushButton#btn_lancer         { color: #000000;  background: #ffffff; }
    QPushButton#btn_lancer:disabled { background: #bbbbcc; color: #888899; }
    QPushButton#btn_couleur_veines  { color: #2a6496; }
    QPushButton#btn_couleur_arteres { color: #e74c3c; }
    QPushButton#btn_couleur_disque  { color: #27ae60; }
    """

    SLIDER_COLORS = {
        "image":   ORANGE,
        "veines":  BLUE,
        "arteres": RED,
        "disque":  GREEN,
    }

    def __init__(self, parent=None):
        super().__init__("  SEGMENTATION", parent)
        self.setMinimumWidth(250)
        self.setStyleSheet(self.TOOLBOX_STYLE)

        self.current_colors = {
            "veines":  BLUE,
            "arteres": RED,
            "disque":  GREEN
        }
        self.sliders = {}
        self.groups  = {}

        self._build_widgets()
        self._build_layout()
        self._connect_signals()
        self.update_ui()

    # ------------------------------------------------------------------ #
    #  Construction                                                         #
    # ------------------------------------------------------------------ #
    
    @staticmethod
    def _styled_msgbox(parent, titre: str, texte: str, info: str = "") -> StyledMessageBox:
        """Crée une QMessageBox stylisée réutilisable."""
        mb = StyledMessageBox(parent)
        mb.setWindowTitle(titre)
        mb.setText(texte)
        if info:
            mb.setInformativeText(info)
        return mb

    def _build_widgets(self):
        """Instancie tous les widgets et assigne leurs objectName."""
        # Checkboxes
        self.cb_veines  = QCheckBox("Veines")
        self.cb_arteres = QCheckBox("Artères")
        self.cb_disque  = QCheckBox("Disque optique")

        # Boutons d'action
        self.btn_editer  = QPushButton("Éditer le disque")
        self.btn_valider = QPushButton("Valider le disque")
        self.btn_lancer  = QPushButton("Lancer les mesures")
        self.btn_lancer.setEnabled(False)

        self.btn_editer.setObjectName("btn_editer")
        self.btn_editer.setEnabled(False)
        self.btn_editer.setCheckable(True)
        self.btn_valider.setObjectName("btn_valider")
        self.btn_lancer.setObjectName("btn_lancer")
        self.btn_valider.setEnabled(False)

        # Boutons couleur
        self.btn_couleur_veines  = QPushButton("Couleur des veines")
        self.btn_couleur_arteres = QPushButton("Couleur des artères")
        self.btn_couleur_disque  = QPushButton("Couleur du disque optique")

        self.btn_couleur_veines.setObjectName("btn_couleur_veines")
        self.btn_couleur_arteres.setObjectName("btn_couleur_arteres")
        self.btn_couleur_disque.setObjectName("btn_couleur_disque")

        

    def _build_layout(self):
        """Assemble le layout principal."""
        root = QWidget()
        root.setObjectName("toolbox_root")
        self.main_layout = QVBoxLayout(root)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(root)
        self.setWidget(scroll)

        # Groupe couches
        self.main_layout.addWidget(self._groupe("Couches disponibles", [
            self.cb_veines, self.cb_arteres, self.cb_disque,
            self.btn_editer, self.btn_valider,
        ]))

        # Groupe couleurs
        self.main_layout.addWidget(self._groupe("Modifier les couleurs", [
            self.btn_couleur_veines,
            self.btn_couleur_arteres,
            self.btn_couleur_disque,
        ]))

        # Bouton principal
        self.main_layout.addWidget(self.btn_lancer)

        # Sliders d'opacité
        for key, label in [
            ("image",   "Opacité image"),
            ("veines",  "Opacité veines"),
            ("arteres", "Opacité artères"),
            ("disque",  "Opacité disque"),
        ]:
            self._setup_slider_group(key, label, self.SLIDER_COLORS[key])

        self.main_layout.addStretch()

    def _connect_signals(self):
        """Toutes les connexions signal/slot au même endroit."""
        self.cb_veines.toggled.connect(self.update_ui)
        self.cb_arteres.toggled.connect(self.update_ui)
        self.cb_disque.toggled.connect(self.update_ui)

        self.btn_editer.clicked.connect(self._on_editer_disque)
        self.btn_valider.clicked.connect(self._on_valider_disque)
        self.btn_lancer.clicked.connect(self._on_lancer_mesures)

        self.btn_couleur_veines.clicked.connect(lambda: self.modifier_couleurs("veines"))
        self.btn_couleur_arteres.clicked.connect(lambda: self.modifier_couleurs("arteres"))
        self.btn_couleur_disque.clicked.connect(lambda: self.modifier_couleurs("disque"))

    # ------------------------------------------------------------------ #
    #  Helpers UI                                                           #
    # ------------------------------------------------------------------ #

    def _setup_slider_group(self, key: str, label_text: str, color: str):
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        self._style_slider(slider, color)

        val_label = QLabel("50")
        val_label.setStyleSheet("color: #000000; background: #f4fbf6;")
        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))
        slider.valueChanged.connect(self.appliquer)

        container = QWidget()
        container.setStyleSheet("background: #f4fbf6;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(5, 5, 5, 5)
        lay.addWidget(slider)
        lay.addWidget(val_label, alignment=Qt.AlignCenter)

        group = self._groupe(label_text, [container])
        if key != "image":
            group.setVisible(False)

        self.main_layout.addWidget(group)
        self.sliders[key] = slider
        self.groups[key]  = group

    @staticmethod
    def _groupe(titre: str, widgets: list) -> QGroupBox:
        box = QGroupBox(titre)
        vbox = QVBoxLayout(box)
        vbox.setSpacing(2)
        for w in widgets:
            vbox.addWidget(w)
        return box

    @staticmethod
    def _style_slider(slider: QSlider, color: str = "#f4fbf6", back_color = "#f4fbf6"):
        h = 13
        m = -(h - 8) // 2
        slider.setStyleSheet(f"""
            QSlider {{ background: {back_color}; }}
            QSlider::groove:horizontal   {{ border: 1px solid #bbb; height: 8px;  }}
            QSlider::handle:horizontal   {{ background: {color}; border: 1px solid #5c5c5c;
                                            width: {h}px; height: {h}px;
                                            margin: {m}px 0; border-radius: {h//2}px; }}
            QSlider::sub-page:horizontal {{ background: {color}; border-radius: 4px; }}
        """)

    # ------------------------------------------------------------------ #
    #  Logique                                                              #
    # ------------------------------------------------------------------ #

    def update_ui(self):
        veines  = self.cb_veines.isChecked()
        arteres = self.cb_arteres.isChecked()
        disque  = self.cb_disque.isChecked()

        self.groups["veines"].setVisible(veines)
        self.groups["arteres"].setVisible(arteres)
        self.groups["disque"].setVisible(disque)

        self.btn_couleur_veines.setEnabled(veines)
        self.btn_couleur_arteres.setEnabled(arteres)
        self.btn_couleur_disque.setEnabled(disque)
        self.btn_editer.setEnabled(disque)
        self.btn_valider.setEnabled(disque)

        self.appliquer()

    def activate_all_segmentations(self):
        """Active automatiquement toutes les segmentations (veines, artères, disque)."""
        self.cb_veines.setChecked(True)
        self.cb_arteres.setChecked(True)
        self.cb_disque.setChecked(True)
        self.update_ui()
        self.appliquer()
    
    def appliquer(self):
        data = {
            "veines":        {"visible": self.cb_veines.isChecked(),  "opacity": self.sliders["veines"].value()},
            "arteres":       {"visible": self.cb_arteres.isChecked(), "opacity": self.sliders["arteres"].value()},
            "disque":        {"visible": self.cb_disque.isChecked(),  "opacity": self.sliders["disque"].value()},
            "image_opacity": self.sliders["image"].value(),
        }
        parent = self.parent()
        if parent and hasattr(parent, "on_segmentation_appliquee"):
            parent.on_segmentation_appliquee(data)

    def modifier_couleurs(self, key: str):
        """Ouvre un QColorDialog pour la couche `key`."""
        titre, default_qt_color = COLOR_CONFIG[key]
        choix = QColorDialog.getColor(QColor(default_qt_color), self, titre)
        
        if not choix.isValid():
            return

        couleur_hex = choix.name(QColor.NameFormat.HexRgb) # Utilisez HexRgb pour le CSS
        
        # --- AJOUTEZ CETTE LIGNE POUR LA SAUVEGARDE ---
        self.current_colors[key] = couleur_hex 
        # ----------------------------------------------

        # Mise à jour visuelle du bouton dans la toolbox
        bouton = getattr(self, f"btn_couleur_{key}")
        bouton.setStyleSheet(f"color: {couleur_hex}; font-weight: bold;")
        
        slider = self.sliders.get(key)
        if slider:
            self._style_slider(slider, couleur_hex)

        # Notification du parent (Main) pour redessiner les masques
        color_modif = self.hex_to_rgb(couleur_hex)
        parent = self.parent()
        if parent and hasattr(parent, "modif_couleurs"):
            parent.modif_couleurs(key, color_modif)

    
    def _on_editer_disque(self):
        parent = self.parent()
        state = self.btn_editer.isChecked()
        if parent and hasattr(parent, "edit_disque_optique"):
            parent.edit_disque_optique(state)
        else:
            print("Erreur : le parent ne peut pas modifier le disque")

    def _on_valider_disque(self):
        rep = StyledMessageBox(self)
        rep.setWindowTitle("Valider le disque optique")
        rep.setText("Validation du disque optique")
        rep.setInformativeText("Êtes-vous sûr de vouloir valider le disque optique ?")
        btn_oui= rep.addButton("Oui", QMessageBox.ActionRole)
        btn_non = rep.addButton("Non", QMessageBox.ActionRole)
        rep.exec()
        if rep.clickedButton() == btn_oui:
            self.btn_lancer.setEnabled(True)
        if rep.clickedButton() == btn_non:
            return

    def _on_lancer_mesures(self):
        parent = self.parent()
        if parent and hasattr(parent, "mesure"):
            parent.mesure()
        else:
            print("Erreur lors du lancement des mesures dans le main")
    
    def hex_to_rgb(self,value):
        value = value.lstrip('#')
        lv = len(value)
        rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return rgb

    def recup_config(self) -> dict:
        """Retourne les couleurs et opacités actuelles (pour sauvegarde par image)."""
        return {
            "couleurs": {
                "veines":  self._hex_to_rgba(self.current_colors.get("veines",  "#2a6496")),
                "arteres": self._hex_to_rgba(self.current_colors.get("arteres", "#e74c3c")),
                "disque":  self._hex_to_rgba(self.current_colors.get("disque",  "#27ae60")),
            },
            "opacites": {
                "image":   self.sliders["image"].value(),
                "veines":  self.sliders["veines"].value(),
                "arteres": self.sliders["arteres"].value(),
                "disque":  self.sliders["disque"].value(),
            },
            "visibilites": {
                "veines":  self.cb_veines.isChecked(),
                "arteres": self.cb_arteres.isChecked(),
                "disque":  self.cb_disque.isChecked(),
            },
            "current_colors": dict(self.current_colors),
        }

    def restaurer_config(self, config: dict):
        """Restaure les couleurs et opacités depuis une config sauvegardée."""
        # Opacités
        for key, val in config.get("opacites", {}).items():
            if key in self.sliders:
                self.sliders[key].blockSignals(True)
                self.sliders[key].setValue(val)
                self.sliders[key].blockSignals(False)

        # Visibilités
        for cb, key in [(self.cb_veines, "veines"), (self.cb_arteres, "arteres"), (self.cb_disque, "disque")]:
            if key in config.get("visibilites", {}):
                cb.blockSignals(True)
                cb.setChecked(config["visibilites"][key])
                cb.blockSignals(False)

        # Couleurs boutons et sliders
        for key, hex_color in config.get("current_colors", {}).items():
            self.current_colors[key] = hex_color
            bouton = getattr(self, f"btn_couleur_{key}", None)
            if bouton:
                bouton.setStyleSheet(f"color: {hex_color}; font-weight: bold;")
            slider = self.sliders.get(key)
            if slider:
                self._style_slider(slider, hex_color)

        self.update_ui()

    @staticmethod
    def _hex_to_rgba(hex_color: str) -> tuple:
        """Convertit #rrggbb en (r, g, b, 255)."""
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r, g, b, 255)

    def recup_image(self):
        """Récupère l'état actuel depuis les items du parent (MainWindow)."""
        parent = self.parent()
        
        # Sécurité si le parent n'est pas encore prêt
        if not hasattr(parent, "item_veins") or parent.item_veins is None:
            return {}

        segmentation_state = {
            "layers": {
                "veines": {
                    "opacity": parent.item_veins.opacity(),
                    "visible": parent.item_veins.isVisible(),
                    "color": self.current_colors.get("veines")
                },
                "arteres": {
                    "opacity": parent.item_arteries.opacity(),
                    "visible": parent.item_arteries.isVisible(),
                    "color": self.current_colors.get("arteres")
                },
                "disque_optique": {
                    "opacity": parent.item_od.opacity(),
                    "visible": parent.item_od.isVisible(),
                    "color": self.current_colors.get("disque")
                }
            },
            "fundus": {
                "opacity": parent.item_fundus.opacity()
            }
        }
        return segmentation_state