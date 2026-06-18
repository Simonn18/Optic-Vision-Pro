from chargement_images import images_paths, load_images

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QGraphicsScene, QGraphicsView
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
import numpy as np
import sys

def conversion_qpixmap (image_originale , mask_veins , mask_arteries , mask_od) :
    """
    Retourne 4 Qpixmap à partir des 4NdArrays fournis pour être affichés par PySide6 dans une QGraphicsScene.

    Args:
        Plusieurs NDarray correspondant à l'image et à ses masques
            - En premier, l'image RGB originale non modifiée
            - En second, mask_veins : masque colorisé en bleu   (H, W, 4) uint8
            - En troisième, mask_arteries : masque colorisé en rouge  + intersections veines/artères (H, W, 4) uint8
            - EN quatrième, mask_od : masque colorisé en vert   (H, W, 4) uint8
    Returns:
        Plusieurs Qpixmap correspondant à l'image et à ses masques comme fourni en entrée.
            - En premier, pixmap_fundus : l'image RGB originale non modifiée
            - En second, pixmap_veins : masque des veines colorisé en bleu (RGBA pour la transparence)
            - En troisième, pixmap_arteries : masque des artères colorisé en rouge  + intersections veines/artères (RGBA pour la transparence)
            - EN quatrième, pixmap_od : masque du DO colorisé en vert (RGBA pour la transparence)
    """
    #Conversion de l'image fundus en QPixmap
    image_originale = np.transpose(image_originale, (1, 2, 0))
    image_originale =  np.ascontiguousarray(image_originale)
    h = image_originale.shape[0]
    w = image_originale.shape[1]
    qimg_originale = QImage (image_originale.data , w , h , 3*w, QImage.Format.Format_RGB888)
    pixmap_fundus = QPixmap.fromImage(qimg_originale)

    # Chaque masque utilise SA propre largeur/hauteur pour le stride QImage
    # (et non celles du fundus) : sinon un masque de taille différente est
    # lu avec un mauvais pas mémoire et s'affiche décalé/vide.
    def _masque_vers_pixmap(masque):
        masque = np.ascontiguousarray(masque)
        hm, wm = masque.shape[:2]
        qimg = QImage(masque.data, wm, hm, 4 * wm, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    pixmap_veins    = _masque_vers_pixmap(mask_veins)
    pixmap_arteries = _masque_vers_pixmap(mask_arteries)
    pixmap_od       = _masque_vers_pixmap(mask_od)

    return pixmap_fundus , pixmap_veins , pixmap_arteries , pixmap_od

def afficher(app, pixmap_fundus , pixmap_veins, pixmap_arteries , pixmap_od):
    """
    Petite fonction rapide pour pouvoir display les différentes images.
    """
    fenetre = QMainWindow()

    # Scène et vue
    scene = QGraphicsScene()
    vue = QGraphicsView(scene)

    # Ajout des calques
    scene.addPixmap(pixmap_fundus)
    item_veins    = scene.addPixmap(pixmap_veins)
    item_arteries = scene.addPixmap(pixmap_arteries)
    item_od       = scene.addPixmap(pixmap_od)

    # Opacités initiales
    item_veins.setOpacity(0.5)
    item_arteries.setOpacity(0.5)
    item_od.setOpacity(0.5)

    # Sliders
    def make_callback(item):
        return lambda valeur: item.setOpacity(valeur / 100.0)

    slider_veins    = QSlider(Qt.Orientation.Horizontal)
    slider_arteries = QSlider(Qt.Orientation.Horizontal)
    slider_od       = QSlider(Qt.Orientation.Horizontal)

    for slider in [slider_veins, slider_arteries, slider_od]:
        slider.setRange(0, 100)
        slider.setValue(50)

    slider_veins.valueChanged.connect(make_callback(item_veins))
    slider_arteries.valueChanged.connect(make_callback(item_arteries))
    slider_od.valueChanged.connect(make_callback(item_od))

    # Layout
    conteneur = QWidget()
    layout = QVBoxLayout(conteneur)

    layout.addWidget(vue)
    layout.addWidget(QLabel("Veines"))
    layout.addWidget(slider_veins)
    layout.addWidget(QLabel("Artères"))
    layout.addWidget(slider_arteries)
    layout.addWidget(QLabel("Disque optique"))
    layout.addWidget(slider_od)

    fenetre.setCentralWidget(conteneur)
    fenetre.setWindowTitle("Visualisation des masques")
    fenetre.resize(800, 600)
    vue.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    fenetre.show()
    app.exec()

