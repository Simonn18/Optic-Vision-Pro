from PySide6.QtWidgets import QDialog, QSlider, QPushButton, QLabel
from PySide6.QtCore import Qt


BLUE  = "#2a6496"
RED   = "#e74c3c"
GREEN = "#27ae60"
ORANGE = "#e67e22"


class Opacite(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opacité")
        self.setFixedSize(360, 200)
        
        #images de fond d'oeils
        self.slider_oeil = QSlider(Qt.Horizontal, self)
        self.forme_slider(self.slider_oeil, color=ORANGE, back_color="#f0d0d0")
        self.slider_oeil.setGeometry(10, 20, 340, 24)
        self.slider_oeil.setRange(0, 100)
        self.slider_oeil.setValue(100)
        self.slider_oeil.valueChanged.connect(self.valueChanged)

        self.label_oeil = QLabel("100", self)
        self.label_oeil.setGeometry(10, 40, 60, 24)
        
        #veines
        self.slider_veines = QSlider(Qt.Horizontal, self)
        self.forme_slider(self.slider_veines)
        self.slider_veines.setGeometry(10, 60, 340, 24)
        self.slider_veines.setRange(0, 100)
        self.slider_veines.setValue(100)
        self.slider_veines.valueChanged.connect(self.valueChanged)

        self.label_veines = QLabel("100", self)
        self.label_veines.setGeometry(10, 80, 60, 24)

        #artères
        self.slider_arteres = QSlider(Qt.Horizontal, self)
        self.forme_slider(self.slider_arteres, color=RED, back_color="#f0d0d0")
        self.slider_arteres.setGeometry(10, 100, 340, 24)
        self.slider_arteres.setRange(0, 100)
        self.slider_arteres.setValue(100)
        self.slider_arteres.valueChanged.connect(self.valueChanged)

        self.label_arteres = QLabel("100", self)
        self.label_arteres.setGeometry(10, 120, 60, 24)
        
        #disque optique
        self.slider_disque = QSlider(Qt.Horizontal, self)
        self.forme_slider(self.slider_disque,color=GREEN)
        self.slider_disque.setGeometry(10, 140, 340, 24)
        self.slider_disque.setRange(0, 100)
        self.slider_disque.setValue(100)
        self.slider_disque.valueChanged.connect(self.valueChanged)
        
        self.label_disque = QLabel("100", self)
        self.label_disque.setGeometry(10, 160, 60, 24)

    def forme_slider(self, slider, color=BLUE, back_color="#d0d0d0"):
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid #999999;
                height: 8px;
                background: {back_color};
                margin: 0px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                border: 1px solid #5c5c5c;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border: 1px solid #777777;
                height: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
        """)


    def valueChanged(self, value):
        # Mise à jour du label correspondant selon le slider source
        slider = self.sender()
        if slider is self.slider_oeil:
            self.label_oeil.setText(str(value))
        if slider is self.slider_veines:
            self.label_veines.setText(str(value))
        if slider is self.slider_arteres:
            self.label_arteres.setText(str(value))
        if slider is self.slider_disque:
            self.label_disque.setText(str(value))

    # def resetValue(self):
    #     self.slider.setValue(50)


