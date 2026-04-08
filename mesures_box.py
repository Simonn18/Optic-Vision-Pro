import os
from PySide6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QGroupBox, QCheckBox, QPushButton, QHBoxLayout, QMessageBox, QScrollArea, QFrame)
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
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 0;
        font-size: 13px;
        font-weight: bold;
        margin-top: 6px;
    }
    QPushButton { background: #4444bb; }
    QPushButton:disabled { background: #bbbbcc; color: #666666; }
    QPushButton {
        background: #e8e8f4;
        color: #666666;
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
        layout.addWidget(self._groupe(
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
        btn_tout.clicked.connect(self._update_lancer_btn)
        btn_rien.clicked.connect(self._update_lancer_btn)

        layout.addWidget(self._groupe("Zones", zone_cbs,
                                      extra_buttons=[btn_tout, btn_rien]))

        # Groupes d'actions
        self.cb_wpr        = QCheckBox("WPR")
        self.cb_vzr        = QCheckBox("VZR")
        self.cb_cal_diam   = QCheckBox("Calibre + diametre")
        self.cb_topologie  = QCheckBox("Topologie")
        self.cb_tortuosite = QCheckBox("Tortuosite")
        self.cb_pts_crit   = QCheckBox("Points critiques")
        groupes_cbs = [self.cb_wpr, self.cb_vzr, self.cb_cal_diam,
                       self.cb_topologie, self.cb_tortuosite, self.cb_pts_crit]
        btn_tout2 = QPushButton("Tout")
        btn_tout2.setObjectName("btn_tout")
        btn_rien2 = QPushButton("Rien")
        btn_rien2.setObjectName("btn_rien")
        btn_tout2.clicked.connect(lambda: [cb.setChecked(True)  for cb in groupes_cbs])
        btn_rien2.clicked.connect(lambda: [cb.setChecked(False) for cb in groupes_cbs])
        btn_tout2.clicked.connect(self._update_lancer_btn)
        btn_rien2.clicked.connect(self._update_lancer_btn)
        
        layout.addWidget(self._groupe(
            "Groupes d'actions",
            groupes_cbs, extra_buttons=[btn_tout2, btn_rien2]
        ))

        # Bouton Lancer
        self.btn_lancer = QPushButton("Lancer les mesures")
        self.btn_lancer.setObjectName("btn_lancer")
        self.btn_lancer.clicked.connect(self.lancer_mesures)
        layout.addWidget(self.btn_lancer)
        layout.addStretch()

    def _groupe(self, titre: str, checkboxes: list,
                extra_buttons: list = None) -> QGroupBox:
        box = QGroupBox(titre)
        vbox = QVBoxLayout(box)
        vbox.setSpacing(2)
        for cb in checkboxes:
            cb.stateChanged.connect(self._update_lancer_btn)
            vbox.addWidget(cb)
        if extra_buttons:
            row = QHBoxLayout()
            row.setContentsMargins(0, 4, 0, 0)
            for btn in extra_buttons:
                row.addWidget(btn)
            vbox.addLayout(row)
        return box

    def _all_checkboxes(self):
        return [
            self.cb_veines, self.cb_arteres, self.cb_les2,
            self.cb_zoneA, self.cb_zoneB, self.cb_zoneC, self.cb_zoneAll, self.cb_zoneOut,
            self.cb_wpr, self.cb_vzr, self.cb_cal_diam,
            self.cb_topologie, self.cb_tortuosite, self.cb_pts_crit,
        ]

    def _set_enabled(self, enabled: bool):
        for cb in self._all_checkboxes():
            cb.setEnabled(enabled)
        if not enabled:
            self.btn_lancer.setEnabled(False)

    def _update_lancer_btn(self):
        any_checked = any(cb.isChecked() for cb in self._all_checkboxes())
        self.btn_lancer.setEnabled(any_checked)

    def activer(self):
        """Appele quand la segmentation est validee."""
        self._set_enabled(True)
        self.show()

    def selections(self) -> tuple:
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
        if self.cb_wpr.isChecked():        groupes.append("WPR")
        if self.cb_vzr.isChecked():        groupes.append("VZR")
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
            self._afficher_terminal(resultat)
            
            return resultat
            
        
        except FileNotFoundError:
            QMessageBox.critical(self, "Erreur", "Le fichier data.json est introuvable dans le dossier.")

#fonction temporaire en vif pour afficher sur le terminal propre : 


    def _afficher_terminal(self, res):
            """Affiche les résultats dans le terminal de manière structurée (Clé = Valeur)."""

            print("\n" + "═"*60)

            if not res:
                print(" ⚠️  Aucune donnée ne correspond à la sélection.")
                return

            for organe, zones in res.items():
                # Titre de l'organe en gras/majuscule
                print(f"\nORGANE : {organe.upper()}")
                print(f"  " + "─"*30)

                for zone, groupes in zones.items():
                    print(f"ZONE {zone}")

                    for groupe, mesures in groupes.items():
                        # Affichage du nom du groupe (wpr, vzr, Calibre...)
                        print(f"   mesures : {groupe}:")

                        for cle, valeur in mesures.items():
                            if isinstance(valeur, (float, int)):
                                val_str = f"{valeur:.4f}"
                            else:
                                val_str = str(valeur)

                            print(f"      • {cle.ljust(35)} = {val_str}")
            
            print("\n" + "═"*60 + "\n")
        