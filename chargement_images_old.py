import os
import numpy as np
import skimage as ski


    
def images_paths (path_image_ref) :
    """
    Retourne une liste de chemins de fichiers à partir du chemin de l'image originale,
    dans l'ordre suivant : originale, veines, artères, disque optique.

    Args:
        path_image_ref (str): chemin de l'image originale

    Returns:
        list(str): la liste des chemins des images (originale + segmentations)
    """
    list_paths = []

    #Normalise le chemin de fichier (change les '/' en '\')
    path_image_ref = os.path.normcase(path_image_ref)

    #Ajoute le chemin de l'image originale à la liste
    list_paths.append (path_image_ref)

    #Décomposition du filepath en 2 parties
    split_path = os.path.split(path_image_ref)

    #Chemin vers le projet
    project_path = split_path[0]

    #Nom précis de l'image originale
    filename = split_path[1]

    #Nom des images de segmentation
    mask_name = filename.replace ("jpg", "png")

    #Création du chemin vers le répertoire des masques
    path_segmentations = os.path.split(project_path)
    path_segmentations = os.path.join(path_segmentations[0]  , "segmentation_masks")

    #Création du chemin pour les veines
    path_veins = os.path.join(path_segmentations , "veins" , mask_name)
    list_paths.append (path_veins)

    #Création du chemin pour les artères
    path_arteries = path_veins.replace("veins" , "arteries")
    list_paths.append (path_arteries)

    #Création du chemin pour le disque optique
    path_od = path_veins.replace("veins" , "od")
    list_paths.append (path_od)

    return list_paths

# def recuperation_couleur(color):
#     return color

def load_images(list_paths,
                couleur_veines=(0, 0, 255, 255),
                couleur_arteres=(255, 0, 100, 255),
                couleur_disque=(0, 255, 0, 255),
                couleur_superposition=(255, 0, 255, 255)):

    image_originale = ski.io.imread(list_paths[0])
    image_originale = np.transpose(image_originale, (2, 0, 1))

    mask_veins_raw = ski.io.imread(list_paths[1])
    if mask_veins_raw.ndim == 3:          # si RGB ou RGBA
        mask_veins_raw = mask_veins_raw.max(axis=2)
    h, w = mask_veins_raw.shape

    # Veines — couleur paramétrable
    mask_temp = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            if mask_veins_raw[y, x] > 0:
                mask_temp[y, x] = couleur_veines   
    mask_veins = mask_temp

    # Artères — couleur paramétrable
    mask_arteries_raw = ski.io.imread(list_paths[2])
    if mask_arteries_raw.ndim == 3:
        mask_arteries_raw = mask_arteries_raw.max(axis=2)
    mask_temp = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            if mask_arteries_raw[y, x] > 0:
                if mask_veins_raw[y, x] > 0:
                    mask_temp[y, x] = couleur_superposition  # overlap artères/veines
                else:
                    mask_temp[y, x] = couleur_arteres      
    mask_arteries = mask_temp

    # Disque optique — couleur paramétrable
    mask_od_raw = ski.io.imread(list_paths[3])
    if mask_od_raw.ndim == 3:
        mask_od_raw = mask_od_raw.max(axis=2)
    mask_temp = np.zeros((h, w, 4), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            if mask_od_raw[y, x] > 0:
                mask_temp[y, x] = couleur_disque           
    mask_od = mask_temp

    return image_originale, mask_veins, mask_arteries, mask_od