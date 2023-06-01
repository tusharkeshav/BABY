import os
import sys
import random

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QDesktopWidget
from sounds.play import playsound
from voice2intent import SUBMIT_JOB

from speech.text2speech import speak

data = None
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/../')

IMAGE = {
    'heads': 'img/heads.gif',
    'tails': 'img/tails.gif'
}


def flip_coin():
    result = random.choice(["Heads", "Tails"])
    # speak("It is {state}".format(state=result))
    if result == 'Heads':
        start(outcome=result, file=IMAGE['heads'], title="Heads")
    else:
        start(outcome=result, file=IMAGE['tails'], title="Tails")


class Worker(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        # Simulate a long-running task
        # time.sleep(2)
        playsound('sounds/coin_flip.mp3')
        self.finished.emit()


class MainWindow(QWidget):
    def __init__(self, file, title):
        super().__init__()
        self.title = title

        # Create a QMovie object to display the loader
        self.movie = QMovie(file)
        self.movie.setScaledSize(QSize(300, 300))
        self.loader_label = QLabel()
        self.loader_label.setMovie(self.movie)
        screen_size = QDesktopWidget().screenGeometry()
        width, height = screen_size.width(), screen_size.height()
        # print(f'with is {width}')
        # print(f'height is {height}')
        self.setGeometry(0, 0, 150, 150)
        self.move(width // 2 - 100, height // 2 - 200)  # this control where is the coordinate of the window
        # self.center_on_screen()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Create a label to display the result of the function
        self.result_label = QLabel('')
        self.start_function()

        layout = QVBoxLayout()
        layout.addWidget(self.loader_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

        # Set the window title and size
        self.setWindowTitle(title)
        # self.resize(self.movie.scaledSize())
        # get_intent(self.worker)

    def start_function(self):
        # Disable the button and start the loader
        # self.button.setEnabled(False)4
        self.movie.start()
        QApplication.processEvents()

        # Create a worker thread to run the function
        self.worker = Worker()
        self.worker.finished.connect(self.get_intent)
        # self.worker.finished.connect(self.stop_loader)
        self.worker.start()

    def stop_loader(self):
        # Stop the loader and show the result
        self.movie.stop()
        self.window().destroy()
        self.window().close()
        QApplication.quit()

    def get_intent(self):
        # # QApplication.quit()
        # global data
        # data = result
        font = QtGui.QFont()
        font.setPointSize(20)
        self.result_label.setFont(font)
        self.result_label.setAlignment(Qt.AlignHCenter)
        self.result_label.setText(f'It\'s {self.title}')
        SUBMIT_JOB.submit(speak, 'It is {outcome}'.format(outcome=self.title))
        # TODO: Optimize this below to use pyqt threading instead of python threading
        QTimer.singleShot(4000, self.stop_loader)


def start(outcome, file, title):
    app = QApplication(sys.argv)
    window = MainWindow(file, title)
    window.show()
    app.exec_()
