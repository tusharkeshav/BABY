import os.path
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, QScrollArea, QPushButton
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QSettings

path = os.path.dirname(os.path.abspath(__file__))


class ConfigUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window properties
        self.setWindowTitle("Config File")
        self.setGeometry(100, 100, 400, 300)

        # Set application color palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#F5F5F5"))
        palette.setColor(QPalette.WindowText, QColor("#333333"))
        palette.setColor(QPalette.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.Text, QColor("#333333"))
        QApplication.setPalette(palette)

        # Create main widget and layout
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.main_widget = QWidget(self)
        self.scroll_area.setWidget(self.main_widget)

        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Read config.ini file
        config = QSettings("config.ini", QSettings.IniFormat)

        # Track section labels and variable labels
        section_labels = {}
        variable_labels = {}

        # Iterate through the sections in the config file
        sections = config.childGroups()
        for section in sections:
            # Create section header label
            section_label = QLabel(f"[{section}]", self)
            section_label.setFont(QFont("Arial", 12, QFont.Bold))
            section_label.setStyleSheet("color: #336699;")
            self.layout.addWidget(section_label)

            # Store the section label in the dictionary
            section_labels[section] = []

            # Read the variables in the section
            config.beginGroup(section)
            variables = config.childKeys()
            for variable in variables:
                # Create variable label
                variable_label = QLabel(variable, self)
                variable_label.setFont(QFont("Arial", 10))
                self.layout.addWidget(variable_label)

                # Create line edit
                line_edit = QLineEdit(self)
                line_edit.setText(config.value(variable, ""))
                self.layout.addWidget(line_edit)

                # Store the variable label in the corresponding section
                section_labels[section].append(variable_label)

                # Store the variable label and line edit in the dictionary
                variable_labels[variable_label] = line_edit

            config.endGroup()

        # Add an empty stretch at the end to push the save button to the bottom
        self.layout.addStretch(1)

        # Create save button
        save_button = QPushButton("Save", self)
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.setStyleSheet("background-color: #336699; color: #FFFFFF; border-radius: 5px;")
        save_button.clicked.connect(lambda: self.save_config(variable_labels, section_labels))
        self.layout.addWidget(save_button)

        # Set the main widget and layout
        self.setCentralWidget(self.scroll_area)

    def save_config(self, variable_labels, section_labels):
        # Read values from line edits and update config.ini
        config = QSettings(os.path.join(path, "config.ini"), QSettings.IniFormat)
        for section, variables in section_labels.items():
            for variable_label in variables:
                value = variable_labels[variable_label].text()
                config.setValue(f"{section}/{variable_label.text()}", value)

        # Save the config file
        config.sync()

        # Close the window
        self.close()


def view_config():
    app = QApplication(sys.argv)
    window = ConfigUI()
    window.show()
    app.exec_()
