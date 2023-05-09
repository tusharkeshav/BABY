import sys
import time

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QDesktopWidget

intent = None


def get_data():
    start()
    return intent


class Worker(QThread):
    finished = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()

    def run(self):
        # Simulate a long-running task
        from voice2intent import record_analyse
        result = record_analyse()
        # time.sleep(5)
        # result = (1, "hello")
        self.finished.emit(result)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Create a QMovie object to display the loader
        self.movie = QMovie('img/listen.gif')
        self.movie.setScaledSize(QSize(200, 200))
        self.loader_label = QLabel()
        self.loader_label.setMovie(self.movie)
        screen_size = QDesktopWidget().screenGeometry()
        width, height = screen_size.width(), screen_size.height()
        # print(f'with is {width}')
        # print(f'height is {height}')
        # self.setGeometry(0, 0, 150, 150)
        self.move(width // 2 - 100, height - 200)  # this control where is the coordinate of the window
        # self.center_on_screen()
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Create a label to display the result of the function
        self.result_label = QLabel('')
        self.start_function()

        layout = QVBoxLayout()
        layout.addWidget(self.loader_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

        # Set the window title and size
        self.setWindowTitle('Listening')
        self.resize(self.movie.scaledSize())
        # get_intent(self.worker)

    def start_function(self):
        # Disable the button and start the loader
        # self.button.setEnabled(False)
        self.movie.start()
        QApplication.processEvents()

        # Create a worker thread to run the function
        self.worker = Worker()
        self.worker.finished.connect(self.get_intent)
        # self.worker.finished.connect(self.stop_loader)
        self.worker.start()

    def stop_loader(self):
        # Stop the loader and show the result
        # print(resul)
        # self.result_label.setText('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx!')
        # time.sleep(2)
        self.movie.stop()
        # time.sleep(5)
        self.window().destroy()
        # self.worker.deleteLater()
        self.window().close()
        # self.movie.finished
        QApplication.quit()

    def get_intent(self, result):
        # print(f"I m in get {intent}")
        # QApplication.quit()
        global intent
        intent = result
        if intent[1]['intent'] != '':
            font = QtGui.QFont()
            font.setPointSize(20)
            self.result_label.setFont(font)
            self.result_label.setText('Intent: {found_intent}'.format(found_intent=intent[1]['text']))
        QTimer.singleShot(5000, self.stop_loader)
        # print(self.stop_loader(intent))
        print("I'm in get function")
        # return intent


def start():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     app.exec_()

# start()
