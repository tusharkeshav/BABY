import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog
from PyQt5.QtGui import QFont, QPainter, QIcon, QPen, QColor, QPainterPath
from PyQt5.QtCore import Qt, QRectF
from utilities.custom_skill import write_custom_skill, check_function_existence, check_intent_exist_csv

cross_icon = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'img/icons/cross.png')


class RoundedTextEdit(QTextEdit):
    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)

        # Set the rounded rectangle shape
        rect = QRectF(0, 0, self.viewport().width(), self.viewport().height())
        painter.drawRoundedRect(rect, 10, 10)

        super().paintEvent(event)


class InputFormWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Add Skill")
        self.setGeometry(100, 100, 400, 500)
        self.setStyleSheet("background-color: #e6d330;")
        self.setWindowFlag(Qt.FramelessWindowHint)

        # Create the widgets
        self.heading_label = QLabel(self)
        self.heading_label.setText("Skill")
        self.heading_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.heading_label.move(20, 20)

        self.intent_label = QLabel(self)
        self.intent_label.setText("Intent:")
        self.intent_label.setFont(QFont("Times", 15))
        self.intent_label.move(20, 80)

        self.intent_entry = QLineEdit(self)
        self.intent_entry.setFont(QFont("Arial", 12))
        self.intent_entry.setGeometry(120, 80, 260, 30)
        self.intent_entry.setPlaceholderText("Enter the intent")

        self.action_label = QLabel(self)
        self.action_label.setText("Action:")
        self.action_label.setFont(QFont("Times", 15))
        self.action_label.move(20, 120)

        self.action_entry = QLineEdit(self)
        self.action_entry.setFont(QFont("Arial", 12))
        self.action_entry.setGeometry(120, 120, 260, 30)
        self.action_entry.setPlaceholderText("open | close")

        self.sentences_label = QLabel(self)
        self.sentences_label.setText("Sentences:")
        self.sentences_label.setFont(QFont("Times", 15))
        self.sentences_label.move(20, 160)

        self.sentences_text = RoundedTextEdit(self)
        self.sentences_text.setFont(QFont("Arial", 12))
        self.sentences_text.setGeometry(20, 190, 360, 100)
        self.sentences_text.setPlaceholderText("please <action> the door; can you <action> the door")
        self.sentences_text.textChanged.connect(self.update_non_editable_field)

        self.non_editable_field = QLabel(self)
        self.non_editable_field.setFont(QFont("Arial", 12))
        self.non_editable_field.setGeometry(20, 430, 360, 60)

        self.file_path_label = QLabel(self)
        self.file_path_label.setText("File Path:")
        self.file_path_label.setFont(QFont("Arial", 12))
        self.file_path_label.setFont(QFont("Times", 15))
        self.file_path_label.move(20, 310)

        self.file_path_entry = QLineEdit(self)
        self.file_path_entry.setFont(QFont("Times", 12))
        self.file_path_entry.setGeometry(120, 310, 200, 30)

        self.browse_button = QPushButton(self)
        self.browse_button.setText("Browse")
        self.browse_button.setFont(QFont("Arial", 12))
        self.browse_button.setGeometry(330, 310, 60, 30)
        self.browse_button.setStyleSheet("background-color: #CCCCCC; color: #333333;")

        self.method_label = QLabel(self)
        self.method_label.setText("Method:")
        self.method_label.setFont(QFont("Times", 15))
        self.method_label.move(20, 350)

        self.method_entry = QLineEdit(self)
        self.method_entry.setFont(QFont("Arial", 12))
        self.method_entry.setGeometry(120, 350, 260, 30)
        self.method_entry.setPlaceholderText("Enter the method name(E.g: insult()")

        self.submit_button = QPushButton(self)
        self.submit_button.setText("Submit")
        self.submit_button.setFont(QFont("Arial", 14, QFont.Bold))
        self.submit_button.setGeometry(140, 400, 120, 30)
        self.submit_button.setStyleSheet("background-color: #336699; color: #FFFFFF; border-radius: 5px;")

        self.close_button = QPushButton(self)
        self.close_button.setIcon(QIcon(cross_icon))  # Replace "cross.png" with the path to your cross image
        self.close_button.setGeometry(370, 10, 20, 20)
        self.close_button.setStyleSheet("background-color: transparent;")
        self.close_button.clicked.connect(self.close)

        # Connect the button signals to slots
        self.browse_button.clicked.connect(self.browse_file)
        self.submit_button.clicked.connect(self.submit)

        self.draggable = False
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create a rounded rectangle path
        rounded_rect = QPainterPath()
        rounded_rect.addRoundedRect(QRectF(self.rect()), 10, 10)

        # Set the window shape mask to the rounded rectangle path
        painter.setClipPath(rounded_rect)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw the bold black border
        border_pen = QPen(QColor(0, 0, 0), 3)
        painter.setPen(border_pen)
        painter.drawRect(self.rect())

        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset is not None:
            self.move(self.mapToGlobal(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = False
            self.offset = None

    def update_non_editable_field(self):
        action = self.action_entry.text()
        action = action.split('|')
        sentences = (self.sentences_text.toPlainText()).split(';')
        sentences_list = []
        for sentence in sentences:
            for act in action:
                sentences_list.append(sentence.replace('<action>', act))
        self.non_editable_field.setFont(QFont("Arial", 10, QFont.Bold))
        self.non_editable_field.setStyleSheet("color: green")
        # self.non_editable_field.setText(f"Action: {action}\nSpeak: {sentences_list}")
        self.non_editable_field.setText(f"Sentences: {sentences_list}")

    def browse_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Python/Shell Files (*.py *.sh)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.file_path_entry.setText(file_path)

    def set_error(self, error_msg: str):
        error_tooltip = error_msg
        self.non_editable_field.setFont(QFont("Arial", 10, QFont.Bold))
        self.non_editable_field.setStyleSheet("color: red")
        self.non_editable_field.setText(error_tooltip)

    def check_error(self, intent, action, sentences, file_path, method):
        """
        :return: True-> if error exist. False -> no error
        """
        file_type = os.path.splitext(file_path)[1]
        print('file exist or not: ' + str(os.path.exists(file_path)))
        if len(intent) == 0:
            self.set_error(error_msg="Error: Intent can't be empty")
            return True
        elif check_intent_exist_csv(intent=intent):
            self.set_error(error_msg="Error: Intent already exist in skill.csv file.\n"
                                     "Note: Please recheck skill.csv and sentence file")
            return True
        elif len(sentences) == 0:
            self.set_error(error_msg="Error: Sentences can't be empty")
            return True

        elif len(file_path) == 0:
            self.set_error(error_msg="Error: File path can't be empty")
            return True

        elif os.path.splitext(file_path)[1] not in ('.py', '.sh'):
            """
            if file type selected/pasted is not .py or .sh. So, not supported
            """
            self.set_error(error_msg=f"Error: File Type is \'{file_type}\', which is not supported.\n"
                                     f"NOTE: Only .py or .sh file type are allowed")
            return True

        elif not os.path.exists(file_path):
            self.set_error(error_msg=f"Error: File: \'{file_path}\' doesn't exist. Please recheck")
            return True

        elif len(method) == 0:
            """
            if method field is empty and filetype is also python. Then its not allowed.
            """
            if file_type == '.py':
                self.set_error(error_msg="Error: Method can't be empty for python file.\n"
                                         "NOTE: If file path is python file. Then method can't be empty.")
                return True

        elif len(method) != 0:
            if file_type == '.py' and not check_function_existence(file_path, method.replace('(', '').replace(')', '')):
                self.set_error(error_msg=f"Error: Method '{method}' doesn't exist in file path."
                                         "\nNote: For python file, method should exist.")
                return True

        return False

    def submit(self):
        intent = self.intent_entry.text()
        action = self.action_entry.text()
        sentences = self.sentences_text.toPlainText()
        file_path = self.file_path_entry.text()
        method = self.method_entry.text()
        print("sentences are" + str(sentences))
        if self.check_error(intent, action, sentences, file_path, method):
            pass
        elif len(method) == 0:
            write_custom_skill(intent, action, sentences, file_path)
            QApplication.quit()
        else:
            write_custom_skill(intent, action, sentences, file_path + '::' + method.replace('(', '').replace(')', ''))
            QApplication.quit()


def add_skill():
    app = QApplication(sys.argv)
    window = InputFormWindow()
    window.show()
    app.exec_()
