from typing import Optional

from napari import Viewer
import numpy as np

from ..qt.plots import LinePlotWidget


class LinePlot:
    """Extension to display intensity traces

    Parameters
    ----------
    viewer : napari.Viewer
        The viewer to add the image layer and dock widget to.
    x : Optional[np.ndarray]
        The image the that will be thresholded by a pixel value threshold
    y : Optional[napari.Viewer]
        The viewer to add the image layer and dock widget to.
    event_indices : Optional[list]
        Indices of discrete events to display on the line plot for each
        trace in y. The events should be the indices corresponding to x.
    current_x : int
        The current x value for setting the vertical line.
    displayed_traces : Optional[list]
        The indices of the traces to display.
        Should match the first dimension of y.

    xlabel : str
        The label for the horizontal axis of the histogram.
    ylabel : str
        The label for the horizontal axis of the histogram.
    name : str
        The name for the plot widget. This is passed as the name to viewer.add_dock_widget()
        and will the be the name of the histogram widget in the Window menu.
        The default value is 'histogram'
    """

    def __init__(
        self,
        viewer: Viewer,
        x: Optional[np.ndarray] = None,
        y: Optional[np.ndarray] = None,
        event_indices: Optional[list] = None,
        current_x: int = 0,
        displayed_traces: Optional[list] = None,
        xlabel: str = '',
        ylabel: str = '',
        name: str = 'traces',
    ):
        if x is None:
            x = np.empty()
        if y is None:
            y = np.empty()

        self.x = x
        self.y = y

        # create the plot
        self.plot_widget = LinePlotWidget(
            xlabel=xlabel, ylabel=ylabel, events=None,
        )

        # store the displayed traces
        # this also updates the plot
        if displayed_traces is None:
            self.displayed_traces = {}
        else:
            self.displayed_traces = set(displayed_traces)
        self.current_x = current_x

        # add the histogram dock widget to the viewer
        viewer.window.add_dock_widget(self.plot_widget, name=name)

    @property
    def current_x(self) -> int:
        return self._current_x

    @current_x.setter
    def current_x(self, current_x):
        self.plot_widget.update_vline(current_x)
        self._current_x = current_x

    @property
    def displayed_traces(self) -> set:
        return self._displayed_traces

    @displayed_traces.setter
    def displayed_traces(self, displayed_traces):
        if not isinstance(set(displayed_traces), set):
            displayed_traces = set(displayed_traces)

        if len(displayed_traces) > 0:
            if self.x.ndim == 2:
                x = np.squeeze(self.x[list(displayed_traces)])
            else:
                x = self.x
            y = np.squeeze(self.y[list(displayed_traces)])
            self.plot_widget.plot(x, y)
            self._displayed_traces = displayed_traces
        else:
            self.clear()

    def clear(self):
        self.plot_widget.clear()
