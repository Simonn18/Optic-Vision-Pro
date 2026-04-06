import sys
import os

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog,
    QLabel, QMenu, QStatusBar, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QStyle, QDockWidget, QCheckBox,
    QGroupBox, QScrollArea, QFrame, QSizePolicy)


import image_ref as ir
import opacite as op
import mesures_box as mb
import plein_ecran as pe 
import affiche_seg as af
import segmentation as seg


CARD  = "#b0b0b0"
BG    = "#f0f0f0"


#_______________________________
# Création panel central 
#________________________________
def make_panel(parent, color=CARD): # Fond gris derriere les images 
    """Crée un panneau gris arrondi."""
    panel = QWidget(parent)
    panel.setStyleSheet(f"background-color: {color}; border-radius: 40px;")
    return panel


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.od_valide             = False
        self.segmentation_terminee = False
        self.chemin_image          = None
        self.chemin_veines         = None
        self.chemin_arteres        = None
        self.chemin_disque         = None
        self.panel_active          = False
        self.affichage_double      = None
        self.open_panel = False

        self.setWindowTitle("Optic Vision Pro")
        self.resize(960, 620)

        self._init_actions()
        self._create_menus()
        self._init_panels()
    
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("ETAPE 1 : Telecharger une image de fond d'oeil.")
    
    # ──────────────────────────────────────────────
    # Panneau central
    # ──────────────────────────────────────────────

    def _init_panels(self):
        self.bg = QWidget(self)
        self.bg.setStyleSheet(f"background-color: {BG};")
        self.setCentralWidget(self.bg)

        main_layout = QVBoxLayout(self.bg)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.panel_centre = make_panel(self.bg)
        panel_layout = QVBoxLayout(self.panel_centre)

        self.lbl_import = QLabel(
            "GLISSER UN FICHIER OU\nRECHERCHER UN FICHIER\nSUR L'ORDINATEUR",
            self.panel_centre,
        )
        self.lbl_import.setAlignment(Qt.AlignCenter)
        self.lbl_import.setWordWrap(True)
        self.lbl_import.setStyleSheet(
            "color: #222; font-size: 18px; background: transparent;"
        )
        
        if self.open_panel is False:
            self.lbl_import.setCursor(Qt.PointingHandCursor)
            self.lbl_import.triggered.connect(self.open)
            self.open_panel = True

        panel_layout.addWidget(self.lbl_import)
        main_layout.addWidget(self.panel_centre)

    # ──────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────

    def _init_actions(self):
        style = self.style()

        self.actOpen = QAction("&Ouvrir...", self)
        self.actOpen.setShortcut("Ctrl+O")
        self.actOpen.setStatusTip("Ouvrir un fichier image")
        self.actOpen.triggered.connect(self.open)

        self.actSave = QAction("&Enregistrer", self)
        self.actSave.setShortcut("Ctrl+S")
        self.actSave.setStatusTip("Enregistrer le fichier")

        self.actOpacite = QAction("&Opacite", self)
        self.actOpacite.setShortcut("Ctrl+T")
        self.actOpacite.setStatusTip("Regler l'opacite")
        self.actOpacite.setEnabled(False)
        self.actOpacite.triggered.connect(self.open_opacite)

        self.actEditerDisque = QAction("&Editer le disque", self)
        self.actEditerDisque.setShortcut("Ctrl+E")
        self.actEditerDisque.setStatusTip("Editer le disque optique")
        self.actEditerDisque.setEnabled(False)

        self.act_valider_od = QAction("Valider le Disque Optique", self)
        self.act_valider_od.setEnabled(False)
        self.act_valider_od.triggered.connect(self.valider_disque_optique)

        self.act_run_seg = QAction("Lancer la Segmentation", self)
        self.act_run_seg.setIcon(
            style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.act_run_seg.setEnabled(False)
        self.act_run_seg.triggered.connect(self.lancer_segmentation)

        self.actAfficherToolbox = QAction("&Mesures", self)
        self.actAfficherToolbox.setCheckable(True)
        self.actAfficherToolbox.setShortcut("Ctrl+M")
        self.actAfficherToolbox.setStatusTip(
            "Afficher / masquer la boite a outils des mesures"
        )

        self.actPleinEcran = QAction("&Plein ecran", self)
        self.actPleinEcran.setShortcut("Ctrl+P")
        self.actPleinEcran.setStatusTip("Afficher en plein ecran")
        self.actPleinEcran.triggered.connect(self.open_plein_ecran)

        self.actAbout  = QAction("A propos", self)
        self.actReadme = QAction("Readme",   self)

    # ──────────────────────────────────────────────
    # Menus
    # ──────────────────────────────────────────────

    def _create_menus(self):
        mb = self.menuBar()

        m_fichier = mb.addMenu("&Fichier")
        m_fichier.addAction(self.actOpen)
        m_fichier.addSeparator()
        m_fichier.addAction(self.actSave)
        
        m_outils = mb.addMenu("&Outils")
        m_outils.addAction(self.actEditerDisque)
        m_outils.addAction(self.actOpacite)

        m_config = mb.addMenu("&Configuration")
        m_config.addAction(self.act_valider_od)

        m_analyse = mb.addMenu("&Analyse")
        m_analyse.addAction(self.act_run_seg)
        m_analyse.addSeparator()
        #m_analyse.addAction(self.actAfficherToolbox)

        m_pe = mb.addMenu("&Plein ecran")
        m_pe.addAction(self.actPleinEcran)

        m_aide = mb.addMenu("&Aide")
        m_aide.addAction(self.actAbout)
        m_aide.addAction(self.actReadme)


    #__________________________________________
    #FONCTION APPELEE PAR LES ACTIONS
    #__________________________________________

    #------------------ACTION 1 : CHARGER IMAGE-----------------
    @Slot()
    def open(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une image","", "Images (*.jpg)" 
        )
        if chemin:  
            self.chemin_image = chemin
            ir.charger_image_dans_label(self.lbl_import, chemin)
            self.panel_active = True  
            self.statusBar().showMessage("Image chargée avec succès. ÉTAPE 2 : Ajouter les segmentations.")
            self.tableau_seg()
            self.actOpacite.setEnabled(True)
            
            
    #------------------ACTION 2 : AFFICHER/SUPPRIMER LES SEGMENTATIONS-----------------
    def tableau_seg(self):
        self.segmentation_window = seg.SegmentationToolbox(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.segmentation_window)
        self.actAfficherToolbox.triggered.connect(self.segmentation_window.setVisible)
        self.segmentation_window.visibilityChanged.connect(self.actAfficherToolbox.setChecked)
    
    
    def on_segmentation_appliquee(self, sel: dict):
        if sel["veines"]:
            af.affiche_seg(self,"veines",chemin=self.chemin_image)
        if sel["arteres"]:
            af.affiche_seg(self,"arteres",chemin=self.chemin_image)
        if sel["disque"]:
            af.affiche_seg(self,"disque",chemin=self.chemin_image)
            self.actEditerDisque.setEnabled(True)
            self.act_valider_od.setEnabled(True)
    
               
    #------------------ACTION 3 : OUVRIR LA FENETRE OPACITE----------------
    def open_opacite(self):
        dialog = op.Opacite(self)
        dialog.exec()
        
    #------------------ACTION 4 : EDITER LE DISQUE OPTIQUE-----------------
    def edit_disque_optique(self):
        return 
         
    #------------------ACTION 5 : VALIDER LE DISQUE OPTIQUE-----------------
    def valider_disque_optique(self):
        rep = QMessageBox.question(self, "Validation", 
            "Confirmez-vous le placement du Disque Optique ?")

        if rep == QMessageBox.Yes:
            self.od_valide = True
            self.act_valider_od.setEnabled(False)
            
            self.act_run_seg.setEnabled(True) 
            
            self.statusBar().showMessage("Configuration validée. Vous pouvez lancer la segmentation avant de définir les paramètres.")
        else:
            self.statusBar().showMessage("Ajustez le disque optique avant de valider.")
            
        
    #------------------ACTION 6 : LANCER LA SEGMENTATION-----------------
    def lancer_segmentation(self):
        self.statusBar().showMessage("Segmentation IA en cours...")
        self.segmentation_terminee = True
        self.act_run_seg.setEnabled(False)
        self._init_toolbox()
        
    #-----------------ACTION 7: OUVRIR MESURES----------------
    def _init_toolbox(self):
        self.toolbox = mb.MesuresToolbox(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.toolbox)
        self.actAfficherToolbox.triggered.connect(self.toolbox.setVisible)
        self.toolbox.visibilityChanged.connect(self.actAfficherToolbox.setChecked)
        
    #------------------ACTION 8 : PLEIN ECRAN-----------------
    def open_plein_ecran(self):
        if self.chemin_image is None:
            self.statusBar().showMessage("Chargez d'abord une image.")
            return
        pe.PleinEcranWindow(self, chemin=self.chemin_image).exec()
    
            
    
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MyWindow()
    win.show()
    sys.exit(app.exec())