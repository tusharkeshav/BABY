import urllib.request
from bs4 import BeautifulSoup
from speech.text2speech import speak
import wikipedia
from PyQt5.QtCore import QRect, QPropertyAnimation, QEasingCurve, Qt, QThread, pyqtSignal, QTimer, QEvent
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QScrollArea, QDesktopWidget

RESULT = ()

def get_image(soup):
    try:
        for img in soup.select("img"):
            print(img["src"])

    except:
        pass

def get_about(soup):
    try:
        divs = soup.select(".kno-rdesc")  # select div of about section.
        results = divs[0].select("span:nth-child(2)")[0].get_text()
        return True, results, 'Google'
    except:
        return False, '', ''
    pass


def get_wa_description(soup):
    try:
        divs = soup.select(".V3FYCf > div:nth-child(1) > div:nth-child(1) > span:nth-child(1) > span:nth-child(1)")
        result = divs[0].get_text()
        return True, result, 'Google'
    except:
        return False, '', ''
        pass


def get_wikipedia_result(query):
    try:
        suggest = wikipedia.suggest(query)
        result = ''
        if len(suggest) > 0 and suggest is not None:
            result = wikipedia.summary(suggest, sentences=3)
        else:
            search = wikipedia.search(query)[0]
            result = wikipedia.summary(search, sentences=3)

        if result != '':
            return True, result, 'Wikipedia'
        else:
            False, None, ''
    except:
        return False, None, ''


def search(query):
    url = 'https://google.com/search?q={query}'.format(query=str(query).replace(' ', '+'))

    # Perform the request
    request = urllib.request.Request(url)

    # Set a normal User Agent header, otherwise Google will block the request.
    request.add_header('User-Agent',
                       'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0')
    raw_response = urllib.request.urlopen(request).read()
    html = raw_response.decode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')

    # get_image(soup)
    about = get_about(soup)
    wa_description = get_wa_description(soup)
    print("wa description" + str(wa_description))
    print('meow')
    wiki_date = get_wikipedia_result(query=query)
    global RESULT
    if about[0]:
        RESULT = (about[1], about[2])
    elif wa_description[0]:
        RESULT = (wa_description[1], wa_description[2])
    elif wiki_date[0]:
        RESULT = (wiki_date[1], wiki_date[2])


class Worker(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        print(RESULT)
        speak("As per " + RESULT[1])
        speak(RESULT[0])
        self.finished.emit()


class PopUp(QWidget):
    def __init__(self, text, parent=None):
        super(PopUp, self).__init__(parent)

        screen_size = QDesktopWidget().screenGeometry()
        width, height = screen_size.width(), screen_size.height()
        self.setGeometry(QRect(0, 0, 320, height))
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.label = QLabel(text)
        self.label.setStyleSheet("background-color: rgba(0,0,0,150); color: white; font-size: 24px;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedWidth(300)
        self.label.setFixedHeight(height)
        self.label.setWordWrap(True)
        self.label.setWordWrap(True)
        # self.move(width, height - 800)
        # self.label.move(width, height - 800)
        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidget(self.label)
        scroll_area.setAttribute(Qt.WA_TranslucentBackground, True)
        scroll_area.setStyleSheet("background-color: rgba(0,0,0,150)")
        layout = QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(1000)
        self.animation.setStartValue(QRect(width - 320, 0, 320, height))
        self.animation.setEndValue(QRect(width - 320, 0, 320, height))
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        QApplication.processEvents()
        self.worker = Worker()
        self.worker.finished.connect(self.tmp)
        self.worker.start()
        self.animation.start()
        self.show()
        self.installEventFilter(self)

    def tmp(self):
        QTimer.singleShot(2000, self.stop)

    def stop(self):
        QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.geometry().contains(event.pos()):
            self.close()


def search_result(query):
    search(query)
    if len(RESULT) == 0:
        return

    app = QApplication([])
    pop_up = PopUp(RESULT[0], parent=None)
    app.exec_()


# search_result("cutipie meaning in english")
