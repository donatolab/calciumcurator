from typing import Optional, Union

import napari
from napari._qt.qt_error_notification import NapariNotification
import numpy as np

from .extensions import CellMask, LinePlot, ThresholdImage
from .qt.mode_controls import ModeControls


class CalciumCurator:
    def __init__(
        self,
        img: np.ndarray,
        data_range,
        cell_masks: np.ndarray,
        mip: Optional[np.ndarray] = None,
        initial_cell_masks_state: Union[str, np.ndarray] = 'good',
        f: Optional[np.ndarray] = None,
        spikes: Optional[np.ndarray] = None,
        snr: Optional[np.ndarray] = None,
        snr_mask: Optional[np.ndarray] = None,
        cells: Optional[np.ndarray] = None,
        output: str = "iscell_curated.npy",
    ):
        self.viewer = napari.view_image(
            img,
            multiscale=False,
            contrast_limits=data_range,
            visible=True,
            name='movie',
        )
        if mip is not None:
            self.mip = self.viewer.add_image(
                mip, name='MIP', colormap='viridis', visible=False
            )
        else:
            self.mip = None
        # todo: add this to snr extension
        self.snr = snr
        self.f = f
        self.save_path = output

        self.movie = self.viewer.layers['movie']

        # add the SNR widgets
        if (snr_mask is not None) and (snr is not None):
            self.snr_extension = ThresholdImage(
                image=snr_mask,
                viewer=self.viewer,
                xlabel='SNR',
                ylabel='counts',
                image_layer_name='SNR mask',
                name='SNR histogram',
            )

        # # Add the cell labels
        self.cell_masks = CellMask(
            viewer=self.viewer,
            im_shape=img.shape[-2::],
            cell_masks=cell_masks,
            initial_state=initial_cell_masks_state,
        )

        t = np.arange(len(f[0]))
        if spikes is not None:
            spike_events = spikes[0] > 50
        else:
            spike_events = None
        self.line_plot = LinePlot(
            viewer=self.viewer,
            x=t,
            y=f,
            xlabel="time",
            ylabel="fluorescence",
            event_indices=spike_events,
        )

        def update_line(event=None):
            current_frame = self.viewer.dims.point[0]
            self.line_plot.current_x = current_frame

        self.viewer.dims.events.current_step.connect(update_line)

        def select_on_click(viewer, event):
            selected_layers = viewer.layers.selected
            if len(selected_layers) == 1:

                if isinstance(selected_layers[0], napari.layers.Labels):
                    selected_index = selected_layers[0]._value

                    if selected_index is not None:
                        selected_index = [selected_index - 1]
                        self.selected_cell = np.array(
                            selected_index, dtype=np.int
                        )
                elif (snr_mask is not None) and (snr is not None):
                    if selected_layers[0] is self.snr_extension.image_layer:
                        visual = viewer.window.qt_viewer.layer_to_visual[
                            self.cell_masks.accepted_labels
                        ]
                        pos = list(event.pos)
                        self.cell_masks.accepted_labels.position = visual._transform_position(
                            pos
                        )
                        selected_index = (
                            self.cell_masks.accepted_labels._get_value()
                        )

                        if selected_index is not None:
                            self.selected_cell = [selected_index - 1]
            yield

        self.viewer.mouse_drag_callbacks.append(select_on_click)

        self.mode_controls = ModeControls(
            n_cells=len(self.cell_masks.masks.contours)
        )
        self.mode_controls.manual_curation_controls.manual_mode_button.clicked.connect(
            self._on_manual_mode_clicked
        )
        self.mode_controls.manual_curation_controls.focus_mode_button.clicked.connect(
            self._on_focus_mode_clicked
        )
        self.mode_controls.snr_mode_button.clicked.connect(
            self._on_snr_mode_clicked
        )
        self.mode_controls.manual_curation_controls.selected_cell_spinbox.valueChanged.connect(
            self._on_selected_cell_changed
        )
        self.mode_controls.save_button.clicked.connect(self.save_cells)
        self.viewer.window.add_dock_widget(
            self.mode_controls, name='mode', area='right'
        )

        self._dataset_loaded = True

        self.mode = 'all'
        self.selected_cell = [0]
        self.viewer.show()

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode: str):

        if mode == 'all':
            # set visibility
            self.cell_masks.accepted_labels.visible = True
            self.cell_masks.rejected_labels.visible = False
            self.snr_extension.image_layer.visible = False
            self.movie.visible = True

            # select layer
            self.cell_masks.accepted_labels.selected = True
            self.cell_masks.rejected_labels.selected = False
            self.snr_extension.image_layer.selected = False
            self.movie.selected = False

            # set the mode
            self.cell_masks.mode = 'all'

            # update the UI
            self.mode_controls.manual_curation_controls.manual_mode_button.setChecked(
                True
            )

        elif mode == 'focus':
            # set visibility
            self.cell_masks.accepted_labels.visible = True
            self.cell_masks.rejected_labels.visible = True
            self.snr_extension.image_layer.visible = False
            self.movie.visible = True

            # select layer
            self.cell_masks.accepted_labels.selected = True
            self.cell_masks.rejected_labels.selected = False
            self.snr_extension.image_layer.selected = False
            self.movie.selected = False

            # update the cell masks
            # if no cell is selected, select the first one
            if len(self.selected_cell) == 0:
                self.cell_masks.selected_mask = [0]
            self.cell_masks.mode = 'focus'

            # update the UI
            self.mode_controls.manual_curation_controls.focus_mode_button.setChecked(
                True
            )

        elif mode == 'snr_threshold':
            # set visibility
            self.cell_masks.accepted_labels.visible = False
            self.cell_masks.rejected_labels.visible = False
            self.snr_extension.image_layer.visible = True
            self.movie.visible = True

            # select layer
            self.cell_masks.accepted_labels.selected = False
            self.cell_masks.rejected_labels.selected = False
            self.snr_extension.image_layer.selected = True
            self.movie.selected = False

            # update the UI
            self.mode_controls.snr_mode_button.setChecked(True)

        else:
            raise ValueError(f'{mode} is not a recognized mode')

        self._mode = mode

    @property
    def dataset_loaded(self) -> bool:
        return self._dataset_loaded

    @property
    def selected_cell(self) -> set:
        return self.cell_masks.selected_mask

    @selected_cell.setter
    def selected_cell(self, selected_cell: Union[set, list]):
        self.cell_masks.selected_mask = set(selected_cell)
        self._update_selection()

        self.mode_controls.manual_curation_controls.selected_cell_spinbox.blockSignals(
            True
        )
        self.mode_controls.manual_curation_controls.selected_cell_spinbox.setValue(
            list(self.cell_masks.selected_mask)[0]
        )
        self.mode_controls.manual_curation_controls.selected_cell_spinbox.blockSignals(
            False
        )

    def _update_selection(self, selected_indices: Optional[np.ndarray] = None):
        selected_masks = np.asarray(list(self.cell_masks.selected_mask))
        if len(selected_masks) > 0:
            self.line_plot.displayed_traces = {}
            if np.all(selected_masks >= 0):
                self._update_plot(cell_indices=selected_masks)
        else:
            self.line_plot.clear()

    def save_cells(self, viewer):
        snr_thresh = self.snr_extension.threshold
        accepted_cells_indices = np.argwhere(
            self.snr[self.cell_masks.masks.good_contour] > snr_thresh
        )
        accepted_cells = np.zeros((self.f.shape[0],))
        accepted_cells[accepted_cells_indices] = 1

        good_cells = accepted_cells
        good_cells_path = self.save_path + '_iscell.npy'
        np.save(good_cells_path, good_cells)

        f_path = self.save_path + '_F.npy'
        np.save(f_path, self.f)

        path_message = f'files saved: {f_path}, {good_cells_path}'
        notification = NapariNotification(
            message=path_message, severity='info'
        )
        notification.show()

    def _update_plot(self, cell_indices):
        self.line_plot.displayed_traces = cell_indices
        current_frame = self.viewer.dims.point[0]
        self.line_plot.current_x = current_frame

    def _on_manual_mode_clicked(self):
        self.mode = 'all'

    def _on_focus_mode_clicked(self):
        self.mode = 'focus'

    def _on_snr_mode_clicked(self):
        self.mode = 'snr_threshold'

    def _on_selected_cell_changed(self):
        new_selection = (
            self.mode_controls.manual_curation_controls.selected_cell_spinbox.value()
        )
        self.selected_cell = [new_selection]
