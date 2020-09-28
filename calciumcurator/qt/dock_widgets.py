from typing import Optional

import numpy as np
from qtpy.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QSpacerItem,
)

from .plots import Histogram


class HistogramWidget(QWidget):
    def __init__(
        self,
        x: np.ndarray,
        y: np.ndarray,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        parent=None,
    ):
        super(HistogramWidget, self).__init__(parent)

        # set the width of the histogram plot to match the napari layer control width
        self.setMinimumWidth(240)
        self.setMaximumWidth(240)

        self.hist_plot = Histogram(
            x, y, xlabel=xlabel, ylabel=ylabel, parent=self
        )
        self.hist_plot.setMaximumWidth(230)

        self.thresh_text = QLineEdit()
        self.text_layout = QHBoxLayout()
        self.text_layout.addWidget(QLabel("SNR threshold:"))
        self.text_layout.addWidget(self.thresh_text)
        self.text_layout.addItem(QSpacerItem(5, 1))

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(2)
        # self.grid_layout.setColumnMinimumWidth(0, 86)
        # self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.addWidget(self.hist_plot, 0, 0, 4, 6)
        self.grid_layout.addLayout(self.text_layout, 4, 0)
        self.grid_layout.setRowStretch(5, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.setLayout(self.grid_layout)

        self.threshold_changed_callbacks = []

        self._on_hist_thresh_change()

        # connect events
        self.hist_plot.connect_line_dragged(self._on_hist_thresh_change)
        self.thresh_text.returnPressed.connect(self._on_thresh_text_change)

    def _on_hist_thresh_change(self):
        hist_thresh_value = self.hist_plot._vert_line.getPos()[0]
        self.thresh_text.setText(f"{hist_thresh_value:.2f}")

        for func in self.threshold_changed_callbacks:
            func()

    def _on_thresh_text_change(self):
        hist_thresh_value = float(self.thresh_text.text())
        self.hist_plot._vert_line.setValue(hist_thresh_value)
