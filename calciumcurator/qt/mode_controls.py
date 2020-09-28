from qtpy.QtWidgets import QWidget, QVBoxLayout, QButtonGroup, QPushButton


class ModeControls(QWidget):
    def __init__(self, parent=None):
        super(ModeControls, self).__init__(parent)

        button_group = QButtonGroup()
        self.manual_mode_button = QPushButton('manual')
        self.manual_mode_button.setCheckable(True)
        button_group.addButton(self.manual_mode_button)

        self.snr_mode_button = QPushButton('snr threshold')
        self.snr_mode_button.setCheckable(True)
        button_group.addButton(self.snr_mode_button)

        self.mode_button_group = button_group

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(self.manual_mode_button)
        vbox_layout.addWidget(self.snr_mode_button)

        self.setLayout(vbox_layout)

        self.setMaximumHeight(100)
        self.setStyleSheet(
            'QPushButton:checked{background-color: rgb(0, 122, 204);}'
        )
