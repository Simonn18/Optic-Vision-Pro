import os
from PySide6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QGroupBox,QCheckBox, 
                               QPushButton, QHBoxLayout, QMessageBox, QScrollArea, 
                               QFrame, QTreeWidget, QTreeWidgetItem,QFileDialog) 
from PySide6.QtCore import Qt
import read_csv as rc
import json


class MesuresToolbox(QDockWidget):
    """Panneau lateral avec les mesures sous forme de liste cochable."""

    TOOLBOX_STYLE = """
    QDockWidget::title {
        background: #3a3a4a;
        color: #ffffff;
        padding: 6px 10px;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    QGroupBox {
        font-weight: bold;
        font-size: 11px;
        color: #3a3a4a;
        border: 1px solid #c8c8d8;
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 6px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
        color: #5555aa;
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
        border: 1.5px solid #8888aa;
        border-radius: 3px;
        background: #ffffff;
    }
    QCheckBox::indicator:checked {
        background: #5555cc;
        border-color: #3333aa;
    }
    QCheckBox:disabled {
        color: #aaaaaa;
    }
    QCheckBox::indicator:disabled {
        border-color: #cccccc;
        background: #eeeeee;
    }
    QPushButton{
        background: #5555cc;
        border-radius: 6px;
        padding: 8px 0;
        font-size: 13px;
        font-weight: bold;
        margin-top: 6px;
    }
    QPushButton { background: #4444bb; }
    QPushButton:disabled { background: #bbbbcc; }
    QPushButton {
        background: #e8e8f4;
        color: #000000;
        border: 1px solid #c0c0d8;
        border-radius: 4px;
        padding: 3px 10px;
        font-size: 11px;
    }    """
    
    def __init__(self, parent=None):
        super().__init__("  MESURES", parent)
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

        # Organes
        self.cb_veines  = QCheckBox("Veines")
        self.cb_arteres = QCheckBox("Arteres")
        self.cb_les2    = QCheckBox("Arteres + Veines")
        layout.addWidget(self.groupe(
            "Type de vaisseaux",
            [self.cb_veines, self.cb_arteres, self.cb_les2]
        ))

        # Zones
        self.cb_zoneA   = QCheckBox("Zone A")
        self.cb_zoneB   = QCheckBox("Zone B")
        self.cb_zoneC   = QCheckBox("Zone C")
        self.cb_zoneAll = QCheckBox("Toutes les zones")
        self.cb_zoneOut = QCheckBox("Hors zones")
        zone_cbs = [self.cb_zoneA, self.cb_zoneB, self.cb_zoneC, self.cb_zoneAll, self.cb_zoneOut]

        btn_tout = QPushButton("Tout")
        btn_tout.setObjectName("btn_tout")
        btn_rien = QPushButton("Rien")
        btn_rien.setObjectName("btn_rien")
        btn_tout.clicked.connect(lambda: [cb.setChecked(True)  for cb in zone_cbs])
        btn_rien.clicked.connect(lambda: [cb.setChecked(False) for cb in zone_cbs])
        btn_tout.clicked.connect(self.update_lancer_btn)
        btn_rien.clicked.connect(self.update_lancer_btn)

        layout.addWidget(self.groupe("Zones", zone_cbs,
                                      extra_buttons=[btn_tout, btn_rien]))

        # Groupes d'actions
        self.cb_secteur       = QCheckBox("Secteurs")
        self.cb_cal_diam   = QCheckBox("Calibre + diametre")
        self.cb_topologie  = QCheckBox("Topologie")
        self.cb_tortuosite = QCheckBox("Tortuosite")
        self.cb_pts_crit   = QCheckBox("Points critiques")
        groupes_cbs = [self.cb_secteur, self.cb_cal_diam,
                       self.cb_topologie, self.cb_tortuosite, self.cb_pts_crit]
        btn_tout2 = QPushButton("Tout")
        btn_tout2.setObjectName("btn_tout")
        btn_rien2 = QPushButton("Rien")
        btn_rien2.setObjectName("btn_rien")
        btn_tout2.clicked.connect(lambda: [cb.setChecked(True)  for cb in groupes_cbs])
        btn_rien2.clicked.connect(lambda: [cb.setChecked(False) for cb in groupes_cbs])
        btn_tout2.clicked.connect(self.update_lancer_btn)
        btn_rien2.clicked.connect(self.update_lancer_btn)
        
        layout.addWidget(self.groupe(
            "Groupes d'actions",
            groupes_cbs, extra_buttons=[btn_tout2, btn_rien2]
        ))

        # Bouton Lancer
        self.btn_lancer = QPushButton("Afficher les mesures")
        self.btn_lancer.setObjectName("btn_lancer")
        self.btn_export = QPushButton("Exporter les mesures ")
        self.btn_export.setObjectName("btn_export")
        self.btn_export.clicked.connect(self.exporter_resultats)
        layout.addWidget(self.btn_export)

        self.btn_lancer.clicked.connect(self.lancer_mesures)
        layout.addWidget(self.btn_lancer)
        layout.addStretch()

        # --- ZONE D'AFFICHAGE DES RÉSULTATS ---
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Propriété", "Valeur"])
        self.tree.setColumnWidth(0, 160)
        self.tree.setMinimumHeight(250) 
        
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff;
                color: #222233;            
                border: 1px solid #c8c8d8;
                border-radius: 4px;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 3px;
                color: #222233;            
            }
            QTreeWidget::item:selected {
                background-color: #5555cc; 
                color: #ffffff;            
            }
            QHeaderView::section {
                background-color: #e8e8f4;
                color: #3333aa;            
                padding: 4px;
                font-weight: bold;
                border: none;
            }
        """)
        layout.addWidget(self.tree)

    def groupe(self, titre, checkboxes,
                extra_buttons = None) :
        box = QGroupBox(titre)
        vbox = QVBoxLayout(box)
        vbox.setSpacing(2)
        for cb in checkboxes:
            cb.stateChanged.connect(self.update_lancer_btn)
            vbox.addWidget(cb)
        if extra_buttons:
            row = QHBoxLayout()
            row.setContentsMargins(0, 4, 0, 0)
            for btn in extra_buttons:
                row.addWidget(btn)
            vbox.addLayout(row)
        return box

    def all_checkboxes(self):
        return [
            self.cb_veines, self.cb_arteres, self.cb_les2,
            self.cb_zoneA, self.cb_zoneB, self.cb_zoneC, self.cb_zoneAll, self.cb_zoneOut,
            self.cb_secteur, self.cb_cal_diam,
            self.cb_topologie, self.cb_tortuosite, self.cb_pts_crit,
        ]

    def set_enabled(self, enabled):
        for cb in self.all_checkboxes():
            cb.setEnabled(enabled)
        if not enabled:
            self.btn_lancer.setEnabled(False)

    def update_lancer_btn(self):
        any_checked = any(cb.isChecked() for cb in self.all_checkboxes())
        self.btn_lancer.setEnabled(any_checked)

    def activer(self):
        """Appele quand la segmentation est validee."""
        self.set_enabled(True)
        self.show()

    def selections(self) :
        """Retourne 3 listes avec les noms exacts du JSON."""
        vaisseaux = []
        if self.cb_veines.isChecked():  vaisseaux.append("Veins")
        if self.cb_arteres.isChecked(): vaisseaux.append("Arteries")
        if self.cb_les2.isChecked():    vaisseaux.append("AV")

        zones = []
        if self.cb_zoneA.isChecked():   zones.append("A")
        if self.cb_zoneB.isChecked():   zones.append("B")
        if self.cb_zoneC.isChecked():   zones.append("C")
        if self.cb_zoneAll.isChecked(): zones.append("All")
        if self.cb_zoneOut.isChecked(): zones.append("Out")

        groupes = []
        
        if self.cb_secteur.isChecked():    groupes.append("Secteurs")
        if self.cb_cal_diam.isChecked():   groupes.append("Calibre")
        if self.cb_topologie.isChecked():  groupes.append("Topologie")
        if self.cb_tortuosite.isChecked(): groupes.append("Tortuosite")
        if self.cb_pts_crit.isChecked():   groupes.append("Points_critiques")

        return vaisseaux, zones, groupes

    def lancer_mesures(self):

        vaisseaux, zones, groupes = self.selections()
        
        if not vaisseaux or not zones or not groupes:
            QMessageBox.warning(self, "Sélection incomplète", 
                                "Cochez au moins un élément dans chaque groupe.")
            return


        try:
            with open('data.json', 'r') as f:
                data_test = json.load(f)
            
            resultat = rc.requete(data_test, organe=vaisseaux, zone=zones, groupe=groupes)
            QMessageBox.information(self, "Succès","Les mesures ont été enregistées dans votre dossier")

            print("--- DONNÉES FILTRÉES ---")
            if resultat:
                self.remplir_interface(resultat)
            
            return resultat
            
        
        except FileNotFoundError:
            QMessageBox.critical(self, "Erreur", "Le fichier data.json est introuvable dans le dossier.")


            
    
        
    def remplir_interface(self, data):
        """Remplit le QTreeWidget avec les données filtrées."""
        self.tree.clear()
        
        for organe, zones in data.items():
            # Branche Organe (ARTERIES / VEINS)
            item_organe = QTreeWidgetItem(self.tree, [organe.upper()])
            
            for zone, groupes in zones.items():
                # Branche Zone (Zone A, B...)
                item_zone = QTreeWidgetItem(item_organe, [f"Zone {zone}"])
                
                for groupe, mesures in groupes.items():
                    # Branche Groupe (Calibre, Secteurs...)
                    item_groupe = QTreeWidgetItem(item_zone, [groupe])
                    
                    if isinstance(mesures, dict):
                        for mesure, valeur in mesures.items():
                            # Gestion spécifique pour les sous-secteurs wpr/vzr
                            if isinstance(valeur, dict): 
                                item_sub = QTreeWidgetItem(item_groupe, [mesure])
                                for sub_m, sub_v in valeur.items():
                                    v_str = f"{sub_v}" if isinstance(sub_v, float) else str(sub_v)
                                    QTreeWidgetItem(item_sub, [sub_m, v_str])
                            else:
                                v_str = f"{valeur}" if isinstance(valeur, float) else str(valeur)
                                QTreeWidgetItem(item_groupe, [mesure, v_str])
        
        self.tree.expandAll()

    def exporter_resultats(self):
        vaisseaux, zones, groupes = self.selections()
        
        try:
            with open('data.json', 'r') as f:
                data_test = json.load(f)
            
            resultat = rc.requete(data_test, organe=vaisseaux, zone=zones, groupe=groupes)
            
            if not resultat:
                QMessageBox.warning(self, "Export impossible", "Aucune donnée à exporter. Lancez d'abord une mesure.")
                return

            # Fenêtre de dialogue pour choisir l'emplacement
            chemin_save, _ = QFileDialog.getSaveFileName(
                self, "Enregistrer le rapport", "rapport_mesures.txt", "Fichiers Texte (*.txt)"
            )

            if chemin_save:
                rc.export_txt(resultat, chemin_save)
                QMessageBox.information(self, "Export réussi", f"Le rapport a été enregistré ici :\n{chemin_save}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur Export", f"Une erreur est survenue : {str(e)}")
