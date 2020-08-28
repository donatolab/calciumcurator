from qtpy.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
import numpy as np


class LinePlot(QWidget):
    def __init__(
        self, x: np.ndarray, y: np.ndarray, events: np.ndarray = None, parent=None
    ):
        super(LinePlot, self).__init__(parent)
        self.vbox = QVBoxLayout()
        self._curves = []

        self.add_plot(x, y)
        if events is not None:
            self.add_events(events, y)
        else:
            self._events_plot = None
        self.setLayout(self.vbox)

    def add_plot(self, x, y, vert_line: bool = True):

        new_plot = pg.plot()
        vline = pg.InfiniteLine(angle=90, movable=False)
        new_plot.addItem(vline)

        self._plot = new_plot
        # self._curves.append(self._plot.plot(data))
        curve_item = pg.PlotCurveItem(x, y)
        self._plot.addItem(curve_item)

        self._curves.append(curve_item)

        self._vert_line = vline

        self.vbox.addWidget(new_plot)

    def add_events(self, events, f_trace):
        x = np.argwhere(events)
        y = f_trace[x]
        pos = np.hstack((x, y))
        if len(pos) > 0:
            self._events_plot = pg.ScatterPlotItem(pos=pos)
        else:
            self._events_plot = pg.ScatterPlotItem()
        self._plot.addItem(self._events_plot)

    def update_vline(self, new_pos):
        self._vert_line.setValue(new_pos)

    def plot(self, data, events=None):
        self.clear()
        self._plot.plot(data)

        if events is not None:
            if len(events) > 0 and self._events_plot is not None:
                self.add_events(events, data)

    def clear(self):
        self._plot.clear()
        vline = pg.InfiniteLine(angle=90, movable=False)
        self._plot.addItem(vline)
        self._vert_line = vline


class Histogram(LinePlot):
    def __init__(self, x: np.ndarray, y: np.ndarray, parent=None):
        super().__init__(x, y, events=None, parent=parent)

    def add_plot(self, x, y, vert_line: bool = True):
        new_plot = pg.plot()
        vline = pg.InfiniteLine(angle=90, movable=True)
        new_plot.addItem(vline)

        self._plot = new_plot
        # self._curves.append(self._plot.plot(data))
        curve_item = pg.PlotCurveItem(
            x, y, stepMode=True, fillLevel=0, brush=(0, 0, 255, 150)
        )
        self._plot.addItem(curve_item)

        self._curves.append(curve_item)

        self._vert_line = vline

        self.vbox.addWidget(new_plot)

    def connect_line_dragged(self, func):
        self._vert_line.sigPositionChanged.connect(func)