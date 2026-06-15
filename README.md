# Optic Vision Pro (OVP)

Interface de visualisation d'images de fond d'œil et de leurs segmentations associées, développée en Python avec PySide6.

Projet réalisé dans le cadre du Master Bio-informatique de l'Université de Bordeaux.

---

## Fonctionnalités

- Chargement automatique d'une image de fond d'œil et de ses trois masques de segmentation (veines, artères, disque optique)
- Superposition des masques avec réglage indépendant de l'opacité et de la couleur pour chaque couche
- Navigation en mosaïque sur un lot d'images
- Création et édition manuelle du disque optique (glisser-déposer)
- Calcul et affichage des mesures anatomiques par zone et par type de vaisseau
- Export des résultats (images fusionnées, mesures au format CSV/JSON/TXT)
- Sauvegarde des réglages de session (opacités, couleurs) par image

---

## Visuels

Page d'accueil de l'interface  
![Page principale](example_images/Ecran_accueil.png)

Interface de traitement avec superposition des segmentations  
![Exemple de visualisation](example_images/acueille-segm.png)

Visualisation de plusieurs images en mosaïque
![Exemple de visualisation multiple](example_images/mosaique.png)

Choix des catégories de mesures
![Arbrorescence permettant le choix de métriques d'intérêt](example_images/Amesure.png)

---

## Prérequis

- Python **3.10** ou supérieur
- Les dépendances listées dans `requirements.txt`

---

## Installation

**1. Cloner le dépôt**

```bash
git clone <url-du-depot>
cd optic-vision-pro
```

**2. (Recommandé) Créer un environnement virtuel**

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

**3. Installer les dépendances**

```bash
pip install -r requirements.txt
```

---

## Lancer l'application

```bash
python newapp.py
```

> `newapp.py` est le point d'entrée principal de la version actuelle de l'application.  
> `main.py` correspond à une version antérieure toujours fonctionnelle.

---

## Structure des données attendue

L'application repose sur une organisation de dossiers précise. Pour qu'une image et ses segmentations soient chargées correctement, le dossier de travail doit respecter l'arborescence suivante :

```
mon_projet/
├── fundus_images/
│   └── image01.jpg          ← image de fond d'œil (format .jpg)
└── segmentation_masks/
    ├── veins/
    │   └── image01.png      ← masque des veines
    ├── arteries/
    │   └── image01.png      ← masque des artères
    └── od/
        └── image01.png      ← masque du disque optique
```

> Le nom du fichier image (sans extension) doit être identique dans chaque sous-dossier.

---

## Utilisation

### Workflow typique

1. **Lancer l'application** puis cliquer sur **"Traitement d'image"**
2. **Ouvrir un dossier de travail** (bouton en haut à droite) — les résultats y seront sauvegardés
3. **Ouvrir un dossier d'images** — les miniatures apparaissent dans le bandeau inférieur
4. Cliquer sur une miniature pour afficher l'image et ses segmentations superposées
5. Utiliser le **panneau gauche "Segmentation"** pour :
   - Activer/désactiver chaque couche (veines, artères, disque optique)
   - Régler l'opacité avec les curseurs
   - Modifier les couleurs via les boutons dédiés
   - Créer ou éditer manuellement le disque optique si nécessaire
6. Cliquer sur **"Lancer les mesures"** pour calculer les métriques anatomiques
7. Consulter les résultats dans le **panneau "Mesures"** (filtrage par vaisseau, zone et groupe)
8. **Sauvegarder** l'image courante ou toutes les images du lot

### Édition du disque optique

Si le disque optique est absent ou mal positionné :
- Cliquer sur **"Créer un disque"** pour en générer un au centre de l'image
- Cliquer sur **"Éditer le disque"** (mode ON/OFF) pour le déplacer à la souris
- Cliquer à nouveau sur **"Éditer le disque"** pour valider la position — le masque est automatiquement mis à jour sur le disque

### Structure de sauvegarde générée

```
dossier_de_travail/
└── image01_OVP/
    ├── fundus_images/
    │   ├── image01_OVP.jpg
    │   └── config_segmentation.json   ← réglages (opacités, couleurs)
    ├── segmentation_masks/
    │   ├── veins/
    │   ├── arteries/
    │   └── od/
    ├── fundus_rendu_images_finales/
    │   └── image01_OVP_rendu.png      ← image fusionnée exportée
    └── results/
        ├── mesures_globales.csv
        └── mesures_json/
            └── image01_data.json
```

---

## Auteurs

Ce projet a été réalisé par des étudiants du Master Bio-informatique de l'Université de Bordeaux :

- Justin Fonteneau
- Thomas Gonzalez-Bonnaud
- Amine Jorho
- Simon Mundel

Encadré par :
- **Mme Marie Beurton-Aimar** — Maîtresse de conférences, Université de Bordeaux
- **M. Sébastien Richard** — Doctorant, Université de Bordeaux

---

## Licence

Le module `measurements.py` est distribué sous licence **GNU GPL v3**.  
Voir l'en-tête du fichier pour les détails.

---

## État du projet

Ce projet est en cours de développement. Les fonctionnalités principales sont opérationnelles. L'intégration directe des algorithmes de segmentation (production automatique des masques) est prévue comme évolution future.
* [Analyze your code for known vulnerabilities with Static Application Security Testing (SAST)](https://docs.gitlab.com/user/application_security/sast/)
* [Deploy to Kubernetes, Amazon EC2, or Amazon ECS using Auto Deploy](https://docs.gitlab.com/topics/autodevops/requirements/)
* [Use pull-based deployments for improved Kubernetes management](https://docs.gitlab.com/user/clusters/agent/)
* [Set up protected environments](https://docs.gitlab.com/ci/environments/protected_environments/)


