import sys
import os
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from circular_progress import CircularProgress
from dicom3 import AppWindow


class MainWin(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        # RESIZE WINDOW
        self.resize(500, 500)

        # REMOVE TITLE BAR
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # CREATE CONTAINER AND LAYOUT
        self.container = QFrame()
        self.container.setStyleSheet("background-color: transparent")
        self.layout = QVBoxLayout()
        self.layout = QGridLayout()

        # CREATE CIRCULAR PROGRESS
        self.progress = CircularProgress()
        self.progress.value = 20
        self.progress.font_size = 30
        self.progress.progress_width = 20
        self.progress.progress_rounded_cap =True
        self.progress.add_shadow(True)
        self.progress.labeling(True)
        self.progress.setMinimumSize(self.progress.width, self.progress.height)

        # ADD WIDGETS
        self.layout.addWidget(self.progress, Qt.AlignCenter, Qt.AlignCenter)

        # SET CENTRAL WIDGET
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        #SHOW WINDOW
        self.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)
        self.count = 0

    def update(self):
        self.progress.set_value(self.count)

        if self.count >= 100:
            self.timer.stop()
            app.setStyle("Fusion")
            self.mainapp = AppWindow()
            self.mainapp.show()
            self.close()

        self.count += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWin()
    sys.exit(app.exec_())