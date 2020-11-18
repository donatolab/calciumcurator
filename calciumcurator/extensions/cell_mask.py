from typing import Union

from napari import Viewer
import numpy as np

from ..contour_manager import ContourManager


class CellMask:
    """Extension to display cell masks

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
    selection_layer_name : str
        The name of the shapes layer that outlines the selected cells.
    accepted_layer_name : str
        The name of the labels layer containing the accepted cells.
    rejected_layer_name : str
        The name of the labels layer containing the rejected cells.
    """

    def __init__(
        self,
        viewer: Viewer,
        im_shape: tuple,
        cell_masks: list = [],
        initial_state: Union[str, np.ndarray] = "good",
        selection_layer_name: str = 'selected_cell',
        accepted_layer_name: str = 'accepted_mask',
        rejected_layer_name: str = 'rejected_mask',
        mode: str = 'all',
    ):
        self.selected_shapes = viewer.add_shapes(name=selection_layer_name)

        self.initialize_masks(
            viewer=viewer,
            im_shape=im_shape,
            cell_masks=cell_masks,
            initial_state=initial_state,
            accepted_layer_name=accepted_layer_name,
            rejected_layer_name=rejected_layer_name,
        )

        viewer.bind_key("t", self.toggle_selected_mask)

        self._mode = mode

    def initialize_masks(
        self,
        viewer: Viewer,
        im_shape: tuple,
        cell_masks: list = [],
        initial_state: Union[np.ndarray, str] = 'good',
        accepted_layer_name: str = 'accepted_mask',
        rejected_layer_name: str = 'rejected_mask',
    ):
        self.masks = ContourManager(
            contours=cell_masks, im_shape=im_shape, initial_state=initial_state
        )

        # put the masks in their respective labels layers
        rejected_mask = self.masks.make_rejected_mask()
        self.rejected_labels = viewer.add_labels(
            rejected_mask, name=rejected_layer_name, visible=False
        )
        accepted_mask = self.masks.make_accepted_mask()
        self.accepted_labels = viewer.add_labels(
            accepted_mask, name=accepted_layer_name
        )

    @property
    def selected_mask(self) -> set:
        return self.masks.selected_contours

    @selected_mask.setter
    def selected_mask(self, selected_mask):
        # clear any current selections
        self.masks.selected_contours = {}
        self.selected_shapes.selected_data = np.arange(
            len(self.selected_shapes.data)
        )
        self.selected_shapes.remove_selected()

        if np.all(selected_mask != -1):
            self.masks.selected_contours = set(selected_mask)
            selection_bbox = self._calculate_mask_bbox(selected_mask)

            # the selection box is green if the selected contour is accepted
            # and magenta if it is rejected
            if np.all(self.masks.good_contour[list(selected_mask)]):
                edge_color = 'green'
            else:
                edge_color = 'magenta'

            self.selected_shapes.add(
                selection_bbox,
                shape_type="rectangle",
                face_color="transparent",
                edge_color=edge_color,
            )

            rejected_mask = self.masks.make_rejected_mask()
            self.rejected_labels.data = rejected_mask

            accepted_mask = self.masks.make_accepted_mask()
            self.accepted_labels.data = accepted_mask

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode: str):
        old_mode = self._mode

        if mode != old_mode:
            self.masks.mode = mode
            self._mode = mode

            rejected_mask = self.masks.make_rejected_mask()
            self.rejected_labels.data = rejected_mask

            accepted_mask = self.masks.make_accepted_mask()
            self.accepted_labels.data = accepted_mask

    def toggle_selected_mask(self, viewer):
        selected_contours = list(self.selected_mask)
        if len(selected_contours) > 0:
            good_contour = self.masks.good_contour
            new_state = ~good_contour[selected_contours]
            good_contour[selected_contours] = new_state
            self.masks.good_contour = good_contour

            good_mask_image = self.masks.make_accepted_mask()
            bad_mask_image = self.masks.make_rejected_mask()

            self.accepted_labels.data = good_mask_image
            self.rejected_labels.data = bad_mask_image

            # update the colors of the selected shapes
            new_colors = []
            for cont in new_state:
                if cont:
                    new_colors.append('green')
                else:
                    new_colors.append('magenta')
            self.selected_shapes.edge_color = new_colors

    def _calculate_mask_bbox(self, mask_indices: list) -> list:
        selection_bbox = []

        for mask_index in mask_indices:
            contour = self.masks.contours[mask_index]
            min_r = np.min(contour[:, 0])
            min_c = np.min(contour[:, 1])
            max_r = np.max(contour[:, 0])
            max_c = np.max(contour[:, 1])

            selection_bbox.append(
                np.array(
                    [
                        [min_r, min_c],
                        [min_r, max_c],
                        [max_r, max_c],
                        [max_r, min_c],
                    ]
                )
            )

        return selection_bbox
