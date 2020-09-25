from typing import Optional

import napari
import numpy as np

from .contour_manager import ContourManager
from .extensions import LinePlot, ThresholdImage


class CalciumCurator:
    def __init__(
        self,
        img: np.ndarray,
        data_range,
        contour_manager: ContourManager,
        f: Optional[np.ndarray] = None,
        spikes: Optional[np.ndarray] = None,
        snr: Optional[np.ndarray] = None,
        snr_mask: Optional[np.ndarray] = None,
        cells: Optional[np.ndarray] = None,
        output: str = "iscell_curated.npy",
    ):
        viewer = napari.view_image(
            img, multiscale=False, contrast_limits=data_range, visible=True
        )

        # add the SNR widgets
        if (snr_mask is not None) and (snr is not None):
            snr_extension = ThresholdImage(
                image=snr_mask,
                viewer=viewer,
                xlabel='SNR',
                ylabel='counts',
                name='SNR histogram',
            )

        # Add the cell labels
        selected_shapes = viewer.add_shapes(name="selected_cell")
        rejected_mask = contour_manager.make_rejected_mask()
        bad_labels = viewer.add_labels(rejected_mask, visible=False)

        accepted_mask = contour_manager.make_accepted_mask()
        good_labels = viewer.add_labels(accepted_mask)

        t = np.arange(len(f[0]))
        if spikes is not None:
            spike_events = spikes[0] > 50
        else:
            spike_events = None
        line_plot = LinePlot(
            viewer=viewer,
            x=t,
            y=f,
            xlabel="time",
            ylabel="fluorescence",
            event_indices=spike_events,
        )
        # line_plot = LinePlot(
        #     x=t,
        #     y=f[0],
        #     xlabel="time",
        #     ylabel="fluorescence",
        #     events=spike_events,
        # )
        # viewer.window.add_dock_widget(line_plot, name="Fluorescence trace")

        def update_line(event=None):
            current_frame = viewer.dims.point[0]
            line_plot.current_x = current_frame

        viewer.dims.events.current_step.connect(update_line)

        def update_plot(cell_indices):
            line_plot.displayed_traces = cell_indices
            current_frame = viewer.dims.point[0]
            line_plot.current_x = current_frame

        def update_selection(selected_index):
            if selected_index is not None:
                selected_contour = selected_index - 1

                # clear any current selections
                contour_manager.selected_contours = {}
                selected_shapes.selected_data = np.arange(
                    len(selected_shapes.data)
                )
                selected_shapes.remove_selected()
                line_plot.displayed_traces = {}

                if selected_contour != -1:
                    contour_manager.selected_contours = {selected_contour}
                    selection_bbox = []
                    contour = contour_manager.contours[selected_contour]
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
                    selected_shapes.add(
                        selection_bbox,
                        shape_type="rectangle",
                        face_color="transparent",
                        edge_color="green",
                    )
                    update_plot(cell_indices=[selected_contour])

            else:
                line_plot.clear()

        def select_on_click(viewer, event):
            selected_layers = viewer.layers.selected
            if len(selected_layers) == 1:

                if isinstance(selected_layers[0], napari.layers.Labels):
                    selected_index = selected_layers[0]._value
                    update_selection(selected_index)
                elif (snr_mask is not None) and (snr is not None):
                    if selected_layers[0] is snr_extension.image_layer:
                        visual = viewer.window.qt_viewer.layer_to_visual[
                            good_labels
                        ]
                        pos = list(event.pos)
                        good_labels.position = visual._transform_position(pos)
                        selected_index = good_labels._get_value()

                        if selected_index is not None:
                            update_selection(selected_index)
            yield

        viewer.mouse_drag_callbacks.append(select_on_click)

        @viewer.bind_key("t")
        def toggle_selected_contour(viewer):
            selected_contours = list(contour_manager.selected_contours)
            if len(selected_contours) > 0:
                good_contour = contour_manager.good_contour
                good_contour[selected_contours] = ~good_contour[
                    selected_contours
                ]
                contour_manager.good_contour = good_contour

                good_contours_image = contour_manager.make_accepted_mask()
                bad_contours_image = contour_manager.make_rejected_mask()

                good_labels.data = good_contours_image
                bad_labels.data = bad_contours_image

        @viewer.bind_key("q")
        def save_cells(viewer):
            snr_thresh = snr_extension.threshold
            accepted_cells_indices = np.argwhere(
                snr[contour_manager.good_contour] > snr_thresh
            )
            accepted_cells = np.zeros((f.shape[0],))
            accepted_cells[accepted_cells_indices] = 1
            if cells is not None:
                good_cells = np.hstack(
                    (
                        np.expand_dims(accepted_cells, 1),
                        np.expand_dims(cells[:, 1], 1),
                    )
                )
            else:
                good_cells = accepted_cells
            np.save(output, good_cells)

        viewer.show()
