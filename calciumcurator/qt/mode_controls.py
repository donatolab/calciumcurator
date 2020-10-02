import numpy as np
from qtpy.QtWidgets import (
    QLabel,
    QSpinBox,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QButtonGroup,
    QPushButton,
)
from qtpy.QtCore import Qt


class ModeControls(QWidget):
    def __init__(self, n_cells: int = 0, parent=None):
        super(ModeControls, self).__init__(parent)

        vbox_layout = QVBoxLayout()

        self.manual_curation_controls = ManualCurationControls(
            n_cells=n_cells, parent=self
        )
        vbox_layout.addWidget(self.manual_curation_controls)
        snr_title = QLabel('<b>2. threshold snr<\b>')
        snr_title.setMaximumHeight(20)
        vbox_layout.addWidget(snr_title)
        self.snr_mode_button = QPushButton('display SNR')
        self.snr_mode_button.setCheckable(True)
        vbox_layout.addWidget(self.snr_mode_button)

        save_title = QLabel('<b>3. save<\b>')
        save_title.setMaximumHeight(20)
        vbox_layout.addWidget(save_title)
        self.save_button = QPushButton('save curated cells')
        vbox_layout.addWidget(self.save_button)

        button_group = QButtonGroup()
        button_group.addButton(
            self.manual_curation_controls.manual_mode_button
        )
        button_group.addButton(self.manual_curation_controls.focus_mode_button)
        button_group.addButton(self.snr_mode_button)

        self.mode_button_group = button_group
        self.setLayout(vbox_layout)
        self.setMaximumHeight(450)
        self.setStyleSheet(
            'QPushButton:checked{background-color: rgb(0, 122, 204);}'
        )


class LoadControls(QWidget):
    def __init__(self, parent=None):
        super(LoadControls, self).__init__(parent)

        vbox_layout = QVBoxLayout()
        title = QLabel('<b>0: load data<\b>')
        title.setMaximumHeight(20)
        vbox_layout.addWidget(title)

        self.load_button = QPushButton('load')
        vbox_layout.addWidget(self.load_button)
        self.setLayout(vbox_layout)
        self.setMaximumHeight(75)


class ManualCurationControls(QWidget):
    def __init__(self, n_cells: int = 0, parent=None):
        super(ManualCurationControls, self).__init__(parent)

        vbox_layout = QVBoxLayout()
        title = QLabel('<b>1: manual curation<\b>')
        title.setMaximumHeight(20)
        vbox_layout.addWidget(title)

        self.manual_mode_button = QPushButton('all')
        self.manual_mode_button.setCheckable(True)
        # self.manual_mode_button.setMinimumHeight(25)
        vbox_layout.addWidget(self.manual_mode_button)

        self.focus_mode_button = QPushButton('focus')
        self.focus_mode_button.setCheckable(True)
        # self.focus_mode_button.setMinimumHeight(25)
        vbox_layout.addWidget(self.focus_mode_button)

        selected_cell_layout = QHBoxLayout()
        # selected_cell_layout.setAlignment(Qt.AlignCenter)
        selected_cell_title = QLabel('selected cell:')
        # selected_cell_title.setMaximumHeight(20)
        selected_cell_layout.addWidget(selected_cell_title)
        self.selected_cell_spinbox = QSpinBox()
        self.selected_cell_spinbox.setFocusPolicy(Qt.NoFocus)
        self.selected_cell_spinbox.setReadOnly(False)
        self.selected_cell_spinbox.setKeyboardTracking(False)
        max_cell_index = n_cells - 1
        self.selected_cell_spinbox.setMaximum(np.max((max_cell_index, 0)))
        # self.selected_cell_spinbox.setMaximumWidth(8)
        self.selected_cell_spinbox.setAlignment(Qt.AlignCenter)
        selected_cell_layout.addWidget(self.selected_cell_spinbox)

        vbox_layout.addLayout(selected_cell_layout)

        self.setLayout(vbox_layout)
        self.setMaximumHeight(150)
