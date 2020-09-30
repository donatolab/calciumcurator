from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QButtonGroup,
    QPushButton,
)


class ModeControls(QWidget):
    def __init__(self, parent=None):
        super(ModeControls, self).__init__(parent)

        vbox_layout = QVBoxLayout()

        self.load_controls = LoadControls(parent=self)
        vbox_layout.addWidget(self.load_controls)

        button_group = QButtonGroup()
        self.manual_mode_button = QPushButton('manual')
        self.manual_mode_button.setCheckable(True)
        button_group.addButton(self.manual_mode_button)

        self.focus_mode_button = QPushButton('focus')
        self.focus_mode_button.setCheckable(True)
        button_group.addButton(self.focus_mode_button)

        self.snr_mode_button = QPushButton('snr threshold')
        self.snr_mode_button.setCheckable(True)
        button_group.addButton(self.snr_mode_button)

        self.mode_button_group = button_group

        vbox_layout.addWidget(self.manual_mode_button)
        vbox_layout.addWidget(self.focus_mode_button)
        vbox_layout.addWidget(self.snr_mode_button)

        self.setLayout(vbox_layout)

        self.setMaximumHeight(200)
        self.setStyleSheet(
            'QPushButton:checked{background-color: rgb(0, 122, 204);}'
        )


class LoadControls(QWidget):
    def __init__(self, parent=None):
        super(LoadControls, self).__init__(parent)

        vbox_layout = QVBoxLayout()
        title = QLabel('0: load data')
        title.setMaximumHeight(20)
        vbox_layout.addWidget(title)

        self.load_button = QPushButton('load data')
        vbox_layout.addWidget(self.load_button)
        self.setLayout(vbox_layout)
        self.setMaximumHeight(75)
