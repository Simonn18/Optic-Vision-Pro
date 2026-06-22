# langue.py — Gestion multilingue pour Optic Vision Pro
# Langues supportées : "fr" (Français), "en" (English)

TEXTES = {

    # ──────────────────────────────────────────────
    # Barre haute (topbar)
    # ──────────────────────────────────────────────
    "titre_app": {
        "fr": "OPTIC VISION PRO",
        "en": "OPTIC VISION PRO",
    },
    "btn_dossier_travail": {
        "fr": "Ouvrir un dossier de travail",
        "en": "Open a working folder",
    },
    "btn_help":{
        "fr": "Aide",
        "en": "Help",
    },
    "btn_dossier_images": {
        "fr": "Ouvrir un dossier d'images",
        "en": "Open an image folder",
    },
    "lbl_aucun_dossier": {
        "fr": "Aucun dossier chargé",
        "en": "No folder loaded",
    },

    # ──────────────────────────────────────────────
    # Page d'accueil
    # ──────────────────────────────────────────────
    "btn_pretraitement": {
        "fr": "PRÉ-TRAITEMENT",
        "en": "PRE-PROCESSING",
    },
    "btn_traitement": {
        "fr": "TRAITEMENT D'IMAGE",
        "en": "IMAGE PROCESSING",
    },
    "btn_langue": {
        "fr": "English",   # affiché quand la langue est français → propose de passer en anglais
        "en": "Français",  # affiché quand la langue est anglais  → propose de passer en français
    },
    "btn_aide": {
        "fr": "Aide",
        "en": "Help",
    },

    # ──────────────────────────────────────────────
    # Barre d'actions (actionbar)
    # ──────────────────────────────────────────────
    "btn_precedent": {
        "fr": "◀ Précédent",
        "en": "◀ Previous",
    },
    "btn_suivant": {
        "fr": "Suivant ▶",
        "en": "Next ▶",
    },
    "btn_sauvegarder": {
        "fr": "Sauvegarder",
        "en": "Save",
    },
    "btn_sauvegarder_tout": {
        "fr": "Sauvegarder toutes les images",
        "en": "Save all images",
    },
    "lbl_image_num": {
        "fr": "Image {n}/{total}",
        "en": "Image {n}/{total}",
    },

    # ──────────────────────────────────────────────
    # Barre de statut
    # ──────────────────────────────────────────────
    "status_etape1": {
        "fr": "ÉTAPE 1 : Charger ou créer un dossier de travail.",
        "en": "STEP 1: Load or create a working folder.",
    },
    "status_calcul": {
        "fr": "Calcul global en cours, veuillez patienter…",
        "en": "Running global calculation, please wait…",
    },
    "status_mesures_terminees": {
        "fr": "Mesures terminées pour {nom}.",
        "en": "Measurements done for {nom}.",
    },
    "status_mesures_chargees": {
        "fr": "Mesures chargées depuis l'archive projet.",
        "en": "Measurements loaded from project archive.",
    },
    "status_mesures_chargees_global": {
        "fr": "Mesures chargées depuis l'archive globale.",
        "en": "Measurements loaded from global archive.",
    },
    "status_chargement_mesures": {
        "fr": "Chargement des mesures existantes…",
        "en": "Loading existing measurements…",
    },
    "status_aucune_image": {
        "fr": "Aucun dossier de travail sélectionné.",
        "en": "No working folder selected.",
    },
    "status_sauvegarde": {
        "fr": "Image sauvegardée.",
        "en": "Image saved.",
    },
    "status_n_images": {
        "fr": "{n} images sauvegardées.",
        "en": "{n} images saved.",
    },
    "status_maj_reglages": {
        "fr": "Réglages mis à jour avec succès.",
        "en": "Settings updated successfully.",
    },

    # ──────────────────────────────────────────────
    # Dialogues / QMessageBox — dossier de travail
    # ──────────────────────────────────────────────
    "dlg_dossier_titre": {
        "fr": "Dossier chargé",
        "en": "Folder loaded",
    },
    "dlg_dossier_texte": {
        "fr": "Dossier '{nom}' chargé avec succès.",
        "en": "Folder '{nom}' loaded successfully.",
    },
    "dlg_dossier_erreur_titre": {
        "fr": "Erreur",
        "en": "Error",
    },
    "dlg_dossier_erreur_texte": {
        "fr": "Aucun dossier sélectionné.",
        "en": "No folder selected.",
    },

    # ──────────────────────────────────────────────
    # Dialogues — sauvegarde
    # ──────────────────────────────────────────────
    "dlg_save_titre": {
        "fr": "Sauvegarde",
        "en": "Save",
    },
    "dlg_save_config_existe": {
        "fr": "Un fichier de configuration existe déjà.",
        "en": "A configuration file already exists.",
    },
    "dlg_save_config_info": {
        "fr": "Voulez-vous mettre à jour les réglages ou créer un nouveau projet ?",
        "en": "Do you want to update the settings or create a new project?",
    },
    "dlg_save_btn_maj": {
        "fr": "Mettre à jour",
        "en": "Update",
    },
    "dlg_save_btn_nouveau": {
        "fr": "Nouveau projet",
        "en": "New project",
    },
    "dlg_save_btn_annuler": {
        "fr": "Annuler",
        "en": "Cancel",
    },
    "dlg_save_succes_titre": {
        "fr": "Succès",
        "en": "Success",
    },
    "dlg_save_succes_texte": {
        "fr": "Image sauvegardée :\n{chemin}",
        "en": "Image saved:\n{chemin}",
    },
    "dlg_save_erreur_titre": {
        "fr": "Erreur",
        "en": "Error",
    },
    "dlg_save_erreur_texte": {
        "fr": "Erreur de sauvegarde : {erreur}",
        "en": "Save error: {erreur}",
    },
    "dlg_save_aucun_dossier": {
        "fr": "Aucun dossier de travail défini. Veuillez d'abord ouvrir un dossier de travail.",
        "en": "No working folder defined. Please open a working folder first.",
    },

    # ──────────────────────────────────────────────
    # Dialogues — sauvegarde de toutes les images
    # ──────────────────────────────────────────────
    "dlg_save_all_titre": {
        "fr": "Sauvegarde des images",
        "en": "Save images",
    },
    "dlg_save_all_texte": {
        "fr": "Voulez-vous un dossier par image (1) ou un dossier pour toutes les images (2) ?",
        "en": "Do you want one folder per image (1) or one folder for all images (2)?",
    },
    "dlg_save_all_btn1": {
        "fr": "1 ",
        "en": "1 ",
    },
    "dlg_save_all_btn2": {
        "fr": "2 ",
        "en": "2",
    },
    "dlg_rendus_titre": {
        "fr": "Rendus finaux",
        "en": "Final renderings",
    },
    "dlg_rendus_texte": {
        "fr": "Voulez-vous exporter tous les rendus ou seulement les images modifiées ?",
        "en": "Do you want to export all renderings or only modified images?",
    },
    "dlg_rendus_btn_tous": {
        "fr": "Tous",
        "en": "All",
    },
    "dlg_rendus_btn_modif": {
        "fr": "Modifiées",
        "en": "Modified",
    },
    "dlg_save_all_succes": {
        "fr": "{n} images sauvegardées dans :\n{chemin}",
        "en": "{n} images saved in:\n{chemin}",
    },
    "dlg_save_all_partiel": {
        "fr": "{ok}/{total} images sauvegardées.\n\nErreurs :\n{erreurs}",
        "en": "{ok}/{total} images saved.\n\nErrors:\n{erreurs}",
    },

    # ──────────────────────────────────────────────
    # Toolbox de segmentation (segmentation3.py)
    # ──────────────────────────────────────────────
    "seg_titre": {
        "fr": "  SEGMENTATION",
        "en": "  SEGMENTATION",
    },
    "seg_groupe_couches": {
        "fr": "Couches disponibles",
        "en": "Available layers",
    },
    "seg_cb_veines": {
        "fr": "Veines",
        "en": "Veins",
    },
    "seg_cb_arteres": {
        "fr": "Artères",
        "en": "Arteries",
    },
    "seg_cb_disque": {
        "fr": "Disque optique",
        "en": "Optic disc",
    },
    "seg_btn_creer_disque": {
        "fr": "Créer un disque",
        "en": "Create a disc",
    },
    "seg_btn_editer": {
        "fr": "Éditer le disque",
        "en": "Edit the disc",
    },
    "seg_btn_valider": {
        "fr": "Valider les disques",
        "en": "Validate the disks",
    },
    "seg_btn_lancer": {
        "fr": "Lancer les mesures",
        "en": "Run measurements",
    },
    "seg_btn_afficher_zones": {
        "fr": "Afficher les zones d'intérêt",
        "en": "Show areas of interest",
    },
    "btn_maj_rendu": {
        "fr": "Sauvegarder les rendus",
        "en": "Save renderings",
    },
    "btn_selection_activer": {
        "fr": "Sélection",
        "en": "Selection",
    },
    "btn_selection_quitter": {
        "fr": "Quitter sélection",
        "en": "Exit selection",
    },
    "btn_sauvegarder_n": {
        "fr": "Sauvegarder ({n})",
        "en": "Save ({n})",
    },

    # ──────────────────────────────────────────────
    # Dialogues — sauvegarder_rendus
    # ──────────────────────────────────────────────
    "dlg_rendus_maj_titre": {
        "fr": "Rendus finaux",
        "en": "Final renderings",
    },
    "dlg_rendus_maj_texte": {
        "fr": "Voulez-vous mettre à jour le dossier de rendus ?",
        "en": "Do you want to update the renderings folder?",
    },
    "dlg_rendus_choix_texte": {
        "fr": "Voulez-vous enregistrer tous les rendus du dossier ou seulement les retravaillés ?",
        "en": "Do you want to save all renderings or only the reworked ones?",
    },
    "dlg_rendus_btn_tous": {
        "fr": "Tous",
        "en": "All",
    },
    "dlg_rendus_btn_retravailles": {
        "fr": "Retravaillés",
        "en": "Reworked",
    },
    "dlg_rendus_btn_oui": {
        "fr": "Oui",
        "en": "Yes",
    },
    "dlg_rendus_btn_non": {
        "fr": "Non",
        "en": "No",
    },
    "dlg_rendus_succes_retrav": {
        "fr": "Les rendus retravaillés ont été mis à jour.",
        "en": "Reworked renderings have been updated.",
    },
    "dlg_rendus_succes_tous": {
        "fr": "{n} rendus ont été mis à jour.",
        "en": "{n} renderings have been updated.",
    },
    "dlg_rendus_partiel": {
        "fr": "{ok}/{total} rendus sauvegardés.\n\nErreurs :\n{erreurs}",
        "en": "{ok}/{total} renderings saved.\n\nErrors:\n{erreurs}",
    },
    "status_rendu_progress": {
        "fr": "Rendu {i}/{n} — {nom}…",
        "en": "Rendering {i}/{n} — {nom}…",
    },

    # ──────────────────────────────────────────────
    # Dialogues — disque optique
    # ──────────────────────────────────────────────
    "dlg_disque_titre": {
        "fr": "Sauvegarde",
        "en": "Save",
    },
    "dlg_disque_texte": {
        "fr": "Sauvegarder le nouveau disque.",
        "en": "Save the new disc.",
    },
    "dlg_disque_info": {
        "fr": "Voulez-vous mettre à jour l'emplacement du disque optique ?",
        "en": "Do you want to update the optic disc position?",
    },
    "dlg_disque_btn_oui": {
        "fr": "Oui",
        "en": "Yes",
    },
    "dlg_disque_btn_non": {
        "fr": "Non",
        "en": "No",
    },

    # ──────────────────────────────────────────────
    # Dialogues — _check_config_existante
    # ──────────────────────────────────────────────
    "dlg_config_existe_info": {
        "fr": "Voulez-vous mettre à jour les réglages ou créer un nouveau projet ?",
        "en": "Do you want to update the settings or create a new project?",
    },

    # ──────────────────────────────────────────────
    # Dialogues — _save_groupe / QInputDialog
    # ──────────────────────────────────────────────
    "dlg_save_groupe_titre": {
        "fr": "Sauvegarde",
        "en": "Save",
    },
    "dlg_save_groupe_nom": {
        "fr": "Nom du nouveau projet :",
        "en": "New project name:",
    },
    "dlg_save_groupe_texte": {
        "fr": "Un dossier par image (1) ou un dossier pour toutes les images (2) ?",
        "en": "One folder per image (1) or one folder for all images (2)?",
    },
    "dlg_save_groupe_btn1": {
        "fr": "1",
        "en": "1",
    },
    "dlg_save_groupe_btn2": {
        "fr": "2",
        "en": "2",
    },

    # ──────────────────────────────────────────────
    # Boutons mode sélection
    # ──────────────────────────────────────────────
    "btn_selection_quitter": {
        "fr": "Quitter",
        "en": "Exit",
    },
    "btn_selection_activer": {
        "fr": "Sélection",
        "en": "Select",
    },
    "btn_sauvegarder_n": {
        "fr": "Sauvegarder ({n})",
        "en": "Save ({n})",
    },

    # ──────────────────────────────────────────────
    # Messages de statut supplémentaires
    # ──────────────────────────────────────────────
    "status_aucune_image_a_enregistrer": {
        "fr": "Aucune image à enregistrer.",
        "en": "No image to save.",
    },
    "status_aucune_image_chargee": {
        "fr": "Aucune image chargée.",
        "en": "No image loaded.",
    },
    "status_sauvegarde_progress": {
        "fr": "Sauvegarde {i}/{n} — {nom}…",
        "en": "Saving {i}/{n} — {nom}…",
    },
    "status_projet_enregistre": {
        "fr": "Projet « {nom} » enregistré.",
        "en": "Project « {nom} » saved.",
    },
    "status_erreur_calcul": {
        "fr": "Une erreur est survenue lors du calcul.",
        "en": "An error occurred during calculation.",
    },
    "dlg_save_projet_succes": {
        "fr": "Projet créé :\n{chemin}",
        "en": "Project created:\n{chemin}",
    },
    "dlg_selection_vide_titre": {
        "fr": "Sélection vide",
        "en": "Empty selection",
    },
    "dlg_selection_vide_texte": {
        "fr": "Aucune image sélectionnée.\nCliquez sur des miniatures pour en cocher.",
        "en": "No image selected.\nClick on thumbnails to check them.",
    },
    "dlg_save_all_btn_par_image": {
        "fr": "1 — Un dossier par image",
        "en": "1 — One folder per image",
    },
    "dlg_save_all_btn_global": {
        "fr": "2 — Tout dans un dossier",
        "en": "2 — All in one folder",
    },

    "seg_groupe_couleurs": {
        "fr": "Modifier les couleurs",
        "en": "Change colours",
    },
    "seg_btn_couleur_veines": {
        "fr": "Couleur des veines",
        "en": "Vein colour",
    },
    "seg_btn_couleur_arteres": {
        "fr": "Couleur des artères",
        "en": "Artery colour",
    },
    "seg_btn_couleur_disque": {
        "fr": "Couleur du disque optique",
        "en": "Optic disc colour",
    },
    "seg_btn_couleur_superposition": {
        "fr": "Couleur des superpositions",
        "en": "Overlap colour",
    },
    "seg_opacite_image": {
        "fr": "Opacité image",
        "en": "Image opacity",
    },
    "seg_opacite_veines": {
        "fr": "Opacité veines",
        "en": "Veins opacity",
    },
    "seg_opacite_arteres": {
        "fr": "Opacité artères",
        "en": "Arteries opacity",
    },
    "seg_opacite_disque": {
        "fr": "Opacité disque",
        "en": "Disc opacity",
    },
    "seg_groupe_rendus": {
        "fr": "Rendus du dossier d'images",
        "en": "Image folder renderings",
    },
    "seg_dlg_valider_titre": {
        "fr": "Valider le disque optique",
        "en": "Validate the optic disc",
    },
    "seg_dlg_valider_texte": {
        "fr": "Validation du disque optique",
        "en": "Optic disc validation",
    },
    "seg_dlg_valider_info": {
        "fr": "Êtes-vous sûr de vouloir valider le disque optique ?",
        "en": "Are you sure you want to validate the optic disc?",
    },
    "seg_dlg_valider_oui": {
        "fr": "Oui",
        "en": "Yes",
    },
    "seg_dlg_valider_non": {
        "fr": "Non",
        "en": "No",
    },
    "seg_couleur_veines_titre": {
        "fr": "Choisir la couleur des veines",
        "en": "Choose vein colour",
    },
    "seg_couleur_arteres_titre": {
        "fr": "Choisir la couleur des artères",
        "en": "Choose artery colour",
    },
    "seg_couleur_disque_titre": {
        "fr": "Choisir la couleur du disque optique",
        "en": "Choose optic disc colour",
    },
    "seg_couleur_superposition_titre": {
        "fr": "Choisir la couleur des superpositions artères/veines",
        "en": "Choose artery/vein overlap colour",
    },

    # ──────────────────────────────────────────────
    # Boîte à outils des mesures (mesures_box.py)
    # ──────────────────────────────────────────────
    "mes_titre": {
        "fr": "  MESURES",
        "en": "  MEASUREMENTS",
    },
    "mes_groupe_vaisseaux": {
        "fr": "Type de vaisseaux",
        "en": "Vessel type",
    },
    "mes_cb_veines": {
        "fr": "Veines",
        "en": "Veins",
    },
    "mes_cb_arteres": {
        "fr": "Artères",
        "en": "Arteries",
    },
    "mes_cb_les2": {
        "fr": "Artères + Veines",
        "en": "Arteries + Veins",
    },
    "mes_groupe_zones": {
        "fr": "Zones",
        "en": "Zones",
    },
    "mes_cb_zoneAll": {
        "fr": "All",
        "en": "All",
    },
    "mes_cb_zoneOut": {
        "fr": "Out",
        "en": "Out",
    },
    "mes_btn_tout": {
        "fr": "Tout",
        "en": "All",
    },
    "mes_btn_rien": {
        "fr": "Rien",
        "en": "None",
    },
    "mes_groupe_actions": {
        "fr": "Groupes de mesures",
        "en": "Measure groups",
    },
    "mes_cb_quality": {
        "fr": "Contrôle qualité",
        "en": "Quality control",
    },
    "mes_cb_vessel": {
        "fr": "Détection vaisseaux",
        "en": "Vessel detection",
    },
    "mes_cb_geo": {
        "fr": "Métriques géométriques",
        "en": "Geometric metrics",
    },
    "mes_btn_afficher": {
        "fr": "Afficher les mesures",
        "en": "Display measurements",
    },
    "mes_btn_exporter": {
        "fr": "Exporter les mesures",
        "en": "Export measurements",
    },
    "mes_dlg_incomplete_titre": {
        "fr": "Sélection incomplète",
        "en": "Incomplete selection",
    },
    "mes_dlg_incomplete_texte": {
        "fr": "Cochez au moins un élément dans chaque groupe.",
        "en": "Check at least one item in each group.",
    },
    "mes_dlg_aucune_mesure_titre": {
        "fr": "Erreur",
        "en": "Error",
    },
    "mes_dlg_aucune_mesure_texte": {
        "fr": "Aucune mesure disponible pour cette image.\nLancez d'abord les mesures.",
        "en": "No measurements available for this image.\nPlease run measurements first.",
    },
    "mes_tree_image": {
        "fr": "IMAGE ANALYSÉE",
        "en": "ANALYSED IMAGE",
    },
    "mes_tree_col_prop": {
        "fr": "Propriété",
        "en": "Property",
    },
    "mes_tree_col_val": {
        "fr": "Valeur",
        "en": "Value",
    },
    "mes_export_titre": {
        "fr": "Enregistrer le rapport",
        "en": "Save report",
    },
    "mes_export_filtre": {
        "fr": "Fichiers Texte (*.txt)",
        "en": "Text Files (*.txt)",
    },
    "mes_export_succes_titre": {
        "fr": "Export réussi",
        "en": "Export successful",
    },
    "mes_export_succes_texte": {
        "fr": "Le rapport a été enregistré ici :\n{chemin}",
        "en": "The report has been saved here:\n{chemin}",
    },
    "mes_export_impossible_titre": {
        "fr": "Export impossible",
        "en": "Export failed",
    },
    "mes_export_impossible_texte": {
        "fr": "Aucune donnée à exporter. Lancez d'abord une mesure.",
        "en": "No data to export. Please run a measurement first.",
    },
    "mes_dlg_export_titre": {
        "fr": "Export des mesures",
        "en": "Measurements export",
    },
    "mes_dlg_export_texte": {
        "fr": "Que voulez-vous exporter ?",
        "en": "What do you want to export?",
    },
    "mes_dlg_export_btn_cette": {
        "fr": "Cette image",
        "en": "This image",
    },
    "mes_dlg_export_btn_toutes": {
        "fr": "Toutes les images",
        "en": "All images",
    },
    "mes_export_succes_toutes_texte": {
        "fr": "Rapport de toutes les images enregistré :\n{chemin}",
        "en": "Report for all images saved:\n{chemin}",
    },

    # ──────────────────────────────────────────────
    # Placeholder central
    # ──────────────────────────────────────────────
    "placeholder": {
        "fr": "Ouvrez un dossier pour afficher les images",
        "en": "Open a folder to display images",
    },
    "aucune_image_strip": {
        "fr": "Aucune image trouvée dans ce dossier",
        "en": "No images found in this folder",
    },
    "img_n_sur_total": {
        "fr": "{n} image{s} — {dossier}",
        "en": "{n} image{s} — {dossier}",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Fonction principale
# ──────────────────────────────────────────────────────────────────────────────

def changement_langue(langue: str) -> dict:
    """
    Retourne un dictionnaire {clé: texte} pour la langue demandée.

    Paramètres
    ----------
    langue : str
        Code de langue : "fr" pour Français, "en" pour English.
        Toute valeur non reconnue est traitée comme "fr".

    Retourne
    --------
    dict
        Dictionnaire plat {clé_texte: chaîne_localisée} prêt à l'emploi
        dans l'interface.

    Exemple
    -------
    >>> T = changement_langue("en")
    >>> print(T["btn_sauvegarder"])          # "Save"
    >>> print(T["seg_cb_veines"])             # "Veins"
    >>> print(T["lbl_image_num"].format(n=3, total=10))  # "Image 3/10"
    """
    if langue not in ("fr", "en"):
        langue = "fr"

    return {cle: valeurs[langue] for cle, valeurs in TEXTES.items()}


# ──────────────────────────────────────────────────────────────────────────────
# Langue par défaut au démarrage
# ──────────────────────────────────────────────────────────────────────────────

LANGUE_DEFAUT = "fr"