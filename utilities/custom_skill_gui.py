import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog
from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtCore import Qt, QRectF
from utilities.custom_skill import write_custom_skill, check_function_existence


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
        self.non_editable_field.setGeometry(20, 230, 400, 30)

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

        # self.result_label = QLabel(self)
        # self.result_label.setFont(QFont("Arial", 12))
        # self.result_label.setGeometry(20, 420, 360, 100)
        # self.result_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # self.result_label.setWordWrap(True)

        # Connect the button signals to slots
        self.browse_button.clicked.connect(self.browse_file)
        self.submit_button.clicked.connect(self.submit)

    def update_non_editable_field(self):
        action = self.action_entry.text()
        action = action.split('|')
        sentences = (self.sentences_text.toPlainText()).split(';')
        sentences_list = []
        for sentence in sentences:
            for act in action:
                sentences_list.append(sentence.replace('<action>', act))
                # if '<action>' in sentence:
                #     sentences_list.append(sentence.replace('<action>', act))
        self.non_editable_field.setFont(QFont("Arial", 10))
        self.non_editable_field.setText(f"Action: {action}\nSentences: {sentences_list}")

    def browse_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Python/Shell Files (*.py *.sh)")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            self.file_path_entry.setText(file_path)

    def submit(self):
        intent = self.intent_entry.text()
        action = self.action_entry.text()
        sentences = self.sentences_text.toPlainText()
        file_path = self.file_path_entry.text()
        method = self.method_entry.text()

        # Display the entered data
        result_text = f"<b>Intent:</b> {intent}<br><b>Action:</b> {action}<br><b>Sentences:</b><br>{sentences}<br><b>File Path:</b> {file_path}"
        write_custom_skill(intent, action, sentences, file_path)
        # self.result_label.setText(result_text)
        QApplication.quit()


def add_skill():
    app = QApplication(sys.argv)
    window = InputFormWindow()
    window.show()
    sys.exit(app.exec_())


add_skill()
