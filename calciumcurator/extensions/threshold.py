from napari import Viewer
import numpy as np

from ..qt.dock_widgets import HistogramWidget


class ThresholdImage:
    """Extension to threshold an image based on the pixel values

    Parameters
    ----------
    image : np.ndarray
        The image the that will be thresholded by a pixel value threshold
    viewer : napari.Viewer
        The viewer to add the image layer and dock widget to.
    nbins : int
        The number of bins for the histogram. The default is 20.
    xlabel : str
        The label for the horizontal axis of the histogram.
    ylabel : str
        The label for the horizontal axis of the histogram.
    name : str
        The name for the histogram widget. This is passed as the name to viewer.add_dock_widget()
        and will the be the name of the histogram widget in the Window menu.
        The default value is 'histogram'
    """

    def __init__(
        self,
        image: np.ndarray,
        viewer: Viewer,
        nbins: int = 20,
        xlabel: str = '',
        ylabel: str = '',
        image_layer_name: str = 'image',
        name: str = 'histogram',
    ):
        self.image = image
        self.image_layer = viewer.add_image(
            image, name=image_layer_name, visible=False
        )

        # create the histogram
        self.nbins = nbins
        counts, values = self._calculate_histogram()
        self.histogram_widget = HistogramWidget(
            values, counts, xlabel=xlabel, ylabel=ylabel
        )
        self._threshold = 0

        # update the SNR image and connect the event
        self.on_snr_changed()
        self.histogram_widget.threshold_changed_callbacks.append(
            self.on_snr_changed
        )

        # add the histogram dock widget to the viewer
        viewer.window.add_dock_widget(self.histogram_widget, name=name)

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, threshold: float):
        self._threshold = threshold

        # apply the threshold to the image
        thresholded_image = self._threshold_image(threshold)
        self.image_layer.data = thresholded_image

    def _threshold_image(self, threshold):
        thresholded_image = np.copy(self.image)
        thresholded_image[thresholded_image <= threshold] = 0

        return thresholded_image

    def _calculate_histogram(self):
        pixel_values = np.ravel(self.image)
        bins = np.linspace(
            np.int(pixel_values.min()), np.int(pixel_values.max()), self.nbins
        )
        counts, values = np.histogram(pixel_values, bins=bins)

        return counts, values

    def on_snr_changed(self, event=None):
        self.threshold = self.histogram_widget.hist_plot._vert_line.getPos()[0]
