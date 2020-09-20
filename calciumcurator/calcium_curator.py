from typing import Optional

import napari
import numpy as np

from .contour_manager import ContourManager
from .qt.plots import LinePlot
from .qt.dock_widgets import HistogramWidget

from .images.masks import make_scalar_mask


def calcium_curator(
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

    with napari.gui_qt():
        viewer = napari.view_image(
            img, multiscale=False, contrast_limits=data_range, visible=True
        )

        # add the SNR widgets
        if (snr_mask is not None) and (snr is not None):
            snr_image = viewer.add_image(snr_mask, visible=False)
            bins = np.linspace(np.int(snr.min()), np.int(snr.max()), 20)
            y, x = np.histogram(snr, bins=bins)
            hist = HistogramWidget(x, y, xlabel="SNR", ylabel="counts")

            def snr_dragged(event=None):
                snr_thresh = hist.hist_plot._vert_line.getPos()[0]
                if np.sum(contour_manager.good_contour) > 0:
                    good_snr_indices = np.squeeze(
                        np.argwhere(
                            snr[contour_manager.good_contour] > snr_thresh
                        )
                    )
                    if good_snr_indices.ndim != 0:
                        good_masks = [
                            contour_manager.accepted_contours[i]
                            for i in good_snr_indices
                        ]
                        good_snr = snr[contour_manager.good_contour][
                            good_snr_indices
                        ]
                        im_shape = (img.shape[-2], img.shape[-1])
                        new_snr_mask = make_scalar_mask(
                            good_masks, im_shape, good_snr
                        )
                        snr_image.data = new_snr_mask

            # update the SNR image and connect the event
            snr_dragged()
            hist.hist_plot.connect_line_dragged(snr_dragged)

            viewer.window.add_dock_widget(hist, name="SNR histogram")

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
            x=t,
            y=f[0],
            xlabel="time",
            ylabel="fluorescence",
            events=spike_events,
        )
        viewer.window.add_dock_widget(line_plot, name="Fluorescence trace")

        def update_line(event=None):
            current_frame = viewer.dims.point[0]
            line_plot.update_vline(current_frame)

        viewer.dims.events.axis.connect(update_line)

        def update_plot(cell_indices):
            for i in cell_indices:
                data = f[i]
                if spikes is not None:
                    spike_events = spikes[i] > 25
                else:
                    spike_events = None
                line_plot.plot(data, spike_events)
                current_frame = viewer.dims.point[0]
                line_plot.update_vline(current_frame)

        def update_selection(selected_index):
            if selected_index is not None:
                selected_contour = selected_index - 1

                # clear any current selections
                contour_manager.selected_contours = {}
                selected_shapes.selected_data = np.arange(
                    len(selected_shapes.data)
                )
                selected_shapes.remove_selected()

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
                    if selected_layers[0] is snr_image:
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

                if (snr_mask is not None) and (snr is not None):
                    snr_dragged()

        @viewer.bind_key("q")
        def save_cells(viewer):
            snr_thresh = hist.hist_plot._vert_line.getPos()[0]
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
