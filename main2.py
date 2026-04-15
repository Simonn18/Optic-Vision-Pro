import sys
import os
import shutil
import cv2
import numpy as np
import json


from PySide6 import QtGui
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog, 
    QLabel, QMenu, QStatusBar, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QStyle, QDockWidget, QCheckBox, QGraphicsScene, QGraphicsView,
    QGroupBox, QScrollArea, QFrame, QSizePolicy, QInputDialog, QSplashScreen)

import opacite as op
import mesures_box as mb
import plein_ecran as pe
import segmentation2 as seg
import measurements2 as m_script
# import superposition_imagesv3 as sp
import read_csv as rc
from chargement_images import load_images, images_paths
from affichage_images import conversion_qpixmap


CARD  = "#000000"
BG    = "#f0f0f0"


#_______________________________
# Création panel central 
#________________________________
def make_panel(parent, color=CARD): # Fond gris derriere les images 
    """Crée un panneau noir arrondi."""
    panel = QWidget(parent)
    panel.setStyleSheet(f"background-color: {color}; border-radius: 20px;")
    return panel


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.od_valide = False
        self.segmentation_terminee = False
        self.chemin_dossier = None
        self.chemin_image = None
        self.chemin_veines = None
        self.chemin_arteres = None 
        self.chemin_disque= None
        self.panel_active = False
        self.affichage_double = None
        self.segmentation_window = None
        self.toolbox = None
        self.image_composite = None
        self.path_image_courante = None 

        self.setWindowTitle("Optic Vision Pro")
        self.resize(960, 620)
        self._init_actions()
        self._create_menus()
        self._init_panels()

        self.couleurs = {
            "veines":  (0,   0,   255, 255),
            "arteres": (255, 0,   100, 255),
            "disque":  (0,   255, 0,   255),
        }
    
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

        # Remplacement du QLabel par une QGraphicsView
        self.scene = QGraphicsScene()
        self.vue = QGraphicsView(self.scene)
        self.vue.setStyleSheet("background: transparent; border: none;")

        self.lbl_import = QLabel(
            "CHARGER OU CREER UN DOSSIER\nET RECHERCHER UN FICHIER\nSUR L'ORDINATEUR",
            self.panel_centre,
        )
        self.lbl_import.setAlignment(Qt.AlignCenter)
        self.lbl_import.setWordWrap(True)
        self.lbl_import.setStyleSheet(
            "color: #F7F2FF; font-size: 18px; background: transparent, bold;"
        )

        # Calques de la scène (None tant qu'aucune image n'est chargée)
        self.item_fundus    = None
        self.item_veins     = None
        self.item_arteries  = None
        self.item_od        = None

        panel_layout.addWidget(self.lbl_import)
        panel_layout.addWidget(self.vue)
        self.vue.hide()  # cachée jusqu'au chargement d'une image
        main_layout.addWidget(self.panel_centre)
 
    # ──────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────

    def _init_actions(self):
        style = self.style()

        self.charger_dossier = QAction("&Créer/ouvrir un dossier", self)
        self.charger_dossier.setShortcut("Ctrl+L")
        self.charger_dossier.setStatusTip("creer/charger dossier")
        self.charger_dossier.triggered.connect(self.creer_charger_dossier_travail)
        
        self.actOpen = QAction("&Ouvrir...", self)
        self.actOpen.setShortcut("Ctrl+O")
        self.actOpen.setStatusTip("Ouvrir un fichier image")
        self.actOpen.setEnabled(True)
        self.actOpen.triggered.connect(self.open)

        self.actSave = QAction("&Enregistrer", self)
        self.actSave.setShortcut("Ctrl+S")
        self.actSave.setStatusTip("Enregistrer le fichier")
        self.actSave.setEnabled(False)
        self.actSave.triggered.connect(self.save)

        self.actOpacite = QAction("&Opacite", self)
        self.actOpacite.setShortcut("Ctrl+T")
        self.actOpacite.setStatusTip("Regler l'opacite")
        self.actOpacite.setEnabled(False)
        #self.actOpacite.triggered.connect(self.open_opacite)

        self.actEditerDisque = QAction("&Editer le disque", self)
        self.actEditerDisque.setShortcut("Ctrl+E")
        self.actEditerDisque.setStatusTip("Editer le disque optique")
        self.actEditerDisque.setEnabled(False)

        self.act_valider_od = QAction("Valider le Disque Optique", self)
        self.act_valider_od.setShortcut("Ctrl+Y")
        self.act_valider_od.setEnabled(False)
        #self.act_valider_od.triggered.connect(self.valider_disque_optique)

        self.act_run_seg = QAction("Lancer les mesures", self)
        self.act_run_seg.setShortcut("Ctrl+M")
        self.act_run_seg.setIcon(
            style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.act_run_seg.setEnabled(False)
        self.act_run_seg.triggered.connect(self.mesure)

        self.actAfficherToolbox = QAction("&Mesures", self)
        self.actAfficherToolbox.setCheckable(True)
        self.actAfficherToolbox.setStatusTip(
            "Afficher / masquer la boite a outils des mesures"
        )

        self.actPleinEcran = QAction("&Plein ecran", self)
        self.actPleinEcran.setShortcut("Ctrl+P")
        self.actPleinEcran.setStatusTip("Afficher en plein ecran")
        self.actPleinEcran.setEnabled(False)
        self.actPleinEcran.triggered.connect(self.open_plein_ecran)

        self.actAbout  = QAction("A propos", self)
        self.actReadme = QAction("Readme",   self)

    # ──────────────────────────────────────────────
    # Menus
    # ──────────────────────────────────────────────

    def _create_menus(self):
        mb = self.menuBar()

        m_fichier = mb.addMenu("&Fichier")
        m_fichier.addAction(self.charger_dossier)
        m_fichier.addSeparator()
        m_fichier.addAction(self.actOpen)
        m_fichier.addSeparator()
        m_fichier.addAction(self.actSave)
        
        # m_outils = mb.addMenu("&Outils")
        # m_outils.addAction(self.actEditerDisque)
        # m_outils.addAction(self.actOpacite)

        # m_config = mb.addMenu("&Configuration")
        # m_config.addAction(self.act_valider_od)

        # m_analyse = mb.addMenu("&Analyse")
        # m_analyse.addAction(self.act_run_seg)
        # m_analyse.addSeparator()
        # #m_analyse.addAction(self.actAfficherToolbox)

        m_pe = mb.addMenu("&Plein ecran")
        m_pe.addAction(self.actPleinEcran)

        m_aide = mb.addMenu("&Aide")
        m_aide.addAction(self.actAbout)
        m_aide.addAction(self.actReadme)


    #__________________________________________
    #FONCTION APPELEE PAR LES ACTIONS
    #__________________________________________


    #-----------------ACTION 0 : CRÉER REPERTOIRE DE TRAVAIL------
                
    def creer_charger_dossier_travail(self):
        if self.chemin_dossier is None:
            chemin_dossier = QFileDialog.getExistingDirectory(self, "Choisir un dossier de travail", os.getcwd())
            if chemin_dossier:
                # Logique pour charger les données du dossier
                QMessageBox.information(self, "Dossier chargé", f"Dossier '{chemin_dossier}' chargé avec succès.")
                self.actOpen.setEnabled(True)
                self.chemin_dossier = chemin_dossier
            else:
                QMessageBox.warning(self, "Erreur", "Aucun dossier sélectionné.")
                print(self.chemin_dossier)
        else:
            self.reset()
            self.chemin_dossier = None
        
        
    #------------------ACTION 1 : CHARGER IMAGE-----------------
    @Slot()
    def open(self):
        if self.chemin_image is None:
            chemin, _ = QFileDialog.getOpenFileName(
                self,
                "Choisir une image","", "Images (*.jpg)" 
            )
            if chemin:  
                self.chemin_image = chemin
                self.path_image_courante = chemin
                list_paths = images_paths(chemin)
                image_originale, mask_veins, mask_arteries, mask_od = load_images(list_paths)
                pixmap_fundus, pixmap_veins, pixmap_arteries, pixmap_od = conversion_qpixmap(
                    image_originale, mask_veins, mask_arteries, mask_od
                )
                
                # Initialisation de la scène
                self.scene.clear()
                self.item_fundus    = self.scene.addPixmap(pixmap_fundus)
                self.item_veins     = self.scene.addPixmap(pixmap_veins)
                self.item_arteries  = self.scene.addPixmap(pixmap_arteries)
                self.item_od        = self.scene.addPixmap(pixmap_od)
                self.item_veins.setOpacity(0.5)
                self.item_arteries.setOpacity(0.5)
                self.item_od.setOpacity(0.5)

                # Affichage
                self.lbl_import.hide()
                self.vue.show()
                self.vue.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

                self.panel_active = True  
                self.tableau_seg()
                self.actSave.setEnabled(True)
                self.actPleinEcran.setEnabled(True)
        else:
            
            self.reset()
            
            
    #------------------ACTION 2 : AFFICHER/SUPPRIMER LES SEGMENTATIONS-----------------
    def tableau_seg(self):
        self.segmentation_window = seg.SegmentationToolbox(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.segmentation_window)
        self.actAfficherToolbox.triggered.connect(self.segmentation_window.setVisible)
        self.segmentation_window.visibilityChanged.connect(self.actAfficherToolbox.setChecked)
        
        # ✅ Activer automatiquement toutes les segmentations
        self.segmentation_window.activate_all_segmentations()
    
    
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
               
    #------------------ACTION 3 : OUVRIR LA FENETRE OPACITE----------------
    def open_opacite(self):
        dialog = op.Opacite(self)
        dialog.exec()
        
    #------------------ACTION 4 : EDITER LE DISQUE OPTIQUE-----------------
    def edit_disque_optique(self):
        print("renvoie au parent")
         
    # #------------------ACTION 5 : VALIDER LE DISQUE OPTIQUE-----------------
    # def valider_disque_optique(self):
    #     rep = QMessageBox.question(self, "Validation", 
    #         "Confirmez-vous le placement du Disque Optique ?")

    #     if rep == QMessageBox.Yes:
    #         self.od_valide = True
                        
    #         self.statusBar().showMessage("Configuration validée. Vous pouvez lancer la segmentation avant de définir les paramètres.")
    #     else:
    #         self.statusBar().showMessage("Ajustez le disque optique avant de valider.")
            
        
    #------------------ACTION 6 : LANCER LES MESURES-----------------
    def mesure(self):
        # self.segmentation_terminee = True
        QMessageBox.information(self, "Mesures lancées", "Les mesures ont été lancées avec succès.")
        self._init_toolbox()
        
        if not self.chemin_image:
            print("Erreur : Aucune image chargÃ©e.")
            return

        nom_image = os.path.basename(self.chemin_image)
        
        nom_masque = nom_image.replace(".jpg", ".png")
        self.statusBar().showMessage("Veuillez patienter...")

        base_dir = "segmentation_masks"
        vein_dir = self.chemin_abs("veins")
        art_dir  = self.chemin_abs("arteries") 
        od_dir   = self.chemin_abs("od")  
        output_csv = "test_mesures.csv"

        args = ["measurements2.py", art_dir, vein_dir, od_dir, output_csv, nom_masque]

        try:
            m_script.main(args)
            self.statusBar().showMessage("Mesure terminÃ©e. DonnÃ©es enregistrÃ©es dans test_mesure.csv.")

            row_brute = rc.read_first_row(output_csv)
            
            if row_brute:
                self.data_complete = rc.classer_donnees(row_brute)

                rc.write_json(self.data_complete, "data.json")
                
                print("Succès: Données extraites, classées et sauvegardées dans data.json")
                

                self.statusBar().showMessage("Analyse terminée. Données enregistrées dans data.json.")
            else:
                self.statusBar().showMessage("Erreur : Le script n'a gÃ©nÃ©rÃ© aucune ligne de donnÃ©es.")

        except Exception as e:
            print(f"Erreur lors de l'exÃ©cution : {e}")

    def chemin_abs(self, type_seg):
        abs_chemin = self.chemin_image

        if "fundus_images" in abs_chemin:
            abs_chemin = abs_chemin.rsplit("fundus_images", 1)
            abs_chemin = f"segmentation_masks/{type_seg}".join(abs_chemin)

        abs_chemin = os.path.dirname(abs_chemin)
        return abs_chemin
        
    #-----------------ACTION 7: OUVRIR MESURES----------------
    def _init_toolbox(self):
        self.toolbox = mb.MesuresToolbox(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.toolbox)
        self.actAfficherToolbox.triggered.connect(self.toolbox.setVisible)
        self.toolbox.visibilityChanged.connect(self.actAfficherToolbox.setChecked)
        
    #------------------ACTION 8 : PLEIN ECRAN-----------------
    def open_plein_ecran(self):
        fenetre = pe.PleinEcranWindow(
            MyWindow)
        fenetre.exec()
        
   #Générer image avec segmentation     
    def generer_rendu_fusionne(self):
        """Crée une image fusionnant le fond d'œil et les calques de segmentation."""
        if self.item_fundus is None:
            return None

        # 1. Récupérer l'image de base (fundus)
        # On transforme le QPixmap en QImage pour manipuler les pixels
        image_finale = self.item_fundus.pixmap().toImage().convertToFormat(QtGui.QImage.Format_ARGB32)
        
        painter = QPainter(image_finale)
        # Définir le mode de composition pour que l'opacité soit respectée
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # 2. Liste des calques à superposer dans l'ordre
        calques = [
            (self.item_veins, "veines"),
            (self.item_arteries, "arteres"),
            (self.item_od, "disque")
        ]

        for item, key in calques:
            if item and item.opacity() > 0:
                # On récupère le pixmap du calque (qui est déjà coloré par votre fonction _recharger_masques)
                pix = item.pixmap()
                painter.setOpacity(item.opacity()) # On applique l'opacité choisie par l'utilisateur
                painter.drawPixmap(0, 0, pix)

        painter.end()
        return image_finale
    
       #----------------ACTION 9 : SAUVEGARDER-----------------
 
    def save(self):
        """Enregistre l'image originale et les masques dans segmentation_masks/sous_dossiers."""
        if not self.chemin_image:
            self.statusBar().showMessage("Aucune image à enregistrer.")
            return
        
        sauv_fichier, ok = QInputDialog.getText(self, 'Sauvegarde', 'Nom du projet :')
        if not ok or not sauv_fichier.strip(): 
            return
        
        folder_path = self.chemin_dossier
        if not folder_path: 
            return
        
        try:
            # 1. Dossier principal du projet (ex: Patient_01)
            dossier_projet = os.path.join(folder_path, sauv_fichier)
            
            # 2. Dossier parent pour les masques (ex: Patient_01/segmentation_masks)
            dossier_parent_masks = os.path.join(dossier_projet, "segmentation_masks")

            # 3. Liste des segmentations
            calques = [
                (self.item_veins, "veins"),
                (self.item_arteries, "arteries"),
                (self.item_od, "od")
            ]

            for item, nom in calques:
                if item is not None:
                    # On crée le sous-dossier DANS segmentation_masks
                    # ex: Patient_01/segmentation_masks/Veins/
                    sous_dossier = os.path.join(dossier_parent_masks, nom)
                    if not os.path.exists(sous_dossier):
                        os.makedirs(sous_dossier)
                    
                    # Enregistrement
                    image_calque = item.pixmap().toImage()
                    chemin_image = os.path.join(sous_dossier, f"{nom.lower()}.png")
                    image_calque.save(chemin_image)

            # 4. Dossier pour l'image originale
            dossier_orig = os.path.join(dossier_projet, "fundus_images")
            if not os.path.exists(dossier_orig):
                os.makedirs(dossier_orig)
            
            extension = os.path.splitext(self.chemin_image)[1]
            shutil.copy(self.chemin_image, os.path.join(dossier_orig, f"{sauv_fichier}.{extension}"))

            # 5. Rendu fusionné et Config JSON à la racine du projet
            image_fusionnee = self.generer_rendu_fusionne()
            if image_fusionnee:
                image_fusionnee.save(os.path.join(dossier_projet, f"{sauv_fichier}_rendu.png"))

            if self.segmentation_window:
                data_seg = self.segmentation_window.recup_image()
                import json
                with open(os.path.join(dossier_projet, "config_segmentation.json"), 'w', encoding='utf-8') as f:
                    json.dump(data_seg, f, indent=4)

            self.statusBar().showMessage(f"Sauvegarde terminée dans {sauv_fichier}")
            QMessageBox.information(self, "Succès", "Fichiers enregistrés avec succès.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur de sauvegarde : {str(e)}")
            
    #------------------ACTION 10 : REUNITIALISER ET SAUVEGARDER-----------------
    def reset(self):
        rep = QMessageBox.question(self, "Validation", 
            "Voulez-vous sauvegarder les précédentes modifications ?")

        if rep == QMessageBox.Yes:
            self.save()
            self.statusBar().showMessage("Configuration validée. Vous pouvez lancer la segmentation avant de définir les paramètres.")
        
        # Fermer les fenêtres dock si elles existent
        if self.segmentation_window is not None:
            self.segmentation_window.close()
            self.segmentation_window = None
        
        if self.toolbox is not None:
            self.toolbox.close()
            self.toolbox = None
            
        self.chemin_image          = None
        self.chemin_veines         = None
        self.chemin_arteres        = None
        self.chemin_disque         = None
        self.panel_active          = False
        self.affichage_double      = None
        self.od_valide             = False
        self.segmentation_terminee = False
        self.statusBar().showMessage("ETAPE 1 : Telecharger une image de fond d'oeil.")
        self.actSave.setEnabled(False)
        self.actOpacite.setEnabled(False)
        self.actEditerDisque.setEnabled(False)
        self.act_valider_od.setEnabled(False)
        self.act_run_seg.setEnabled(False)
        self.actPleinEcran.setEnabled(False)
        self.lbl_import.clear()
        self._init_panels()
        
    def modif_couleurs(self, key: str, color_modif: tuple):
        """Reçoit la nouvelle couleur depuis SegmentationToolbox."""
        # Met à jour la couleur de la couche concernée (on garde l'alpha à 255)
        r, g, b = color_modif[-3], color_modif[-2], color_modif[-1]
        self.couleurs[key] = (r, g, b, 255)

        # Recharge les masques avec les nouvelles couleurs
        self._recharger_masques()

    def _recharger_masques(self):
        if self.path_image_courante is None:
            return
        
        paths = images_paths(self.path_image_courante)
        image_originale, mask_veins, mask_arteries, mask_od = load_images(
            paths,
            couleur_veines=self.couleurs["veines"],
            couleur_arteres=self.couleurs["arteres"],
            couleur_disque=self.couleurs["disque"],
        )
        
        # ✅ Reconvertir en QPixmap et mettre à jour la scène
        pixmap_fundus, pixmap_veins, pixmap_arteries, pixmap_od = conversion_qpixmap(
            image_originale, mask_veins, mask_arteries, mask_od
        )
        self.item_veins.setPixmap(pixmap_veins)
        self.item_arteries.setPixmap(pixmap_arteries)
        self.item_od.setPixmap(pixmap_od)
        
        # Rafraîchis l'opacité
        self.segmentation_window.appliquer()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pixmap = QPixmap(":/OPV.png")
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()  
    app.setStyle("Fusion")
    win = MyWindow()
    win.show()
    splash.finish(win)
    sys.exit(app.exec())
