from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QComboBox,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
)


class ModeControls(QWidget):
    def __init__(
        self, layer_names, selection_layers, template_ids, parent=None
    ):
        super(ModeControls, self).__init__(parent)

        vbox_layout = QVBoxLayout()

        # Add the overview button
        self.overview_button = QPushButton('Overview Mode')
        vbox_layout.addWidget(self.overview_button)

        # Add the registration mode button
        self.registration_button = QPushButton('Registration Mode')
        vbox_layout.addWidget(self.registration_button)

        self.registration_controls = RegistrationControls(
            layer_names=layer_names,
            selection_layers=selection_layers,
            template_ids=template_ids,
        )
        vbox_layout.addWidget(self.registration_controls)

        self.setLayout(vbox_layout)


class RegistrationControls(QWidget):
    def __init__(
        self, layer_names, selection_layers, template_ids, parent=None
    ):
        super(RegistrationControls, self).__init__(parent)
        vbox_layout = QVBoxLayout()

        # Add the template
        self.template_layout = QHBoxLayout()
        self.template_layout.addWidget(QLabel('Template layer:'))

        self.template_combo = QComboBox(self)
        self.template_combo.addItems(layer_names)
        self.template_layout.addWidget(self.template_combo)

        vbox_layout.addLayout(self.template_layout)

        # Add the template cell selection
        self.template_cell_layout = QHBoxLayout()
        self.template_cell_layout.addWidget(QLabel('template cell:'))
        self.template_cell_combo = QComboBox(self)
        self.template_cell_combo.addItems(template_ids)
        self.template_cell_layout.addWidget(self.template_cell_combo)
        vbox_layout.addLayout(self.template_cell_layout)

        # Add the selection layout
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel('Selection layer:'))
        self.selection_combo = QComboBox(self)
        self.selection_combo.addItems(selection_layers)
        selection_layout.addWidget(self.selection_combo)
        vbox_layout.addLayout(selection_layout)

        self.assign_button = QPushButton('Assign cell')
        vbox_layout.addWidget(self.assign_button)

        self.setLayout(vbox_layout)
        self.setMaximumHeight(200)
