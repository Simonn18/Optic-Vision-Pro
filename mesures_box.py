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
    }
    
    /* --- STYLE ALIGNÉ SUR LES COMPOSANTS DE CONTRÔLE (OPACITÉ) --- */
    QScrollBar:vertical {
        border: none;
        background: #2e2e3a;          /* Fond sombre identique aux boîtes d'outils */
        width: 8px;                   /* Très fin et minimaliste */
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #ffffff;          /* La poignée reste blanche */
        min-height: 30px;
        border-radius: 4px;           /* Coins bien arrondis */
    }
    QScrollBar::handle:vertical:hover {
        background: #e0e0e0;          /* Devient gris très clair au survol */
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;             /* Pas de flèches */
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    """
    
    def __init__(self, parent=None):
        super().__init__("  MESURES", parent)
        self.chemin_json_courant = None
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
        self.cb_zoneAll = QCheckBox("All")
        self.cb_zoneOut = QCheckBox("Out")
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
        self.cb_quality      = QCheckBox("quality control")
        self.cb_vessel   = QCheckBox("vessel detection")
        self.cb_geo  = QCheckBox("geometric metrics")

        groupes_cbs = [self.cb_quality, self.cb_vessel,
                       self.cb_geo]
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
            self.cb_quality, self.cb_vessel,
            self.cb_geo
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
        
        if self.cb_quality.isChecked():    groupes.append("quality control")
        if self.cb_vessel.isChecked():   groupes.append("vessel detection")
        if self.cb_geo.isChecked():  groupes.append("geometric metrics")

        return vaisseaux, zones, groupes

    def lancer_mesures(self):
        vaisseaux, zones, groupes = self.selections()

        if not vaisseaux or not zones or not groupes:
            QMessageBox.warning(self, "Sélection incomplète",
                                "Cochez au moins un élément dans chaque groupe.")
            return

            print(f"[DEBUG] chemin_json_courant = {self.chemin_json_courant}")
            print(f"[DEBUG] existe = {os.path.exists(self.chemin_json_courant) if self.chemin_json_courant else 'N/A'}")
            if not self.chemin_json_courant or not os.path.exists(self.chemin_json_courant):           
                QMessageBox.critical(self, "Erreur",
                "Aucune mesure disponible pour cette image.\n"
                "Lancez d'abord les mesures.")
            return


        
        try :    
            with open(self.chemin_json_courant, 'r', encoding='utf-8') as f:
                data_test = json.load(f)


                resultat = rc.requete(data_test, organe=vaisseaux, zone=zones, groupe=groupes)



            if resultat:
                self.remplir_interface(resultat)

        except Exception as e:
             QMessageBox.critical(self, "Erreur", f"Erreur : {str(e)}")
    
    def appliquer_langue(self, T: dict):
        """Met à jour tous les textes de la toolbox mesures."""
        self.setWindowTitle(T["mes_titre"])
 
        self.cb_veines.setText(T["mes_cb_veines"])
        self.cb_arteres.setText(T["mes_cb_arteres"])
        self.cb_les2.setText(T["mes_cb_les2"])
 
        self.cb_quality.setText(T["mes_cb_quality"])
        self.cb_vessel.setText(T["mes_cb_vessel"])
        self.cb_geo.setText(T["mes_cb_geo"])
 
        self.btn_lancer.setText(T["mes_btn_afficher"])
        self.btn_export.setText(T["mes_btn_exporter"])
 
        self.tree.setHeaderLabels([T["mes_tree_col_prop"], T["mes_tree_col_val"]])

        
    def remplir_interface(self, data):
        """Remplit le QTreeWidget avec les données filtrées."""
        if not isinstance(data, dict):
            print("Erreur : remplir_interface a reçu des données invalides.")
            return

        self.tree.clear()

        image_id = data.get("IMAGE_ID", "Inconnue")
        QTreeWidgetItem(self.tree, ["IMAGE ANALYSÉE", str(image_id)])
        
        for organe, zones in data.items():
            if organe == "IMAGE_ID" or not isinstance(zones, dict):
                continue
            
            item_organe = QTreeWidgetItem(self.tree, [organe.upper()])
            
            for zone, groupes in zones.items():
                if not isinstance(groupes, dict): continue
                
                item_zone = QTreeWidgetItem(item_organe, [f"Zone {zone}"])
                
                for groupe, mesures in groupes.items():
                    item_groupe = QTreeWidgetItem(item_zone, [groupe])
                    
                    if isinstance(mesures, dict):
                        for mesure, valeur in mesures.items():
                            if isinstance(valeur, dict):
                                item_sub = QTreeWidgetItem(item_groupe, [mesure])
                                for sub_m, sub_v in valeur.items():
                                    v_str = f"{sub_v:.2f}" if isinstance(sub_v, float) else str(sub_v)
                                    QTreeWidgetItem(item_sub, [sub_m, v_str])
                            else:
                                v_str = f"{valeur:.2f}" if isinstance(valeur, float) else str(valeur)
                                QTreeWidgetItem(item_groupe, [mesure, v_str])
        
        self.tree.expandAll()

    def exporter_resultats(self):
        vaisseaux, zones, groupes = self.selections()

        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Export des mesures")
        msgBox.setText("Que voulez-vous exporter ?")
        btn_cette = msgBox.addButton("Cette image", QMessageBox.ActionRole)
        btn_toutes = msgBox.addButton("Toutes les images", QMessageBox.ActionRole)
        msgBox.addButton(QMessageBox.Cancel)
        msgBox.exec()

        if msgBox.clickedButton() not in (btn_cette, btn_toutes):
            return

        chemin_save, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le rapport", "rapport_mesures.txt", "Fichiers Texte (*.txt)"
        )
        if not chemin_save:
            return

        if msgBox.clickedButton() == btn_cette:
            # Export image courante uniquement
            if not self.chemin_json_courant or not os.path.exists(self.chemin_json_courant):
                QMessageBox.warning(self, "Erreur", "Aucune mesure disponible pour cette image.")
                return
            try:
                with open(self.chemin_json_courant, 'r', encoding='utf-8') as f:
                    data_test = json.load(f)
                resultat = rc.requete(data_test, organe=vaisseaux, zone=zones, groupe=groupes)
                if resultat:
                    rc.export_txt(resultat, chemin_save)
                    QMessageBox.information(self, "Export réussi", f"Rapport enregistré :\n{chemin_save}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur : {str(e)}")

        else:
            dossier_json = os.path.dirname(self.chemin_json_courant)
            if not os.path.exists(dossier_json):
                QMessageBox.warning(self, "Erreur", "Dossier des mesures introuvable.")
                return

            try:
                with open(chemin_save, "w", encoding="utf-8") as f_out:
                    for nom_fichier in sorted(os.listdir(dossier_json)):
                        if not nom_fichier.endswith("_data.json"):
                            continue
                        chemin_json = os.path.join(dossier_json, nom_fichier)
                        with open(chemin_json, 'r', encoding='utf-8') as f:
                            data_test = json.load(f)
                        resultat = rc.requete(data_test, organe=vaisseaux, zone=zones, groupe=groupes)
                        if resultat:
                            import tempfile
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                                            delete=False, encoding='utf-8') as tmp:
                                tmp_path = tmp.name
                            rc.export_txt(resultat, tmp_path)
                            with open(tmp_path, 'r', encoding='utf-8') as tmp_f:
                                f_out.write(tmp_f.read())
                                f_out.write("\n")
                            os.remove(tmp_path)

                QMessageBox.information(self, "Export réussi",
                    f"Rapport de toutes les images enregistré :\n{chemin_save}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur : {str(e)}")
