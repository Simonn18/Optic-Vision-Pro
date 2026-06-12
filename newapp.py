import sys
import os
import json
import shutil
import copy
import glob 

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QLabel, QFileDialog, QGraphicsScene,
    QGraphicsView, QSizePolicy, QMessageBox, QGraphicsItem, QInputDialog
)

import struct
from PySide6 import QtGui
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon, QPainter, QAction  ,QImage, QColor

import opacite as op
import mesures_box as mb          
import plein_ecran as pe
import segmentation3 as seg
import measurements as m_script
import read_csv as rc
from chargement_images import load_images, images_paths
from affichage_images import conversion_qpixmap
import cv2
from langue import changement_langue, LANGUE_DEFAUT

from PIL import Image, ImageDraw
import numpy as np 


BG    = "#000000"  # Fond app : noir pur
PANEL = "#1e1e1e"  # Panneaux : gris foncé distinct
STRIP = "#141414"  # Barre miniatures : légèrement plus clair que le fond

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
        padding: 6px 14px;
        font-size: 12px;
        font-weight: bold;
        min-width: fit-content;
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
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def showEvent(self, event):
        super().showEvent(event)
        # Forcer la largeur minimum après que Qt a calculé son layout
        self.setFixedWidth(max(self.width(), 480))

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


class ImageStrip(QWidget):
    """Barre de miniatures scrollable avec flèches gauche/droite."""

    image_selectionnee = Signal(str)
    index_change = Signal(int)
    selection_changed = Signal(list)   # émet la liste des chemins sélectionnés

    STRIP_STYLE = """
        QWidget#strip_container { background-color: #141414; }
        QScrollArea { border: none; background: transparent; }
    """

    BTN_FLECHE_STYLE = """
        QPushButton {
            color: #cccccc;
            font-size: 24px;
            font-weight: bold;
            background: #2a2a2a;
            border: none;
            border-radius: 6px;
        }
        QPushButton:hover { background: #3a3a3a; color: white; }
        QPushButton:pressed { background: #444444; }

        QPushButton:disabled { color: #444444; background: #1a1a1a; }
    """

    def __init__(self, parent=None, titre=""):
        super().__init__(parent)
        self.titre = titre
        self.setFixedHeight(120)
        self.setObjectName("strip_container")
        self.setStyleSheet(self.STRIP_STYLE)

        self.chemins = []
        self.boutons = []
        self.index_courant = -1
        self.mode_selection = False          # True = sélection multiple active
        self.indices_selectionnes = set()    # indices des images cochées

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)


        self.btn_gauche = QPushButton("‹")
        self.btn_gauche.setFixedSize(28, 80)
        self.btn_gauche.setStyleSheet(self.BTN_FLECHE_STYLE)
        self.btn_gauche.clicked.connect(self._precedent)
        self.btn_gauche.setEnabled(False)

        self.btn_droite = QPushButton("›")
        self.btn_droite.setFixedSize(28, 80)
        self.btn_droite.setStyleSheet(self.BTN_FLECHE_STYLE)
        self.btn_droite.clicked.connect(self._suivant)
        self.btn_droite.setEnabled(False)

        # Zone scrollable
        self.scroll = QScrollArea()
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.strip_layout = QHBoxLayout(self.container)
        self.strip_layout.setContentsMargins(4, 4, 4, 4)
        self.strip_layout.setSpacing(8)
        self.strip_layout.addStretch()
        self.scroll.setWidget(self.container)

        outer.addWidget(self.btn_gauche)
        outer.addWidget(self.scroll)
        outer.addWidget(self.btn_droite)

    def charger_dossier(self, dossier):
        """Scanne le dossier et affiche les miniatures."""
        
        self.chemins = sorted([
            os.path.join(dossier + "/fundus_images", f)
            for f in os.listdir(dossier + "/fundus_images")
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ])
        self._construire_miniatures(self.chemins)
        self._maj_fleches()

    def charger_images(self, chemins, dossier_masques=None):
        """Charge un ensemble d'images, avec superpositions optionnelle."""
        self.chemins = chemins
        self._construire_miniatures(self.chemins, dossier_masques=dossier_masques)
        self._maj_fleches()

    def _construire_miniatures(self, choix=None, dossier_masques=None):
        # Vider le layout existant
        for btn in self.boutons:
            btn.setParent(None)
        self.boutons.clear()
        self.index_courant = -1
        self.indices_selectionnes.clear()
 
        for i, chemin in enumerate(choix):
            pixmap = QPixmap(chemin).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
 
            # Superposer le masque OD si disponible
            if dossier_masques:
                nom_sans_ext = os.path.splitext(os.path.basename(chemin))[0]
                masque = None
                for ext in (".png", ".jpg", ".jpeg"):
                    candidat = os.path.join(dossier_masques, nom_sans_ext + ext)
                    if os.path.exists(candidat):
                        masque = candidat
                        break
 
                if masque:
                    pixmap = self._superposer_masque(pixmap, masque)
 
            btn = QPushButton()
            btn.setFixedSize(88, 96)
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(pixmap.size())
            btn.setToolTip(os.path.basename(chemin))
            btn.setStyleSheet(self._style_miniature(False, False))

            idx = i
            btn.clicked.connect(lambda _, j=idx: self._on_miniature_cliquee(j))
            self.strip_layout.insertWidget(i, btn)
            self.boutons.append(btn)
 
    @staticmethod
    def _superposer_masque(pixmap_base: QPixmap, chemin_masque: str) -> QPixmap:
        """Superpose le masque OD colorisé en vert sur la miniature."""


        masque_img = QImage(chemin_masque).scaled(
            pixmap_base.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ).convertToFormat(QImage.Format.Format_ARGB32)

        # Remplacer chaque pixel blanc/clair du masque par du vert semi-transparent
        vert = QImage(masque_img.size(), QImage.Format.Format_ARGB32)
        vert.fill(Qt.transparent)
        for y in range(masque_img.height()):
            for x in range(masque_img.width()):
                pixel = masque_img.pixel(x, y)
                r = (pixel >> 16) & 0xFF
                if r > 30:  # pixel actif (non noir)
                    alpha = min(255, int(r * 0.85))
                    vert.setPixel(x, y, QColor(0, 220, 80, alpha).rgba())

        resultat = QPixmap(pixmap_base.size())
        resultat.fill(Qt.transparent)
        painter = QPainter(resultat)
        painter.drawPixmap(0, 0, pixmap_base)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(0, 0, vert)
        painter.end()

        return resultat

    def _on_miniature_cliquee(self, index):
        """Dispatch : coche/décoche en mode sélection, sinon affiche l'image."""
        if self.mode_selection:
            self._toggle_selection(index)
        else:
            self._selectionner(index)

    def activer_mode_selection(self, actif: bool):
        """Active ou désactive le mode sélection multiple.
        À l'activation, toutes les images sont cochées par défaut."""
        self.mode_selection = actif
        if actif:
            self.indices_selectionnes = set()
            for i, btn in enumerate(self.boutons):
                est_courant = (i == self.index_courant)
                btn.setStyleSheet(self._style_miniature(est_courant, False))
        else:
            self.indices_selectionnes.clear()
            for i, btn in enumerate(self.boutons):
                est_courant = (i == self.index_courant)
                btn.setStyleSheet(self._style_miniature(est_courant, False))
        self.selection_changed.emit(self.chemins_selectionnes())

    def _selectionner(self, index):
        # Désélectionner le précédent
        if 0 <= self.index_courant < len(self.boutons):
            est_coche = self.index_courant in self.indices_selectionnes
            self.boutons[self.index_courant].setStyleSheet(self._style_miniature(False, est_coche))

        self.index_courant = index
        est_coche = index in self.indices_selectionnes
        self.boutons[index].setStyleSheet(self._style_miniature(True, est_coche))

        # Scroller pour rendre visible
        self.scroll.ensureWidgetVisible(self.boutons[index])

        self._maj_fleches()
        self.image_selectionnee.emit(self.chemins[index])
        self.index_change.emit(index)

    def _toggle_selection(self, index):
        """Coche/décoche une miniature via clic droit (sélection multiple)."""
        if index in self.indices_selectionnes:
            self.indices_selectionnes.discard(index)
        else:
            self.indices_selectionnes.add(index)

        est_courant = (index == self.index_courant)
        est_coche   = (index in self.indices_selectionnes)
        self.boutons[index].setStyleSheet(self._style_miniature(est_courant, est_coche))
        self.selection_changed.emit(self.chemins_selectionnes())

    def chemins_selectionnes(self):
        """Retourne la liste des chemins des images cochées."""
        return [self.chemins[i] for i in sorted(self.indices_selectionnes)]

    def nb_selectionnes(self):
        return len(self.indices_selectionnes)

    def _precedent(self):
        if self.index_courant > 0:
            self._selectionner(self.index_courant - 1)

    def _suivant(self):
        if self.index_courant < len(self.chemins) - 1:
            self._selectionner(self.index_courant + 1)

    def _maj_fleches(self):
        self.btn_gauche.setEnabled(self.index_courant > 0)
        self.btn_droite.setEnabled(self.index_courant < len(self.chemins) - 1)

    def selectionner_chemin(self, chemin):
        """Sélectionne la miniature correspondant à un chemin donné."""
        if chemin in self.chemins:
            self._selectionner(self.chemins.index(chemin))

    @staticmethod
    def _style_miniature(selected: bool, checked: bool = False) -> str:
        if checked:
            border_color = "#00cc55"   # vert = coché pour export
            bg_color     = "#0d2b1a"
        elif selected:
            border_color = "#ffffff"
            bg_color     = "#2a2a2a"
        else:
            border_color = "transparent"
            bg_color     = "#1e1e1e"
        return f"""
            QPushButton {{
                border: 2px solid {border_color};
                border-radius: 6px;
                background: {bg_color};
                padding: 2px;
            }}
            QPushButton:hover {{
                border: 2px solid #888888;
                background: #252525;
            }}
        """


class ImageStripContainer(QWidget):
    """Conteneur avec deux barres de miniatures."""

    image_selectionnee = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._syncing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre du haut : images fundus (avec aperçu OD superposé)
        self.strip_fundus = ImageStrip(self, titre="Fundus Images")
        self.strip_fundus.image_selectionnee.connect(self._on_fundus_selected)

       

        layout.addWidget(self.strip_fundus)

    def charger_dossier(self, dossier):
        """Charge fundus + les 3 dossiers de masques (arteres, veines, od)."""
        # --- Chemins segmentation définis EN PREMIER (nécessaires pour les miniatures fundus) ---
        base_seg = os.path.join(dossier, "segmentation_masks")
        self.dossier_arteres = os.path.join(base_seg, "arteres")
        self.dossier_veines  = os.path.join(base_seg, "veines")
        self.dossier_od      = os.path.join(base_seg, "od")
 
        # --- Fundus : miniatures avec masque OD superposé en aperçu ---
        dossier_fundus = os.path.join(dossier, "fundus_images")
        try:
            chemins_fundus = sorted([
                os.path.join(dossier_fundus, f)
                for f in os.listdir(dossier_fundus)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ])
            self.strip_fundus.charger_images(chemins_fundus, dossier_masques=self.dossier_od)
        except (FileNotFoundError, OSError) as e:
            print(f"[WARN] fundus_images introuvable : {e}")
 
       
            
    def _on_fundus_selected(self, chemin):
        """Émet le signal quand une image fundus est sélectionnée."""
        self.image_selectionnee.emit(chemin)

   

    def _on_segmentation_index_changed(self, index):
        """Synchronise la sélection fundus avec segmentation."""
        if self._syncing:
            return
        self._syncing = True
        if 0 <= index < len(self.strip_fundus.chemins):
            self.strip_fundus._selectionner(index)
        self._syncing = False

    def _selectionner(self, index):
        """Sélectionne l'image fundus à l'index donné."""
        if self.strip_fundus.chemins:
            self.strip_fundus._selectionner(index)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optic Vision Pro")
        self.resize(1000, 700)
        self.setStyleSheet(f"background-color: {BG}; color: white;")

        self.chemin_dossier = None
        self.chemin_courant = None
        self.index_courant = -1
        self.chemin_image = None
        self.path_image_courante = None
        self.list_paths = None
        self.langue_courante = LANGUE_DEFAUT          # "fr" ou "en"
        self.T = changement_langue(self.langue_courante)  # dictionnaire actif
        # Couleurs par défaut des masques
        self.couleurs_defaut = {
            "veines":  (0,   0,   255, 255),
            "arteres": (255, 0,   100, 255),
            "disque":  (0,   255, 0,   255),
        }
        self.couleurs = dict(self.couleurs_defaut)

        # Config par défaut : seul le disque est visible, opacité 100
        self.config_defaut = {
            "couleurs": dict(self.couleurs_defaut),
            "opacites": {
                "image":   50,
                "veines":  50,
                "arteres": 50,
                "disque":  50,
            },
            "visibilites": {
                "veines":  True,
                "arteres": True,
                "disque":  True,
            },
            "current_colors": {
                "veines":  "#2a6496",
                "arteres": "#e74c3c",
                "disque":  "#27ae60",
            },
        }

        # Stockage des réglages (couleurs + opacités) par image
        # { chemin: { "couleurs": {...}, "opacites": {...} } }
        self.config_par_image = {}

        # Stockage des mesures par image { chemin: {"csv": path, "data": dict} }
        self.mesures_par_image = {}

        # Items de segmentation
        self.item_fundus = None
        self.item_veins = None
        self.item_arteries = None
        self.item_od = None

        # Fenêtres dock (initialisées une seule fois)
        self.segmentation_window = None
        self.toolbox = None

        
        self.actAfficherToolbox = QAction("Afficher la toolbox", self)
        self.actAfficherToolbox.setCheckable(True)

        self.actEditerDisque = QAction("Éditer le disque optique", self)
        self.actEditerDisque.setCheckable(True)
        self.actEditerDisque.triggered.connect(self.edit_disque_optique)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Page d'accueil
        self.btn_container = None

        # Barre du haut avec bouton dossier
        self.topbar = QWidget()
        self.topbar.setFixedHeight(48)
        self.topbar.setStyleSheet(f"background: {PANEL}; border-bottom: 1px solid #2a2a2a;")
        top_layout = QHBoxLayout(self.topbar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        lbl_titre = QLabel("OPTIC VISION PRO")
        lbl_titre.setStyleSheet("font-size: 13px; font-weight: bold; color: #c8c8ff; letter-spacing: 2px;")
        lbl_titre.setCursor(Qt.PointingHandCursor)  
        lbl_titre.mousePressEvent = lambda event: self.retourner_accueil()

        self.dossier_travail = QPushButton("Ouvrir un dossier de travail")
        self.dossier_travail.setFixedHeight(32)
        self.dossier_travail.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: white;
                border: 1px solid #3a3a3a; border-radius: 6px;
                padding: 0 16px; font-size: 12px;
            }
            QPushButton:hover { background: #3a3a3a; }
        """)
        self.dossier_travail.clicked.connect(self.charger_dossier_travail)


        self.btn_dossier = QPushButton("Ouvrir un dossier d'images")
        self.btn_dossier.setFixedHeight(32)
        self.btn_dossier.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: white;
                border: 1px solid #3a3a3a; border-radius: 6px;
                padding: 0 16px; font-size: 12px;
            }
            QPushButton:hover { background: #3a3a3a; }
        """)
        self.btn_dossier.clicked.connect(self._ouvrir_dossier)

        self.lbl_info = QLabel("Aucun dossier chargé")
        self.lbl_info.setStyleSheet("color: #666; font-size: 11px;")

        top_layout.addWidget(lbl_titre)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_info)
        top_layout.addSpacing(16)
        top_layout.addWidget(self.dossier_travail)
        top_layout.addSpacing(16)
        top_layout.addWidget(self.btn_dossier)

        # Barre d'actions (cachée par défaut)
        self.actionbar = self._create_actionbar()
        self.actionbar.hide()

        # Zone d'affichage principale
        self.scene = QGraphicsScene()
        self.vue = QGraphicsView(self.scene)
        self.vue.setStyleSheet("background: #111111; border: none;")
        self.vue.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Label placeholder
        self.lbl_placeholder = QLabel("Ouvrez un dossier pour afficher les images")
        self.lbl_placeholder.setAlignment(Qt.AlignCenter)
        self.lbl_placeholder.setStyleSheet("color: #444; font-size: 16px;")

        # Barre de miniatures
        self.image_strip = ImageStripContainer()
        self.image_strip.hide()
        self.image_strip.image_selectionnee.connect(self._charger_image)
        self.image_strip.strip_fundus.selection_changed.connect(self._on_selection_changed)

        layout.addWidget(self.topbar)
        layout.addWidget(self.actionbar)
        layout.addWidget(self.lbl_placeholder, stretch=1)
        layout.addWidget(self.vue, stretch=1)
        self.vue.hide()
        layout.addWidget(self.image_strip)

        self._init_accueil()
        self.dossier_travail.setEnabled(False)
        self.btn_dossier.setEnabled(False)

        self.initial_pos = None
        self.topbar.hide()

    def resource_path(self,relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(__file__), relative_path)

    def _init_accueil(self):
        """Affiche la page d'accueil ."""
        self.btn_container = QWidget()
        container_layout = QVBoxLayout(self.btn_container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        container_layout.setAlignment(Qt.AlignCenter)

        # Logo
        self.logo = QLabel(self.btn_container)
        logo_pixmap = QPixmap(self.resource_path("OPV3.png"))
        ecran = QApplication.primaryScreen().availableGeometry()
        logo_pixmap = logo_pixmap.scaled(
            ecran.height() // 2, ecran.width() // 2,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.logo.setPixmap(logo_pixmap)
        self.logo.setAlignment(Qt.AlignCenter)

        # Bouton langue
        self.btn_langue = QPushButton(self.T["btn_langue"])
        self.btn_langue.setFixedSize(100, 32)
        self.btn_langue.setStyleSheet("""
            QPushButton {
                font-size: 12px; font-weight: bold;
                border-radius: 16px;
                background-color: #333333;
                color: #ffffff;
                padding: 4px 12px;
            }
            QPushButton:hover { background-color: #555555; }
        """)
        self.btn_langue.clicked.connect(self._basculer_langue)


        # Boutons
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setSpacing(20)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_pretraitement = QPushButton(self.T["btn_pretraitement"])
        self.btn_pretraitement.setFixedSize(200, 50)
        self.btn_pretraitement.setStyleSheet(self._style_accueil_btn())

        self.btn_traitement = QPushButton(self.T["btn_traitement"])
        self.btn_traitement.setFixedSize(200, 50)
        self.btn_traitement.setStyleSheet(self._style_accueil_btn())
        self.btn_traitement.clicked.connect(self._on_traitement_clicked)

        btn_layout.addWidget(self.btn_pretraitement)
        btn_layout.addWidget(self.btn_traitement)

        container_layout.addWidget(self.btn_langue, alignment=Qt.AlignRight)
        container_layout.addWidget(self.logo)
        container_layout.addWidget(btn_row)

        # Insérer avant le placeholder
        self.centralWidget().layout().insertWidget(1, self.btn_container)
        self.lbl_placeholder.hide()
        
    def retourner_accueil(self):
        """Retourne à la page d'accueil, en réinitialisant l'état."""
        self.scene.clear()
        self.item_fundus = None
        self.item_veins = None
        self.item_arteries = None
        self.item_od = None

        if self.segmentation_window:
            self.segmentation_window.hide()
        if self.toolbox:
            self.toolbox.hide()

        self.lbl_placeholder.show()
        self.vue.hide()
        self.actionbar.hide()
        self.image_strip.hide()
        self.topbar.hide()

        if self.btn_container:
            self.btn_container.show()

        # Réinitialiser les chemins et configs
        self.lbl_placeholder.hide()
        self.chemin_courant = None
        self.chemin_image = None
        self.path_image_courante = None
        self.list_paths = None

    def _basculer_langue(self):
            """Alterne entre français et anglais et met à jour toute l'interface."""
            self.langue_courante = "en" if self.langue_courante == "fr" else "fr"
            self.T = changement_langue(self.langue_courante)
            self._appliquer_langue()

    def _appliquer_langue(self):
        """Met à jour tous les textes statiques de l'interface avec self.T."""
        T = self.T
 
        # --- Bouton langue (accueil) ---
        if hasattr(self, "btn_langue"):
            self.btn_langue.setText(T["btn_langue"])
 
        # --- Boutons accueil ---
        if hasattr(self, "btn_pretraitement"):
            self.btn_pretraitement.setText(T["btn_pretraitement"])
        if hasattr(self, "btn_traitement"):
            self.btn_traitement.setText(T["btn_traitement"])
 
        # --- Barre haute ---
        self.dossier_travail.setText(T["btn_dossier_travail"])
        self.btn_dossier.setText(T["btn_dossier_images"])
 
        # --- Barre d'actions ---
        self.btn_precedent.setText(T["btn_precedent"])
        self.btn_suivant.setText(T["btn_suivant"])
        self.btn_exporter.setText(T["btn_sauvegarder"])
        self.btn_exporter_tous.setText(T["btn_sauvegarder_tout"])

        # --- Bouton mode sélection ---
        if hasattr(self, "btn_mode_selection"):
            if self.image_strip.strip_fundus.mode_selection:
                self.btn_mode_selection.setText(T["btn_selection_quitter"])
            else:
                self.btn_mode_selection.setText(T["btn_selection_activer"])
        if hasattr(self, "btn_exporter_selection"):
            n = len(self.image_strip.strip_fundus.indices_selectionnes)
            self.btn_exporter_selection.setText(T["btn_sauvegarder_n"].format(n=n))
 
        # --- Placeholder ---
        self.lbl_placeholder.setText(T["placeholder"])
 
        # --- Toolbox segmentation ---
        if self.segmentation_window is not None:
            self.segmentation_window.appliquer_langue(T)
 
        # --- Toolbox mesures ---
        if self.toolbox is not None:
            self.toolbox.appliquer_langue(T)
 
        # --- Titre fenêtre (si une image est chargée) ---
        if self.chemin_courant:
            n   = self.index_courant + 1
            tot = len(self.image_strip.strip_fundus.chemins)
            self.lbl_image_num.setText(T["lbl_image_num"].format(n=n, total=tot))



    @staticmethod
    def _style_accueil_btn():
        return """
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                border-radius: 25px;
                background-color: #ffffff;
                color: #000000;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #666666;
                color: white;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """

    def _on_traitement_clicked(self):
        """Cache l'accueil et affiche l'interface principale."""
        if self.btn_container:
            self.btn_container.hide()
        self.lbl_placeholder.show()
        self.dossier_travail.setEnabled(True)
        self.btn_dossier.setEnabled(True)
        self.statusBar().showMessage(self.T["status_etape1"])
        self.topbar.show()
        
    def charger_dossier_travail(self):
        if self.chemin_dossier is not None:
            self.reset("de dossier")
            self.chemin_dossier = None

        chemin_dossier = QFileDialog.getExistingDirectory(self, self.T["btn_dossier_travail"], os.getcwd())
        if chemin_dossier:
            StyledMessageBox.information(self, self.T["dlg_dossier_titre"], self.T["dlg_dossier_texte"].format(nom=chemin_dossier))
            self.chemin_dossier = chemin_dossier
            print(self.chemin_dossier)
        else:
            StyledMessageBox.warning(self, self.T["dlg_dossier_erreur_titre"], self.T["dlg_dossier_erreur_texte"])
            print(self.chemin_dossier)

    @staticmethod
    def _styled_msgbox(parent, titre: str, texte: str, info: str = "") -> StyledMessageBox:
        """Crée une QMessageBox stylisée réutilisable."""
        mb = StyledMessageBox(parent)
        mb.setWindowTitle(titre)
        mb.setText(texte)
        if info:
            mb.setInformativeText(info)
        return mb

    @staticmethod
    def _hex_to_rgba_tuple(hex_color: str) -> tuple:
        """Convertit #rrggbb en (r, g, b, 255)."""
        h = hex_color.lstrip("#")
        try:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except (ValueError, IndexError):
            return (0, 0, 255, 255)
        return (r, g, b, 255)

    def _ouvrir_dossier(self):
        dossier = QFileDialog.getExistingDirectory(self, self.T["btn_dossier_images"])
        if not dossier:
            return

        self.image_strip.charger_dossier(dossier)

        nb = len(self.image_strip.strip_fundus.chemins)
        if nb == 0:
            self.lbl_info.setText(self.T["aucune_image_strip"])
            return

        s = "s" if nb > 1 else ""
        self.lbl_info.setText(self.T["img_n_sur_total"].format(n=nb, s=s, dossier=os.path.basename(dossier)))
        self.image_strip.show()

        # Charger automatiquement la première image
        self.image_strip._selectionner(0)

    def _create_actionbar(self):
        """Crée la barre d'actions avec numéro d'image et boutons."""
        actionbar = QWidget()
        actionbar.setStyleSheet(f"background: {PANEL}; border-bottom: 1px solid #2a2a2a;")
        actionbar.setFixedHeight(44)

        layout = QHBoxLayout(actionbar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Affichage du numéro d'image
        self.lbl_image_num = QLabel("")
        self.lbl_image_num.setStyleSheet("color: #888; font-size: 11px; min-width: 150px;")

        # Boutons d'action
        self.btn_precedent = QPushButton(self.T["btn_precedent"])
        self.btn_precedent.setFixedSize(100, 32)
        self.btn_precedent.setStyleSheet(self._style_button())
        self.btn_precedent.clicked.connect(self._action_precedent)

        self.btn_suivant = QPushButton(self.T["btn_suivant"])
        self.btn_suivant.setFixedSize(100, 32)
        self.btn_suivant.setStyleSheet(self._style_button())
        self.btn_suivant.clicked.connect(self._action_suivant)

        self.btn_exporter = QPushButton(self.T["btn_sauvegarder"])
        self.btn_exporter.setFixedSize(100, 32)
        self.btn_exporter.setStyleSheet(self._style_button())
        self.btn_exporter.clicked.connect(self.save)
        
        self.btn_exporter_tous = QPushButton(self.T["btn_sauvegarder_tout"])
        self.btn_exporter_tous.setFixedSize(200, 32)
        self.btn_exporter_tous.setStyleSheet(self._style_button())
        self.btn_exporter_tous.clicked.connect(self._save_toutes_images)

        # Bouton pour activer/désactiver le mode sélection
        self.btn_mode_selection = QPushButton(self.T["btn_selection_activer"])
        self.btn_mode_selection.setFixedSize(100, 32)
        self.btn_mode_selection.setCheckable(True)
        self.btn_mode_selection.setStyleSheet(self._style_button())
        self.btn_mode_selection.clicked.connect(self._toggle_mode_selection)
        self.btn_mode_selection.setToolTip("Activez pour cocher/décocher des images à exporter.")

        # Bouton de sauvegarde de la sélection (visible uniquement en mode sélection)
        self.btn_exporter_selection = QPushButton(self.T["btn_sauvegarder_n"].format(n=0))
        self.btn_exporter_selection.setFixedSize(160, 32)
        self.btn_exporter_selection.setStyleSheet(self._style_button())
        self.btn_exporter_selection.clicked.connect(self._save_images_selectionnees)
        self.btn_exporter_selection.setEnabled(False)
        self.btn_exporter_selection.setVisible(False)

        layout.addWidget(self.lbl_image_num)
        layout.addStretch()
        layout.addWidget(self.btn_precedent)
        layout.addWidget(self.btn_suivant)
        layout.addWidget(self.btn_mode_selection)
        layout.addWidget(self.btn_exporter_selection)
        layout.addWidget(self.btn_exporter)
        layout.addWidget(self.btn_exporter_tous)
     

        return actionbar

    @staticmethod
    def _style_button():
        return """
            QPushButton {
                background: #2a2a2a;
                color: white;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background: #3a3a3a; }
            QPushButton:pressed { background: #444444; }
        """

    def _action_precedent(self):
        """Action bouton précédent."""
        self.image_strip.strip_fundus._precedent()

    def _action_suivant(self):
        """Action bouton suivant."""
        self.image_strip.strip_fundus._suivant()

    def _action_exporter(self):
        """Action pour exporter l'image."""
        if self.chemin_courant:
            fichier, _ = QFileDialog.getSaveFileName(
                self, self.T["btn_sauvegarder"], "", "Images JPG (*.jpg)"
            )
            if fichier:
                if not fichier.lower().endswith(".jpg"):
                    fichier += ".jpg"
                pixmap = QPixmap(self.chemin_courant)
                pixmap.save(fichier, "JPEG", 95)
                self.lbl_info.setText( self.T["btn_sauvegarder"] + os.path.basename(fichier))

    def _charger_image(self, chemin):
        """Affiche l'image sélectionnée avec ses 3 masques colorisés (pipeline main2.py)."""

        # --- Sauvegarder les réglages de l'image précédente ---
        if self.chemin_image and self.segmentation_window:
            self.config_par_image[self.chemin_image] = self.segmentation_window.recup_config()

        self.chemin_courant      = chemin
        self.chemin_image        = chemin
        self.path_image_courante = chemin
        self.index_courant       = self.image_strip.strip_fundus.index_courant

        # --- Restaurer ou initialiser les réglages de cette image ---
        config = self.config_par_image.get(chemin)

        # Si pas de config en mémoire, chercher un JSON sauvegardé sur disque
        if not config:
            nom_sans_ext = os.path.splitext(os.path.basename(chemin))[0]
            dossier      = os.path.dirname(chemin)
            for candidat in [
                os.path.join(dossier, f"{nom_sans_ext}_seg_config.json"),  # ← nouveau
                os.path.join(dossier, f"{nom_sans_ext}_config.json"),
                os.path.join(dossier, "config_segmentation.json"),
            ]:
                if os.path.exists(candidat):
                    try:
                        with open(candidat, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        if "couleurs" in config:
                            config["couleurs"] = {
                                k: tuple(v) for k, v in config["couleurs"].items()
                            }
                        self.config_par_image[chemin] = config
                        print(f"[INFO] Config chargée depuis {candidat}")
                    except Exception as e:
                        print(f"[WARN] Impossible de lire {candidat} : {e}")
                    break
            

        if config:
            self.couleurs = config["couleurs"]
        else:
            config = copy.deepcopy(self.config_defaut)
            self.couleurs = dict(self.couleurs_defaut)

        # --- Construire les 4 chemins ---
        self.list_paths = images_paths(chemin)

        # --- Charger et coloriser ---
        image_originale, mask_veins, mask_arteries, mask_od = load_images(
            self.list_paths,
            couleur_veines=self.couleurs["veines"],
            couleur_arteres=self.couleurs["arteres"],
            couleur_disque=self.couleurs["disque"],
        )
        pixmap_fundus, pixmap_veins, pixmap_arteries, pixmap_od = conversion_qpixmap(
            image_originale, mask_veins, mask_arteries, mask_od
        )

        # --- Peupler la scène ---
        self.scene.clear()
        self.item_fundus   = self.scene.addPixmap(pixmap_fundus)
        self.item_veins    = self.scene.addPixmap(pixmap_veins)
        self.item_arteries = self.scene.addPixmap(pixmap_arteries)
        self.item_od       = self.scene.addPixmap(pixmap_od)

        self.scene.setSceneRect(pixmap_fundus.rect())

        self.lbl_placeholder.hide()
        self.vue.show()
        self.actionbar.show()
        self.vue.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        # --- Titre et labels ---
        nom         = os.path.basename(chemin)
        nb_images   = len(self.image_strip.strip_fundus.chemins)
        num_affiche = self.index_courant + 1
        self.setWindowTitle(f"Optic Vision Pro — {num_affiche}/{nb_images}")
        self.lbl_image_num.setText(f"Image {num_affiche}/{nb_images}")
        self.btn_precedent.setEnabled(self.index_courant > 0)
        self.btn_suivant.setEnabled(self.index_courant < nb_images - 1)

        # --- Init dock segmentation (une seule fois) ---
        self._init_tableau_seg()

        # --- Activer les actions qui nécessitent une image chargée ---
        if hasattr(self, "actSave"):
            self.actSave.setEnabled(True)
        if hasattr(self, "actPleinEcran"):
            self.actPleinEcran.setEnabled(True)

        # --- Restaurer les opacités et couleurs dans la toolbox ---
        if config and self.segmentation_window:
            self.segmentation_window.restaurer_config(config)

        if self.chemin_dossier:
            nom_base = os.path.splitext(os.path.basename(chemin))[0]
            # nom_ovp = avec suffixe _OVP, nom_json = sans
            while nom_base.endswith("_OVP"):
                nom_base = nom_base[:-4]
            nom_json = nom_base          # ex: "1"
            nom_ovp  = f"{nom_base}_OVP" # ex: "1_OVP"

            # Dossier du dossier d'images courant (remonte depuis fundus_images/)
            dossier_image = os.path.dirname(chemin)
            if os.path.basename(dossier_image) == "fundus_images":
                dossier_image = os.path.dirname(dossier_image)
            parent_image = os.path.dirname(dossier_image)

            def _json_prov(nom):
                return os.path.join(self.chemin_dossier, "mesures_json", f"{nom}_data.json")
            def _json_res(nom):
                return os.path.join(self.chemin_dossier, "results", "mesures_json", f"{nom}_data.json")
            def _json_arch(nom):
                return os.path.join(self.chemin_dossier, f"{nom}_OVP", "results", "mesures_json", f"{nom}_data.json")
            def _json_glob(nom):
                pattern = os.path.join(self.chemin_dossier, "*_fundus_images_code_OVP", "results", "mesures_json", f"{nom}_data.json")
                r = glob.glob(pattern)
                return r[0] if r else ""
            def _json_image_results(nom):
                return os.path.join(dossier_image, "results", "mesures_json", f"{nom}_data.json")
            def _json_parent_glob(nom):
                pattern = os.path.join(parent_image, "*_fundus_images_code_OVP", "results", "mesures_json", f"{nom}_data.json")
                r = glob.glob(pattern)
                return r[0] if r else ""

            # Cherche dans l'ordre : archive > results image > provisoire/results, avec _OVP en priorité puis sans
            chemin_json = None
            for nom in (nom_ovp, nom_json):
                for candidat in (_json_arch(nom), _json_glob(nom), _json_image_results(nom), _json_parent_glob(nom), _json_prov(nom), _json_res(nom)):
                    if candidat and os.path.exists(candidat):
                        chemin_json = candidat
                        break
                if chemin_json:
                    break

            self._init_toolbox()
            self.toolbox.chemin_json_courant = chemin_json

    # ------------------------------------------------------------------
    # Chargement / affichage
    # ------------------------------------------------------------------

    def modif_couleurs(self, key: str, color_modif: tuple):
        """Reçoit la nouvelle couleur depuis SegmentationToolbox et recharge les masques."""
        r, g, b = color_modif[-3], color_modif[-2], color_modif[-1]
        self.couleurs[key] = (r, g, b, 255)
        self._sauvegarder_config_courante()
        self._recharger_masques()

    def _sauvegarder_config_courante(self):
        """Sauvegarde les réglages actuels (couleurs + opacités) pour l'image courante."""
        if not self.chemin_image:
            return
        config = {"couleurs": {k: tuple(v) for k, v in self.couleurs.items()}}
        if self.segmentation_window:
            config.update(self.segmentation_window.recup_config())
        self.config_par_image[self.chemin_image] = config

    def sauvegarder_config(self):
        """Sauvegarde en mémoire la config courante (sliders, couleurs, visibilités)
        pour l'image active. Appelé automatiquement au relâchement d'un slider."""
        if not self.chemin_image or not self.segmentation_window:
            return
        config = {"couleurs": {k: tuple(v) for k, v in self.couleurs.items()}}
        config.update(self.segmentation_window.recup_config())
        config["modifie"] = True
        self.config_par_image[self.chemin_image] = config

        # ← Un fichier par image, pas par dossier
        dossier      = os.path.dirname(self.chemin_image)
        nom_sans_ext = os.path.splitext(os.path.basename(self.chemin_image))[0]
        chemin_json  = os.path.join(dossier, f"{nom_sans_ext}_seg_config.json")
        try:
            with open(chemin_json, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, default=str)
        except Exception as e:
            print(f"[WARN] Impossible d'écrire {chemin_json} : {e}")


    def _recharger_masques(self):
        """Recharge les masques colorisés sans toucher au fundus ni à la scène entière."""
        if not self.list_paths or self.item_fundus is None:
            return

        image_originale, mask_veins, mask_arteries, mask_od = load_images(
            self.list_paths,
            couleur_veines=self.couleurs["veines"],
            couleur_arteres=self.couleurs["arteres"],
            couleur_disque=self.couleurs["disque"],
        )
        _, pixmap_veins, pixmap_arteries, pixmap_od = conversion_qpixmap(
            image_originale, mask_veins, mask_arteries, mask_od
        )

        # Met à jour les pixmaps en place — pas de scene.clear(), l'opacité est préservée
        if self.item_veins:
            self.item_veins.setPixmap(pixmap_veins)
        if self.item_arteries:
            self.item_arteries.setPixmap(pixmap_arteries)
        if self.item_od:
            self.item_od.setPixmap(pixmap_od)

        # Réapplique l'opacité courante depuis la toolbox
        if self.segmentation_window:
            self.segmentation_window.appliquer()

    def _init_tableau_seg(self):
        """Crée le dock de segmentation une seule fois, puis le rend visible."""
        if self.segmentation_window is None:
            self.segmentation_window = seg.SegmentationToolbox(self)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.segmentation_window)
            self.actAfficherToolbox.triggered.connect(self.segmentation_window.setVisible)
            self.segmentation_window.visibilityChanged.connect(self.actAfficherToolbox.setChecked)
            self.segmentation_window.appliquer_langue(self.T)

        self.segmentation_window.activate_all_segmentations()
        self.segmentation_window.show()

    def on_segmentation_appliquee(self, sel: dict):
        if self.item_fundus is None:
            return

        self.item_fundus.setOpacity(sel.get("image_opacity", 100) / 100.0)

        if sel.get("veines", {}).get("visible"):
            self.item_veins.setOpacity(sel["veines"]["opacity"] / 100.0)
        else:
            self.item_veins.setOpacity(0)

        if sel.get("arteres", {}).get("visible"):
            self.item_arteries.setOpacity(sel["arteres"]["opacity"] / 100.0)
        else:
            self.item_arteries.setOpacity(0)

        if sel.get("disque", {}).get("visible"):
            self.item_od.setOpacity(sel["disque"]["opacity"] / 100.0)
        else:
            self.item_od.setOpacity(0)

        # Sauvegarder les opacités pour cette image
        self._sauvegarder_config_courante()
        
    def creer_disque_optique(self, x_loc = 500, y_loc = 500):
        DiscToAdd= Image.open(self.list_paths[3]).convert("RGB")
        arr = np.array(DiscToAdd)

        if np.all(arr == 0): 
            draw = ImageDraw.Draw(DiscToAdd)
                    
            rayon = 76

            draw.ellipse(
                (
                x_loc - rayon,
                y_loc - rayon,
                x_loc + rayon,
                y_loc + rayon
                ),
                fill="white"
                )

        DiscToAdd.save(self.list_paths[3])
        self._recharger_masques()



    def edit_disque_optique(self, state=None):
        if state is None:
            state = self.actEditerDisque.isChecked()
 
        self.actEditerDisque.setChecked(state)
 
        if self.segmentation_window:
            self.segmentation_window.btn_editer.setChecked(state)

        if state is True:
            StyledMessageBox.information(self, "Mode édition", "Vous pouvez déplacer le disque sur l'image.")
 
        if self.item_od:
            self.item_od.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, state)
            self.item_od.setCursor(
                Qt.CursorShape.OpenHandCursor if state else Qt.CursorShape.ArrowCursor
            )
 
        # La boîte de sauvegarde s'ouvre seulement quand on DÉSACTIVE l'édition
        # (l'utilisateur vient de finir de déplacer le disque)
        if not state and self.item_od and self.list_paths:
            disqueBox = StyledMessageBox(self)
            disqueBox.setWindowTitle(self.T["dlg_disque_titre"])
            disqueBox.setText(self.T["dlg_disque_texte"])
            disqueBox.setInformativeText(self.T["dlg_disque_info"])
            oui_disque = disqueBox.addButton(self.T["dlg_disque_btn_oui"], QMessageBox.ActionRole)
            non_disque = disqueBox.addButton(self.T["dlg_disque_btn_non"], QMessageBox.ActionRole)
            disqueBox.exec()
 
            if disqueBox.clickedButton() == oui_disque:
                try:
        
                    chemin_od = self.list_paths[3]

                    # Déplacement en coordonnées scène
                    pos = self.item_od.scenePos()
                    dx  = int(pos.x())
                    dy  = int(pos.y())

                    # Charger, translater et sauvegarder le masque
                    masque = cv2.imread(chemin_od, cv2.IMREAD_GRAYSCALE)
                    if masque is not None:
                        h, w = masque.shape
                        M    = np.float32([[1, 0, dx], [0, 1, dy]])
                        masque_deplace = cv2.warpAffine(masque, M, (w, h))
                        cv2.imwrite(chemin_od, masque_deplace)

                        # Recharger le pixmap OD depuis le fichier mis à jour
                        # On force Qt à ne pas utiliser de cache en passant par QImage
                        od_image  = QImage(chemin_od)
                        pixmap_od = QPixmap.fromImage(od_image)

                        # Mettre à jour l'item en place sans bouger la scène
                        self.item_od.setPixmap(pixmap_od)
                        self.item_od.setPos(0, 0)

                        # Coloriser avec les couleurs courantes
                        self._recharger_masques()

                        # Mettre à jour la miniature dans le strip fundus
                        idx = self.image_strip.strip_fundus.index_courant
                        if 0 <= idx < len(self.image_strip.strip_fundus.boutons):
                            pixmap_mini = QPixmap(self.chemin_image).scaled(
                                80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                            pixmap_mini = self.image_strip.strip_fundus._superposer_masque(
                                pixmap_mini, chemin_od
                            )
                            btn = self.image_strip.strip_fundus.boutons[idx]
                            btn.setIcon(QIcon(pixmap_mini))
                            btn.setIconSize(pixmap_mini.size())

                        StyledMessageBox.information(self, "Succès", "Le disque optique a été mis à jour.")
                    else:
                        StyledMessageBox.warning(self, "Erreur", "Impossible de charger le masque du disque optique.")

                except Exception as e:
                    StyledMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {e}")

            if disqueBox.clickedButton() == non_disque:
                StyledMessageBox.information(self, "Annulé", "Le déplacement du disque optique a été annulé.")
                self.item_od.setPos(0, 0)


    #=================Lancer mesure=======================

    def trouver_json_mesures(self, nom_json):
        """Cherche le JSON de mesures dans tous les emplacements possibles."""
        if not self.chemin_dossier:
            return None

        # 1. Provisoire (calcul non sauvegardé)
        json_provisoire = os.path.join(self.chemin_dossier, "mesures_json", f"{nom_json}_data.json")
        if os.path.exists(json_provisoire):
            return json_provisoire

        # 2. Archive individuelle (save image par image)
        json_archive = os.path.join(self.chemin_dossier, f"{nom_json}_OVP", "results", "mesures_json", f"{nom_json}_data.json")
        if os.path.exists(json_archive):
            return json_archive

        # 3. Archive globale — nom du dossier inconnu, on parcourt tous les sous-dossiers
        try:
            for nom_sous_dossier in os.listdir(self.chemin_dossier):
                candidat = os.path.join(
                    self.chemin_dossier, nom_sous_dossier,
                    "results", "mesures_json", f"{nom_json}_data.json"
                )
                if os.path.exists(candidat):
                    return candidat
        except OSError:
            pass

        return None
    

    def mesure(self):

        if self.chemin_dossier is None:
            StyledMessageBox.information(self, "Aucun dossier sélectionné", self.T["dlg_save_aucun_dossier"])
            return

        self._init_toolbox()
        nom_image = os.path.basename(self.chemin_image)
        nom_base  = os.path.splitext(nom_image)[0]
        # Normaliser : retirer tous les _OVP pour avoir la racine
        while nom_base.endswith("_OVP"):
            nom_base = nom_base[:-4]
        nom_json = nom_base          # ex: "1"
        nom_ovp  = f"{nom_base}_OVP" # ex: "1_OVP"

        # Dossier de l'image courante (remonte depuis fundus_images/)
        dossier_image = os.path.dirname(self.chemin_image)
        if os.path.basename(dossier_image) == "fundus_images":
            dossier_image = os.path.dirname(dossier_image)

        def _results_vide(dossier):
            """Retourne True si results/ existe dans ce dossier et est vide."""
            try:
                d = os.path.join(dossier, "results")
                return os.path.isdir(d) and not os.listdir(d)
            except OSError:
                return False

        # Priorité : results/ vide du dossier d'images, puis du dossier de travail
        if _results_vide(dossier_image):
            dossier_results_direct = os.path.join(dossier_image, "results")
            racine_calcul = dossier_results_direct
        elif _results_vide(self.chemin_dossier):
            dossier_results_direct = os.path.join(self.chemin_dossier, "results")
            racine_calcul = dossier_results_direct
        else:
            dossier_results_direct = os.path.join(self.chemin_dossier, "results")
            racine_calcul = self.chemin_dossier

        output_csv_root = os.path.join(racine_calcul, "mesures.csv")

        def _chercher_json(nom):
            """Retourne le premier JSON trouvé pour ce nom (avec ou sans _OVP)."""
            # Dossier du dossier d'images courant (remonte depuis fundus_images/)
            dossier_image = os.path.dirname(self.chemin_image)
            if os.path.basename(dossier_image) == "fundus_images":
                dossier_image = os.path.dirname(dossier_image)

            candidats = [
                os.path.join(racine_calcul, "mesures_json", f"{nom}_data.json"),
                os.path.join(dossier_results_direct, "mesures_json", f"{nom}_data.json"),
                os.path.join(dossier_image, "results", "mesures_json", f"{nom}_data.json"),
                os.path.join(self.chemin_dossier, f"{nom}_OVP", "results", "mesures_json", f"{nom}_data.json"),
            ]
            # archive globale dans chemin_dossier
            pattern = os.path.join(self.chemin_dossier, "*_fundus_images_code_OVP", "results", "mesures_json", f"{nom}_data.json")
            candidats += glob.glob(pattern)
            # archive globale dans le dossier parent du dossier d'images
            parent_image = os.path.dirname(dossier_image)
            pattern2 = os.path.join(parent_image, "*_fundus_images_code_OVP", "results", "mesures_json", f"{nom}_data.json")
            candidats += glob.glob(pattern2)
            for c in candidats:
                if c and os.path.exists(c):
                    return c
            return None

        # --- TESTS D'EXISTENCE : chercher avec _OVP d'abord, puis sans ---
        chemin_json = _chercher_json(nom_ovp) or _chercher_json(nom_json)
        if chemin_json:
            self.toolbox.chemin_json_courant = chemin_json
            self.statusBar().showMessage(self.T["status_mesures_chargees"])
            return

        # --- Fallback CSV → conversion JSON ---
        for csv_path, racine_conv in [
            (os.path.join(dossier_results_direct, "mesures.csv"), dossier_results_direct),
            (output_csv_root, racine_calcul),
        ]:
            if os.path.exists(csv_path) and rc.image_est_dans_csv(csv_path, nom_image):
                self.statusBar().showMessage(self.T["status_chargement_mesures"])
                rc.csv_to_jsons(csv_path, racine_conv)
                chemin_json = _chercher_json(nom_ovp) or _chercher_json(nom_json)
                if chemin_json:
                    self.toolbox.chemin_json_courant = chemin_json
                    return

        # --- RIEN N'EXISTE : LANCEMENT DU CALCUL ---
        self.statusBar().showMessage(self.T["status_calcul"])

        vein_dir = self.chemin_abs("veins")
        art_dir  = self.chemin_abs("arteries")
        od_dir   = self.chemin_abs("od")

        os.makedirs(os.path.join(racine_calcul, "mesures_json"), exist_ok=True)

        args = ["measurements.py", art_dir, vein_dir, od_dir, output_csv_root]

        try:
            m_script.main(args)
            rc.csv_to_jsons(output_csv_root, racine_calcul)
            chemin_json = _chercher_json(nom_ovp) or _chercher_json(nom_json)
            self.toolbox.chemin_json_courant = chemin_json
            StyledMessageBox.information(self, "Mesures lancées avec succès", "Les mesures ont été lancées.")
            self.statusBar().showMessage(self.T["status_mesures_terminees"].format(nom=nom_image))

        except Exception as e:
            print(f"Erreur lors de l'exécution : {e}")
            self.statusBar().showMessage(self.T["status_erreur_calcul"])
            
    def chemin_abs(self, type_seg):
        abs_chemin = self.chemin_image

        if "fundus_images" in abs_chemin:
            abs_chemin = abs_chemin.rsplit("fundus_images", 1)
            abs_chemin = f"segmentation_masks/{type_seg}".join(abs_chemin)

        abs_chemin = os.path.dirname(abs_chemin)
        return abs_chemin

    def _chemin_rendu_final(self, chemin_source: str) -> str:
        """Retourne le chemin de destination du rendu final, crée le sous-dossier si besoin."""
        nom_sans_ext = os.path.splitext(os.path.basename(chemin_source))[0]
        
        # Retirer le suffixe _OVP s'il est déjà présent
        if nom_sans_ext.endswith("_OVP"):
            nom_sans_ext = nom_sans_ext[:-4]
        
        # Remonter d'un niveau au-dessus de fundus_images/
        dossier_parent = os.path.dirname(os.path.dirname(chemin_source))
        dossier_rendus = os.path.join(dossier_parent, "fundus_rendu_images_finales")
        os.makedirs(dossier_rendus, exist_ok=True)
        return os.path.join(dossier_rendus, f"{nom_sans_ext}_OVP_rendu.png")


    def sauvegarder_rendus(self):
        """Sauvegarde les rendus fusionnés dans le sous-dossier 'fundus_rendu_images_finales'
        du dossier d'images. Permet de mettre à jour des rendus déjà créés ou de créer
        des rendus pour des images non traitées."""

        # --- Première question : confirmer la mise à jour ---
        questionRendu = StyledMessageBox(self)
        questionRendu.setWindowTitle(self.T["dlg_rendus_maj_titre"])
        questionRendu.setText(self.T["dlg_rendus_maj_texte"])
        rendus_oui = questionRendu.addButton(self.T["dlg_rendus_btn_oui"], QMessageBox.ActionRole)
        rendus_non = questionRendu.addButton(self.T["dlg_rendus_btn_non"], QMessageBox.ActionRole)
        questionRendu.exec()

        if questionRendu.clickedButton() == rendus_non:
            return

        # --- Deuxième question : tous ou seulement les retravaillés ---
        quesRendu = StyledMessageBox(self)
        quesRendu.setWindowTitle(self.T["dlg_rendus_maj_titre"])
        quesRendu.setText(self.T["dlg_rendus_choix_texte"])
        rend_tous         = quesRendu.addButton(self.T["dlg_rendus_btn_tous"],         QMessageBox.ActionRole)
        rend_retravailles = quesRendu.addButton(self.T["dlg_rendus_btn_retravailles"], QMessageBox.ActionRole)
        quesRendu.exec()

        # --- Sauvegarde des retravaillés uniquement ---
        if quesRendu.clickedButton() == rend_retravailles:
            for chemin, config in self.config_par_image.items():
                if config.get("modifie", False):
                    rendu = self._generer_rendu_pour(chemin)
                    if rendu:
                        rendu.save(self._chemin_rendu_final(chemin), "JPEG", quality=95)
            StyledMessageBox.information(self, self.T["dlg_rendus_maj_titre"], self.T["dlg_rendus_succes_retrav"])

        # --- Sauvegarde de tous les rendus ---
        elif quesRendu.clickedButton() == rend_tous:
            tous_chemins = self.image_strip.strip_fundus.chemins
            nb = len(tous_chemins)
            erreurs = []
            for i, chemin in enumerate(tous_chemins):
                self.statusBar().showMessage(self.T["status_rendu_progress"].format(i=i+1, n=nb, nom=os.path.basename(chemin)))
                QApplication.processEvents()
                try:
                    rendu = self._generer_rendu_pour(chemin)
                    if rendu:
                        chemin_dest = self._chemin_rendu_final(chemin)
                        rendu.save(chemin_dest, "JPEG", quality=95)
                except Exception as e:
                    erreurs.append(f"{os.path.basename(chemin)} : {e}")
            if erreurs:
                StyledMessageBox.warning(self, self.T["dlg_rendus_maj_titre"],
                    self.T["dlg_rendus_partiel"].format(ok=nb - len(erreurs), total=nb, erreurs="\n".join(erreurs)))
            else:
                self.statusBar().showMessage(self.T["dlg_rendus_succes_tous"].format(n=nb))
                StyledMessageBox.information(self, self.T["dlg_rendus_maj_titre"], self.T["dlg_rendus_succes_tous"].format(n=nb))
                
            

    #-----------------ACTION 7: OUVRIR MESURES----------------
    def _init_toolbox(self):
        if self.toolbox is None:
            self.toolbox = mb.MesuresToolbox(self)
            self.addDockWidget(Qt.RightDockWidgetArea, self.toolbox)
            self.actAfficherToolbox.triggered.connect(self.toolbox.setVisible)
            self.toolbox.visibilityChanged.connect(self.actAfficherToolbox.setChecked)
            self.toolbox.appliquer_langue(self.T)
        self.toolbox.show()


    def generer_rendu_fusionne(self):
        """Crée une image fusionnant le fond d'œil et les calques de segmentation."""
        if self.item_fundus is None:
            return None

        image_finale = self.item_fundus.pixmap().toImage().convertToFormat(QtGui.QImage.Format_ARGB32)

        painter = QPainter(image_finale)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        calques = [
            (self.item_veins, "veines"),
            (self.item_arteries, "arteres"),
            (self.item_od, "disque")
        ]

        for item, key in calques:
            if item and item.opacity() > 0:
                pix = item.pixmap()
                painter.setOpacity(item.opacity())
                painter.drawPixmap(0, 0, pix)

        painter.end()
        return image_finale

    def _generer_rendu_pour(self, chemin):
        """Génère le rendu fusionné pour n'importe quelle image, même hors scène."""
        # Récupérer la config sauvegardée pour cette image (couleurs + opacités)
        config = self.config_par_image.get(chemin, self.config_defaut)
        couleurs = config.get("couleurs", self.couleurs_defaut)
        opacites = config.get("opacites", {"image": 100, "veines": 50, "arteres": 50, "disque": 100})
        visibilites = config.get("visibilites", {"veines": True, "arteres": True, "disque": True})

        try:
            paths = images_paths(chemin)
            image_orig, mask_veins, mask_arteries, mask_od = load_images(
                paths,
                couleur_veines=couleurs["veines"],
                couleur_arteres=couleurs["arteres"],
                couleur_disque=couleurs["disque"],
            )
            pix_f, pix_v, pix_a, pix_o = conversion_qpixmap(image_orig, mask_veins, mask_arteries, mask_od)
        except Exception as e:
            print(f"[WARN] Impossible de charger les masques pour {chemin} : {e}")
            return None

        image_finale = pix_f.toImage().convertToFormat(QtGui.QImage.Format_ARGB32)
        painter = QPainter(image_finale)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        for pix, key in [(pix_v, "veines"), (pix_a, "arteres"), (pix_o, "disque")]:
            if visibilites.get(key, True):
                opacity = opacites.get(key, 50) / 100.0
                if opacity > 0:
                    painter.setOpacity(opacity)
                    painter.drawPixmap(0, 0, pix)

        painter.end()
        return image_finale
    
    def _toggle_mode_selection(self, actif: bool):
        """Active/désactive le mode sélection sur les miniatures."""
        strip = self.image_strip.strip_fundus
        strip.activer_mode_selection(actif)

        if actif:
            self.btn_mode_selection.setStyleSheet("""
                QPushButton {
                    background: #1a4a2a;
                    color: #00ee66;
                    border: 1px solid #00cc55;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #205a32; }
                QPushButton:checked { background: #1a4a2a; }
            """)
            self.btn_mode_selection.setText(self.T["btn_selection_quitter"])
            self.btn_exporter_selection.setVisible(True)
            self.btn_precedent.setEnabled(False)
            self.btn_suivant.setEnabled(False)
        else:
            self.btn_mode_selection.setStyleSheet(self._style_button())
            self.btn_mode_selection.setText(self.T["btn_selection_activer"])
            self.btn_exporter_selection.setVisible(False)
            self.btn_exporter_selection.setEnabled(False)
            self.btn_precedent.setEnabled(True)
            self.btn_suivant.setEnabled(True)

    def _on_selection_changed(self, chemins):
        """Met à jour le bouton de sauvegarde de sélection."""
        n = len(chemins)
        self.btn_exporter_selection.setText(self.T["btn_sauvegarder_n"].format(n=n))
        self.btn_exporter_selection.setEnabled(n > 0)

    # ── Helpers partagés ────────────────────────────────────────────────

    def _check_config_existante(self, chemin_config):
        """Retourne True si on doit continuer, False si on annule/met-à-jour."""
        if not os.path.exists(chemin_config):
            return True

        msgBox = StyledMessageBox(self)
        msgBox.setWindowTitle(self.T["dlg_save_titre"])
        msgBox.setText(self.T["dlg_save_config_existe"])
        msgBox.setInformativeText(self.T["dlg_config_existe_info"])
        btn_maj = msgBox.addButton(self.T["dlg_save_btn_maj"], QMessageBox.ActionRole)
        msgBox.addButton(self.T["dlg_save_btn_nouveau"],       QMessageBox.ActionRole)
        msgBox.addButton(QMessageBox.Cancel)
        msgBox.exec()

        if msgBox.clickedButton() == btn_maj:
            if self.segmentation_window:
                data_seg = self.segmentation_window.recup_image()
                with open(chemin_config, 'w', encoding='utf-8') as f:
                    json.dump(data_seg, f, indent=4)
                self.statusBar().showMessage(self.T["status_maj_reglages"])
            return False  # Ne pas continuer la sauvegarde

        return msgBox.standardButton(msgBox.clickedButton()) != QMessageBox.Cancel

    def _exporter_masques(self, chemin_image, dossier_masks, nom_ovp):
        """Exporte les masques binarisés (veins, arteries, od)."""
        try:
            paths = images_paths(chemin_image)
            for chemin_mask, nom_calque in [(paths[1], "veins"), (paths[2], "arteries"), (paths[3], "od")]:
                if os.path.exists(chemin_mask):
                    mask_brut = cv2.imread(chemin_mask, cv2.IMREAD_GRAYSCALE)
                    if mask_brut is not None:
                        _, mask_bin = cv2.threshold(mask_brut, 1, 255, cv2.THRESH_BINARY)
                        sous_dossier = os.path.join(dossier_masks, nom_calque)
                        os.makedirs(sous_dossier, exist_ok=True)
                        cv2.imwrite(os.path.join(sous_dossier, f"{nom_ovp}.png"), mask_bin)
        except Exception as e:
            print(f"[WARN] Masques non exportés pour {nom_ovp} : {e}")

    def _trouver_json_pour_image(self, chemin_image: str) -> str | None:
        """Retourne le chemin du fichier _data.json de mesures pour une image donnée,
        en cherchant dans tous les emplacements connus (provisoire, archive, global)."""
        if not self.chemin_dossier:
            return None

        nom_base = os.path.splitext(os.path.basename(chemin_image))[0]
        while nom_base.endswith("_OVP"):
            nom_base = nom_base[:-4]
        nom_json = nom_base
        nom_ovp  = f"{nom_base}_OVP"

        dossier_image = os.path.dirname(chemin_image)
        if os.path.basename(dossier_image) == "fundus_images":
            dossier_image = os.path.dirname(dossier_image)
        parent_image = os.path.dirname(dossier_image)

        def candidats_pour(nom):
            c = [
                os.path.join(self.chemin_dossier, "mesures_json",          f"{nom}_data.json"),
                os.path.join(self.chemin_dossier, "results", "mesures_json", f"{nom}_data.json"),
                os.path.join(self.chemin_dossier, f"{nom}_OVP", "results", "mesures_json", f"{nom}_data.json"),
                os.path.join(dossier_image, "results", "mesures_json",     f"{nom}_data.json"),
            ]
            c += glob.glob(os.path.join(self.chemin_dossier, "*_fundus_images_code_OVP",
                                        "results", "mesures_json", f"{nom}_data.json"))
            c += glob.glob(os.path.join(parent_image, "*_fundus_images_code_OVP",
                                        "results", "mesures_json", f"{nom}_data.json"))
            return c

        for nom in (nom_ovp, nom_json):
            for c in candidats_pour(nom):
                if c and os.path.exists(c):
                    return c
        return None

    def _archiver_mesures(self, dossier_result):
        """Copie mesures.csv et mesures_json/ vers dossier_result (sans écraser les fichiers existants)."""
        csv_src      = os.path.join(self.chemin_dossier, "mesures.csv")
        json_dir_src = os.path.join(self.chemin_dossier, "mesures_json")

        if os.path.exists(csv_src):
            shutil.copy(csv_src, os.path.join(dossier_result, "mesures_globales.csv"))

        if os.path.exists(json_dir_src):
            json_dir_dest = os.path.join(dossier_result, "mesures_json")
            os.makedirs(json_dir_dest, exist_ok=True)
            for f in os.listdir(json_dir_src):
                src_f  = os.path.join(json_dir_src, f)
                dest_f = os.path.join(json_dir_dest, f)
                if os.path.isfile(src_f):
                    shutil.copy(src_f, dest_f)   # copie (écrase si même nom, mais préserve les autres)

    # ── Sauvegarde d'une seule image ────────────────────────────────────

    def _save_une_image(self, chemin_image, dossier_dest):
        """Sauvegarde une image et ses masques dans dossier_dest."""
        nom_base  = os.path.splitext(os.path.basename(chemin_image))[0]
        while nom_base.endswith("_OVP"):
            nom_base = nom_base[:-4]
        nom_ovp   = f"{nom_base}_OVP"
        extension = os.path.splitext(chemin_image)[1]

        dossier_projet = os.path.join(dossier_dest, nom_ovp)
        dossier_fundus = os.path.join(dossier_projet, "fundus_images")
        dossier_seg    = os.path.join(dossier_projet, "fundus_rendu_images_finales")
        dossier_result = os.path.join(dossier_projet, "results")

        for d in (dossier_fundus, dossier_seg, dossier_result):
            os.makedirs(d, exist_ok=True)

        shutil.copy(chemin_image, os.path.join(dossier_fundus, f"{nom_ovp}{extension}"))
        self._exporter_masques(chemin_image, os.path.join(dossier_projet, "segmentation_masks"), nom_ovp)

        if chemin_image == self.chemin_image:
            image_fusionnee = self.generer_rendu_fusionne()
            if image_fusionnee:
                image_fusionnee.save(os.path.join(dossier_seg, f"{nom_ovp}_rendu.png"))

            if self.segmentation_window:
                data_seg = self.segmentation_window.recup_image()
                with open(os.path.join(dossier_fundus, "config_segmentation.json"), 'w', encoding='utf-8') as f:
                    json.dump(data_seg, f, indent=4)

        mesures = self.mesures_par_image.get(chemin_image)
        if mesures:
            for src, dest in [(mesures.get("csv"), f"{nom_ovp}_mesures.csv"),
                              (mesures.get("json"), f"{nom_ovp}_data.json")]:
                if src and os.path.exists(src):
                    shutil.copy(src, os.path.join(dossier_result, dest))
        else:
            # Fallback : chercher le JSON de mesures sur le disque
            json_src = self._trouver_json_pour_image(chemin_image)
            if json_src:
                shutil.copy(json_src, os.path.join(dossier_result, f"{nom_ovp}_data.json"))

        return dossier_projet

    # ── Sauvegarde groupée (toutes ou sélection) ────────────────────────

    def _save_groupe(self, chemins):
        """Logique commune à _save_toutes_images et _save_images_selectionnees."""
        if not chemins:
            self.statusBar().showMessage(self.T["status_aucune_image_chargee"])
            return
        if self.chemin_dossier is None:
            StyledMessageBox.warning(self, self.T["dlg_save_erreur_titre"], self.T["dlg_save_aucun_dossier"])
            return

        sauv_fichier, ok = QInputDialog.getText(self, self.T["dlg_save_groupe_titre"], self.T["dlg_save_groupe_nom"])
        if not ok or not sauv_fichier.strip():
            return

        msgBox = StyledMessageBox(self)
        msgBox.setWindowTitle(self.T["dlg_save_all_titre"])
        msgBox.setText(self.T["dlg_save_groupe_texte"])
        btn_par_image = msgBox.addButton(self.T["dlg_save_all_btn1"], QMessageBox.ActionRole)
        btn_global    = msgBox.addButton(self.T["dlg_save_all_btn2"], QMessageBox.ActionRole)
        msgBox.addButton(QMessageBox.Cancel)
        msgBox.exec()

        if msgBox.clickedButton() not in (btn_par_image, btn_global):
            return

        nb, erreurs = len(chemins), []

        if msgBox.clickedButton() == btn_par_image:
            msgRendu = StyledMessageBox(self)
            msgRendu.setWindowTitle(self.T["dlg_rendus_titre"])
            msgRendu.setText(self.T["dlg_rendus_texte"])
            btn_tous  = msgRendu.addButton(self.T["dlg_rendus_btn_tous"],  QMessageBox.ActionRole)
            btn_modif = msgRendu.addButton(self.T["dlg_rendus_btn_modif"], QMessageBox.ActionRole)
            msgRendu.addButton(QMessageBox.Cancel)
            msgRendu.exec()

            if msgRendu.clickedButton() not in (btn_tous, btn_modif):
                return

            exporter_tous = msgRendu.clickedButton() == btn_tous
            dossier_dest  = os.path.join(self.chemin_dossier, f"{sauv_fichier}_fundus_images_code_OVP")
            os.makedirs(dossier_dest, exist_ok=True)

            for i, chemin in enumerate(chemins):
                self.statusBar().showMessage(self.T["status_sauvegarde_progress"].format(i=i+1, n=nb, nom=os.path.basename(chemin)))
                QApplication.processEvents()
                try:
                    nom_base  = os.path.splitext(os.path.basename(chemin))[0]
                    while nom_base.endswith("_OVP"):
                        nom_base = nom_base[:-4]
                    nom_ovp   = f"{nom_base}_OVP"
                    extension = os.path.splitext(chemin)[1]

                    # Un dossier par image avec ses 4 sous-dossiers
                    dossier_image  = os.path.join(dossier_dest, nom_ovp)
                    dossier_fundus = os.path.join(dossier_image, "fundus_images")
                    dossier_seg    = os.path.join(dossier_image, "fundus_rendu_images_finales")
                    dossier_result = os.path.join(dossier_image, "results")

                    for d in (dossier_fundus, dossier_seg, dossier_result):
                        os.makedirs(d, exist_ok=True)

                    shutil.copy(chemin, os.path.join(dossier_fundus, f"{nom_ovp}{extension}"))
                    self._exporter_masques(chemin, os.path.join(dossier_image, "segmentation_masks"), nom_ovp)

                    if exporter_tous or chemin in self.config_par_image:
                        image_fusionnee = self._generer_rendu_pour(chemin)
                        if image_fusionnee:
                            image_fusionnee.save(os.path.join(dossier_seg, f"{nom_ovp}_rendu.png"))

                    config = self.config_par_image.get(chemin)
                    if not config and chemin == self.chemin_image and self.segmentation_window:
                        config = self.segmentation_window.recup_image()
                    if config:
                        with open(os.path.join(dossier_fundus, f"{nom_ovp}_config.json"), 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=4, default=str)

                    mesures = self.mesures_par_image.get(chemin)
                    if mesures:
                        for src, dest in [(mesures.get("csv"), f"{nom_ovp}_mesures.csv"),
                                          (mesures.get("json"), f"{nom_ovp}_data.json")]:
                            if src and os.path.exists(src):
                                shutil.copy(src, os.path.join(dossier_result, dest))
                    else:
                        json_src = self._trouver_json_pour_image(chemin)
                        if json_src:
                            shutil.copy(json_src, os.path.join(dossier_result, f"{nom_ovp}_data.json"))

                except Exception as e:
                    erreurs.append(f"{os.path.basename(chemin)} : {e}")

        else:
            msgRendu = StyledMessageBox(self)
            msgRendu.setWindowTitle(self.T["dlg_rendus_titre"])
            msgRendu.setText(self.T["dlg_rendus_texte"])
            btn_tous  = msgRendu.addButton(self.T["dlg_rendus_btn_tous"],  QMessageBox.ActionRole)
            btn_modif = msgRendu.addButton(self.T["dlg_rendus_btn_modif"], QMessageBox.ActionRole)
            msgRendu.addButton(QMessageBox.Cancel)
            msgRendu.exec()

            if msgRendu.clickedButton() not in (btn_tous, btn_modif):
                return

            exporter_tous = msgRendu.clickedButton() == btn_tous
            dossier_dest  = os.path.join(self.chemin_dossier, f"{sauv_fichier}_fundus_images_code_OVP")
            dossier_fundus = os.path.join(dossier_dest, "fundus_images")
            dossier_seg    = os.path.join(dossier_dest, "fundus_rendu_images_finales")
            dossier_result = os.path.join(dossier_dest, "results")

            for d in (dossier_fundus, dossier_seg, dossier_result):
                os.makedirs(d, exist_ok=True)

            for i, chemin in enumerate(chemins):
                self.statusBar().showMessage(self.T["status_sauvegarde_progress"].format(i=i+1, n=nb, nom=os.path.basename(chemin)))
                QApplication.processEvents()
                try:
                    nom_base  = os.path.splitext(os.path.basename(chemin))[0]
                    while nom_base.endswith("_OVP"):
                        nom_base = nom_base[:-4]
                    nom_ovp   = f"{nom_base}_OVP"
                    extension = os.path.splitext(chemin)[1]

                    shutil.copy(chemin, os.path.join(dossier_fundus, f"{nom_ovp}{extension}"))
                    self._exporter_masques(chemin, os.path.join(dossier_dest, "segmentation_masks"), nom_ovp)

                    if exporter_tous or chemin in self.config_par_image:
                        image_fusionnee = self._generer_rendu_pour(chemin)
                        if image_fusionnee:
                            image_fusionnee.save(os.path.join(dossier_seg, f"{nom_ovp}_rendu.png"))

                    config = self.config_par_image.get(chemin)
                    if not config and chemin == self.chemin_image and self.segmentation_window:
                        config = self.segmentation_window.recup_image()
                    if config:
                        with open(os.path.join(dossier_fundus, f"{nom_ovp}_config.json"), 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=4, default=str)

                    # Mesures individuelles : via mesures_par_image ou recherche disque
                    mesures = self.mesures_par_image.get(chemin)
                    if mesures:
                        json_src = mesures.get("json")
                        if json_src and os.path.exists(json_src):
                            dest_json_dir = os.path.join(dossier_result, "mesures_json")
                            os.makedirs(dest_json_dir, exist_ok=True)
                            shutil.copy(json_src, os.path.join(dest_json_dir, f"{nom_ovp}_data.json"))
                    else:
                        json_src = self._trouver_json_pour_image(chemin)
                        if json_src:
                            dest_json_dir = os.path.join(dossier_result, "mesures_json")
                            os.makedirs(dest_json_dir, exist_ok=True)
                            shutil.copy(json_src, os.path.join(dest_json_dir, f"{nom_ovp}_data.json"))

                except Exception as e:
                    erreurs.append(f"{os.path.basename(chemin)} : {e}")

            self._archiver_mesures(dossier_result)

        if erreurs:
            StyledMessageBox.warning(self, self.T["dlg_save_titre"],
                self.T["dlg_save_all_partiel"].format(ok=nb - len(erreurs), total=nb, erreurs="\n".join(erreurs)))
        else:
            self.statusBar().showMessage(self.T["status_n_images"].format(n=nb))
            StyledMessageBox.information(self, self.T["dlg_save_succes_titre"],
                self.T["dlg_save_all_succes"].format(n=nb, chemin=dossier_dest))

    # ── Points d'entrée publics ─────────────────────────────────────────

    def save(self):
        """Sauvegarde l'image courante dans un nouveau projet _OVP."""
        if not self.chemin_image:
            self.statusBar().showMessage(self.T["status_aucune_image_a_enregistrer"])
            return
        if self.chemin_dossier is None:
            StyledMessageBox.warning(self, self.T["dlg_save_erreur_titre"], self.T["dlg_save_aucun_dossier"])
            return

        chemin_config = os.path.join(os.path.dirname(self.path_image_courante), "config_segmentation.json")
        if not self._check_config_existante(chemin_config):
            return

        _base = os.path.splitext(os.path.basename(self.chemin_image))[0]
        while _base.endswith("_OVP"):
            _base = _base[:-4]
        nom_ovp = f"{_base}_OVP"
        try:
            dossier_projet = self._save_une_image(self.chemin_image, self.chemin_dossier)

            if self.segmentation_window:
                data_seg = self.segmentation_window.recup_image()
                config_dest = os.path.join(dossier_projet, "fundus_images", "config_segmentation.json")
                with open(config_dest, 'w', encoding='utf-8') as f:
                    json.dump(data_seg, f, indent=4)

            csv_src = os.path.join(self.chemin_dossier, "mesures.csv")
            if os.path.exists(csv_src):
                shutil.move(csv_src, os.path.join(dossier_projet, "results", f"{nom_ovp}_mesures.csv"))

            json_dir_src = os.path.join(self.chemin_dossier, "mesures_json")
            if os.path.exists(json_dir_src):
                json_dir_dest = os.path.join(dossier_projet, "results", "mesures_json")
                if os.path.exists(json_dir_dest):
                    shutil.rmtree(json_dir_dest)
                shutil.move(json_dir_src, json_dir_dest)

            self.statusBar().showMessage(self.T["status_projet_enregistre"].format(nom=nom_ovp))
            StyledMessageBox.information(self, self.T["dlg_save_succes_titre"],
                self.T["dlg_save_projet_succes"].format(chemin=dossier_projet))
        except Exception as e:
            StyledMessageBox.critical(self, self.T["dlg_save_erreur_titre"],
                self.T["dlg_save_erreur_texte"].format(erreur=str(e)))

    def _save_image_courante(self):
        """Sauvegarde uniquement l'image affichée (choix du dossier libre)."""
        chemin_config = os.path.join(os.path.dirname(self.path_image_courante), "config_segmentation.json")
        if not self._check_config_existante(chemin_config):
            return

        dossier_dest = QFileDialog.getExistingDirectory(self, self.T["dlg_save_titre"])
        if not dossier_dest:
            return

        try:
            dossier_projet = self._save_une_image(self.chemin_image, dossier_dest)
            self.statusBar().showMessage(self.T["status_sauvegarde"])
            StyledMessageBox.information(self, self.T["dlg_save_succes_titre"],
                self.T["dlg_save_succes_texte"].format(chemin=dossier_projet))
        except Exception as e:
            StyledMessageBox.critical(self, self.T["dlg_save_erreur_titre"],
                self.T["dlg_save_erreur_texte"].format(erreur=str(e)))

    def _save_toutes_images(self):
        self._save_groupe(self.image_strip.strip_fundus.chemins)

    def _save_images_selectionnees(self):
        chemins = self.image_strip.strip_fundus.chemins_selectionnes()
        if not chemins:
            StyledMessageBox.information(self, self.T["dlg_selection_vide_titre"],
                self.T["dlg_selection_vide_texte"])
            return
        self._save_groupe(chemins)

    def closeEvent(self, event):
        """Sauvegarde la config de toutes les images modifiées avant de quitter."""
        for chemin, config in self.config_par_image.items():
            dossier      = os.path.dirname(chemin)
            nom_sans_ext = os.path.splitext(os.path.basename(chemin))[0]
            chemin_json  = os.path.join(dossier, f"{nom_sans_ext}_seg_config.json")
            try:
                with open(chemin_json, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, default=str)
            except Exception as e:
                print(f"[WARN] Impossible d'écrire {chemin_json} : {e}")
        
        self.sauvegarder_config()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())