from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PyQt5 import QtGui
import os

class CircularProgress(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        # CUSTOM PROPERTIES
        self.value = 0
        self.width = 450
        self.height = 450
        self.progress_width = 10
        self.progress_rounded_cap = True
        self.progress_color = '#CCCCFF'
        self.max_value = 100
        self.font_family = "Segeo UI"
        self.font_size = 10
        self.suffix = "%"
        self.text_color = 0x498BD1

        # SET DEFAULT SIZE WITHOUT LAYOUT
        self.resize(self.width, self.height)

    # ADD DROPSHADOW
    def add_shadow(self, enable):
        if enable:
            self.shadow = QGraphicsDropShadowEffect(self)
            self.shadow.setBlurRadius(15)
            self.shadow.setXOffset(0)
            self.shadow.setYOffset(0)
            self.shadow.setColor(QColor(0, 0, 0, 120))
            self.setGraphicsEffect(self.shadow)

    # SET VALUE
    def set_value(self, value):
        self.value = value
        # render progress bar after change value
        self.repaint()

    # PAINT EVENT (DESIGN YOUR CIRCULAR PROGRESS)
    def paintEvent(self, event):
        # SET PROGRESS PARAMETERS
        width = self.width - self.progress_width
        height = self.height - self.progress_width
        margin = self.progress_width / 2
        value = self.value * 360 / self.max_value

        # PAINTER
        paint = QPainter()
        paint.begin(self)
        paint.setRenderHint(QPainter.Antialiasing)
        paint.setFont(QFont(self.font_family, self.font_size))

        # CREATE RECTANGLE
        rect = QRect(0, 0, self.width, self.height)
        paint.setPen(Qt.NoPen)
        paint.drawRect(rect)

        # PEN
        pen = QPen()
        pen.setColor(QColor(self.progress_color))
        pen.setWidth(self.progress_width)

        if self.progress_rounded_cap:
            pen.setCapStyle(Qt.RoundCap)

        # CREATE ARC / CIRCULAR PROGRESS
        paint.setPen(pen)
        paint.drawArc(margin, margin, width, height, -90 * 16, -value * 16)

        # END
        paint.end()

    def labeling(self, yes):
        if yes:
            label = QLabel(self)
            icon_path = os.path.join(os.path.dirname(__file__), 'icon_ass2', 'dicom_icon.png')

            # Create a QPixmap object
            pixmap = QPixmap(icon_path)

            # Check if the QPixmap object is valid
            if not pixmap.isNull():
                smaller_pixmap = pixmap.scaled(280, 280, aspectRatioMode=Qt.KeepAspectRatio)
                label.setPixmap(smaller_pixmap)
                label.move(85, 85)
            else:
                print("Error loading the image.")