import os
import sys
import webbrowser

import requests
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QDesktopWidget

_cross_icon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'img/icons/cross.png')
exit_timer = 60  # 60 sec


class ImageDisplayApp(QWidget):
    def __init__(self, data):
        super().__init__()

        # Set window properties
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedWidth(250)
        # self.setStyleSheet("background-color: rgba(0, 0, 0, 0.1);")

        # Set background color to white 
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(palette)

        # Create layout and populate with images and info
        layout = QVBoxLayout(self)
        cross_label = ClickableLabel(self)
        cross_icon = QIcon(_cross_icon)  # Replace "cross_icon.png" with your cross icon file
        cross_label.setPixmap(cross_icon.pixmap(20, 20))
        cross_label.clicked.connect(self.close)
        layout.addWidget(cross_label, alignment=Qt.AlignTop | Qt.AlignLeft)

        for item in data:
            image_url = item["image_url"]
            info = item["info"]
            url = item["url"]

            image_label = ClickableLabel(self)
            image_label.setPixmap(self.get_image_from_url(image_url))
            image_label.clicked.connect(lambda u=url: self.open_link(u))  # Open link on click
            layout.addWidget(image_label)

            info_label = QLabel(info, self)
            info_label.setStyleSheet('background-color: rgba(255,255,255, 1);')
            layout.addWidget(info_label)

        # Add a stretch to push the images and info to the top
        layout.addStretch()

        # Add the cross image label

        container_widget = QWidget(self)
        container_widget.setLayout(layout)

        # Add the container widget to a scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(container_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Add the scroll area to the main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        # Align the window to the left and stretch it to the screen height
        self.move(0, 0)
        screen_geometry = QDesktopWidget().availableGeometry()
        self.setFixedHeight(screen_geometry.height())

        # Open the window with an animation
        self.animation = QPropertyAnimation(self, b"geometry", self)
        self.animation.setDuration(500)  # Animation duration in milliseconds
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setStartValue(QRect(-300, 0, 300, screen_geometry.height()))
        self.animation.setEndValue(QRect(0, 0, 300, screen_geometry.height()))
        self.animation.start()

        # Set up a timer to close the window after 60 seconds
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.timeout.connect(self.close)
        self.auto_close_timer.start(exit_timer * 1000)  # 60,000 milliseconds = 60 seconds

    def get_image_from_url(self, url):
        response = requests.get(url)
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        return pixmap

    def open_link(self, u):
        """
        open link when clicking image
        :param u:
        :return:
        """
        webbrowser.open(u)
        self.close()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            # Check if the mouse event occurred outside of the window
            if obj is self and not self.rect().contains(event.pos()):
                self.close()  # Close the window
        return super().eventFilter(obj, event)


class ClickableLabel(QLabel):
    clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            super(ClickableLabel, self).mousePressEvent(event)


def display_result(result):
    app = QApplication(sys.argv)

    # Set stylesheet for transparency
    app.setStyleSheet("QWidget { background: transparent; }")

    sample_results = result
    window = ImageDisplayApp(sample_results)
    window.show()
    app.exec_()


sample_results = [
    {
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Big_%26_Small_Pumkins.JPG/1024px-Big_%26_Small_Pumkins.JPG",
        "info": "Image 1 info",
        "url": "https://example.com/page1"},
    {
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpXE7dOugxRUd0dBP_mz5IBwQ3J0NeijJ7tiOrRq9mpw&s",
        "info": "Image 2 info",
        "url": "https://example.com/page2"},
    {
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpXE7dOugxRUd0dBP_mz5IBwQ3J0NeijJ7tiOrRq9mpw&s",
        "info": "Image 3 info",
        "url": "https://example.com/page3"},
    {
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpXE7dOugxRUd0dBP_mz5IBwQ3J0NeijJ7tiOrRq9mpw&s",
        "info": "Image 3 info",
        "url": "https://example.com/page3"},
    {
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpXE7dOugxRUd0dBP_mz5IBwQ3J0NeijJ7tiOrRq9mpw&s",
        "info": "Image 3 info",
        "url": "https://example.com/page3"},
    {
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpXE7dOugxRUd0dBP_mz5IBwQ3J0NeijJ7tiOrRq9mpw&s",
        "info": "Image 3 info",
        "url": "https://example.com/page3"},
    {
        "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpXE7dOugxRUd0dBP_mz5IBwQ3J0NeijJ7tiOrRq9mpw&s",
        "info": "Image 3 info",
        "url": "https://example.com/page3"},
    # Add more results as needed
]

# display_result(sample_results)
