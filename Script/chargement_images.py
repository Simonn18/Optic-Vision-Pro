import os
import numpy as np
import skimage as ski
import skimage.transform  # noqa: F401  (assure ski.transform.resize disponible)
import skimage.measure    # noqa: F401  (assure ski.measure.label disponible)


def _fov_square(image_rgb):
    """Retrouve le carré du champ de vue (la rétine) dans un fundus RGB.

    La segmentation a été produite sur un crop carré centré sur la rétine, donc
    pour réaligner les masques il faut ce même carré. On isole la plus grande
    composante lumineuse (élimine labels/reflets en bord), on prend sa boîte
    englobante, puis un carré de côté = min(largeur, hauteur) centré dessus.

    Returns:
        (x0, y0, side) : coin haut-gauche et côté du carré (peut dépasser l'image,
        le placement sera tronqué par l'appelant).
    """
    h, w = image_rgb.shape[:2]
    clair = image_rgb.sum(axis=2) > 30          # rétine éclairée vs fond noir
    if clair.any():
        lab = ski.measure.label(clair)
        if lab.max() > 1:                        # garde la plus grande composante
            tailles = np.bincount(lab.ravel())
            tailles[0] = 0
            clair = lab == tailles.argmax()
        ys, xs = np.where(clair)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    else:                                        # garde-fou : tout le cadre
        x0, x1, y0, y1 = 0, w - 1, 0, h - 1
    side = min(x1 - x0 + 1, y1 - y0 + 1)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    return cx - side // 2, cy - side // 2, side


    
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

    #Nom des images de segmentation (toujours .png, quelle que soit l'extension source)
    mask_name = os.path.splitext(filename)[0] + ".png"

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

def _normalise_rgb(image):
    """Force une image vers 3 canaux RGB : gère le niveaux de gris (2D) et le
    RGBA (4 canaux), sinon le transpose suppose à tort 3 canaux et casse
    l'affichage des PNG."""
    if image.ndim == 2:                                   # niveaux de gris
        image = np.stack([image] * 3, axis=-1)
    elif image.ndim == 3 and image.shape[2] == 4:         # RGBA
        image = image[:, :, :3]
    return image


def _placer_masque(chemin, h, w, sx0, sy0, side):
    """Recale un masque (carré, issu d'un crop du champ de vue) dans le repère
    (h, w) du fundus : resize vers le carré du FOV puis dépose à sa position.

    Les masques sont carrés (ex. 1024x1024) car la segmentation est faite sur un
    CROP CARRÉ centré sur le champ de vue (la rétine), pas sur l'image entière.
    Un simple resize vers (h, w) étirerait le masque et décalerait le centre
    quand le fundus n'est pas carré ; si la rétine remplit déjà le cadre (JPG OVP
    déjà recadrés), le carré = image entière -> mapping 1:1.
    """
    m = ski.io.imread(chemin)
    # Réduit un masque RGB/RGBA en 2D. On ignore le canal alpha : sinon un PNG
    # RGBA avec alpha=255 partout marquerait toute l'image comme active.
    if m.ndim == 3:
        m = m[:, :, :3].max(axis=2)
    # Redimensionne le masque au côté du carré du champ de vue (order=0 = plus
    # proche voisin -> reste binaire) puis le dépose à la bonne position.
    m = ski.transform.resize(
            m, (side, side), order=0, preserve_range=True, anti_aliasing=False
        ).astype(m.dtype)
    plein = np.zeros((h, w), dtype=m.dtype)
    ax0, ay0 = max(sx0, 0), max(sy0, 0)
    ax1, ay1 = min(sx0 + side, w), min(sy0 + side, h)
    plein[ay0:ay1, ax0:ax1] = m[ay0 - sy0:ay1 - sy0, ax0 - sx0:ax1 - sx0]
    return plein


def load_images(list_paths,
                couleur_veines=(0, 0, 255, 255),
                couleur_arteres=(255, 0, 100, 255),
                couleur_disque=(0, 255, 0, 255),
                couleur_superposition=(255, 0, 255, 255)):
    """Charge l'image et ses 3 masques colorisés.

    Version VECTORISÉE (indexation booléenne numpy) : produit exactement le
    même résultat que les anciennes doubles boucles pixel par pixel
    (cf. chargement_images_old.py), mais en une fraction du temps.
    """

    image_originale = _normalise_rgb(ski.io.imread(list_paths[0]))
    h, w = image_originale.shape[:2]

    sx0, sy0, side = _fov_square(image_originale)

    mask_veins_raw    = _placer_masque(list_paths[1], h, w, sx0, sy0, side)
    mask_arteries_raw = _placer_masque(list_paths[2], h, w, sx0, sy0, side)
    mask_od_raw       = _placer_masque(list_paths[3], h, w, sx0, sy0, side)

    image_originale = np.transpose(image_originale, (2, 0, 1))

    # Masques booléens des pixels actifs
    veines  = mask_veins_raw > 0
    arteres = mask_arteries_raw > 0
    disque  = mask_od_raw > 0

    # Veines — couleur paramétrable
    mask_veins = np.zeros((h, w, 4), dtype=np.uint8)
    mask_veins[veines] = couleur_veines

    # Artères — couleur paramétrable, avec couleur dédiée pour l'overlap A/V
    mask_arteries = np.zeros((h, w, 4), dtype=np.uint8)
    mask_arteries[arteres & ~veines] = couleur_arteres
    mask_arteries[arteres &  veines] = couleur_superposition

    # Disque optique — couleur paramétrable
    mask_od = np.zeros((h, w, 4), dtype=np.uint8)
    mask_od[disque] = couleur_disque

    return image_originale, mask_veins, mask_arteries, mask_od


def masque_od_recale(chemin_fundus, chemin_masque):
    """Masque du disque optique recalé dans le repère du fundus (2D uint8 0/255,
    dimensions (h, w) du fundus).

    Applique EXACTEMENT le même recalage que load_images, afin que l'aperçu des
    miniatures soit fidèle à l'affichage de l'image principale.
    """
    image = _normalise_rgb(ski.io.imread(chemin_fundus))
    h, w = image.shape[:2]
    sx0, sy0, side = _fov_square(image)

    m = _placer_masque(chemin_masque, h, w, sx0, sy0, side)
    return (m > 0).astype(np.uint8) * 255


def centre_disque_optique(list_paths):
    """Centre (x, y) du disque optique dans le repère du fundus, ou None si vide.

    Applique EXACTEMENT le même recalage géométrique que load_images (carré du
    champ de vue + resize du masque carré), de sorte que le centre renvoyé
    corresponde à la position du disque telle qu'affichée sur l'image principale.
    """
    m = masque_od_recale(list_paths[0], list_paths[3])
    ys, xs = np.nonzero(m)
    if xs.size == 0:
        return None

    return float(xs.mean()), float(ys.mean())