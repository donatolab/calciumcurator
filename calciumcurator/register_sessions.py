from itertools import cycle
import os

import h5py
import napari
import numpy as np
from skimage.filters import threshold_li
from skimage import measure
from skimage.registration import optical_flow_tvl1
from skimage.transform import warp

from calciumcurator.qt.registration_widgets import ModeControls


def get_cells(fname):
    with h5py.File(fname, 'r') as f:
        cells = f['A'].value

    return np.moveaxis(cells, [0, 1, 2], [2, 1, 0])


def load_data(fname):
    cells = get_cells(fname)

    return cells / np.max(cells)


def register_image(image_1, image_2):
    v, u = optical_flow_tvl1(np.max(image_1, 0), np.max(image_2, 0))

    # --- Use the estimated optical flow for registration
    nr, nc = image_1.shape[1::]
    row_coords, col_coords = np.meshgrid(
        np.arange(nr), np.arange(nc), indexing='ij'
    )

    image2_warp = []
    for plane in image_2:
        image2_warp.append(
            warp(
                plane,
                np.array([row_coords + v, col_coords + u]),
                mode='nearest',
            )
        )
    image2_warp = np.asarray(image2_warp)

    return image2_warp


def segment_cells(image):
    labels_image = np.zeros(image.shape[1::])
    all_contours = []
    for i, cell in enumerate(image):
        thresh = threshold_li(cell) * 1.2
        mask = cell > thresh
        labels_image[mask] = i + 1
        contours = measure.find_contours(cell, thresh)
        # if there is more than one contour found, take the biggest one
        if len(contours) > 1:
            all_lengths = [len(c) for c in contours]
            selected_contour = contours[np.argmax(all_lengths)]
        else:
            selected_contour = contours[0]
        all_contours.append(selected_contour)

    return labels_image, all_contours


def make_layer(fname, contours, next_cell_id, face_color=None):
    n_cells = len(contours)
    cell_id_start = next_cell_id
    cell_id_finish = cell_id_start + n_cells

    cell_id = np.arange(cell_id_start, cell_id_finish)
    layer_properties = {
        'filename': np.asarray([fname] * n_cells),
        'cell_id_orig': cell_id,
        'cell_id': cell_id.copy(),
        'displayed': np.ones((n_cells,), dtype=np.bool),
    }

    if face_color is not None:
        face_color = next(face_color)
    else:
        face_color = face_color

    layer_dict = {
        'data': contours,
        'properties': layer_properties,
        'shape_type': 'polygon',
        'face_color': face_color,
        'edge_color': [1, 1, 1, 1],
        'opacity': 0.7,
        'name': os.path.basename(fname),
    }

    return layer_dict


files = [
    '/Users/yamauc0000/Documents/align_test/OF.mat',
    '/Users/yamauc0000/Documents/align_test/TM.mat',
    '/Users/yamauc0000/Documents/align_test/TM40.mat',
]
data = [load_data(f) for f in files]

# register the data
registered_cells = []
for i, d in enumerate(data):
    if i == 0:
        registered_cells.append(d)
    else:
        registered_cells.append(register_image(data[0], d))

# get the labels and contours
all_labels = []
all_contours = []
for i, cell_image in enumerate(registered_cells):
    l, c = segment_cells(cell_image)
    all_labels.append(l)
    all_contours.append(c)


# make the layer data
face_color_cycle = cycle(['blue', 'green', 'magenta'])
layer_data = []
next_cell_id = 0
layer_colors = {}

for f, c in zip(files, all_contours):
    layer = make_layer(f, c, next_cell_id, face_color_cycle)
    layer_data.append(layer)

    # save the layer colors
    layer_colors[layer['name']] = layer['face_color']

    next_cell_id += len(c)


class GuiData:
    def __init__(
        self, layer_names, template_layer, template_id, selection_layer
    ):
        self.layer_names = layer_names
        self.template_layer = template_layer
        self.template_id = template_id
        self.selection_layer = selection_layer


layer_names = [l['name'] for l in layer_data]
gui_data = GuiData(
    layer_names=layer_names,
    template_layer=layer_names[0],
    template_id=0,
    selection_layer=layer_names[1],
)
# state variables
# LAYER_NAMES = [l['name'] for l in layer_data]
# TEMPLATE_LAYER = LAYER_NAMES[0]
# TEMPLATE_ID = 0
# SELECTION_LAYER = LAYER_NAMES[1]

# colors
TEMPLATE_CELL_COLOR = np.array([0, 1, 0, 1])
TEMPLATE_LAYER_COLOR = np.array([0, 0, 0, 0])
TEMPLATE_EDGE_COLOR = np.array([1, 1, 1, 1])
SELECTION_LAYER_COLOR = np.array([0, 0, 1, 0.5])
SELECTION_EDGE_COLOR = np.array([0, 0, 1, 1])

with napari.gui_qt():
    # set up the viewer
    for i, ld in enumerate(layer_data):
        if i == 0:
            viewer = napari.view_shapes(**ld)
        else:
            viewer.add_shapes(**ld)

    def set_template_layer():
        # set up the template layer
        t_layer = viewer.layers[gui_data.template_layer]
        t_layer.visible = True

        # set the edge_color
        t_layer.edge_color = TEMPLATE_EDGE_COLOR

        # set up the face color
        t_layer_props = t_layer.properties
        t_face_color_cycle = {
            c_id: TEMPLATE_LAYER_COLOR for c_id in t_layer_props['cell_id']
        }
        t_face_color_cycle[gui_data.template_id] = TEMPLATE_CELL_COLOR
        t_layer.face_color = 'cell_id'
        t_layer.face_color_cycle_map = t_face_color_cycle
        t_layer.face_color_mode = 'cycle'
        t_layer.refresh_colors()

        # set the opacity
        t_layer.opacity = 0.7

        set_selection_layer(gui_data.selection_layer)

    def set_selection_layer(layer_name):
        # get the selection layer
        s_layer = viewer.layers[layer_name]

        # make the selection layer visible
        s_layer.visible = True

        # set the edge_color
        s_layer_props = s_layer.properties
        s_edge_color_cycle = {
            c_id: SELECTION_EDGE_COLOR for c_id in s_layer_props['cell_id']
        }
        s_edge_color_cycle[gui_data.template_id] = TEMPLATE_CELL_COLOR
        s_layer.edge_color_cycle_map = s_edge_color_cycle
        s_layer.edge_color = 'cell_id'
        s_layer.edge_color_mode = 'cycle'

        # set the face_color and opacity
        s_layer.face_color = SELECTION_LAYER_COLOR
        s_layer.opacity = 0.5

        # select the mode and layer
        viewer.layers.unselect_all()
        s_layer.selected = True
        s_layer.mode = 'select'

        # make all other layers invisble
        for l in gui_data.layer_names:
            if l not in [gui_data.template_layer, gui_data.selection_layer]:
                viewer.layers[l].visible = False

    def assign_cell():
        s_layer = viewer.layers[gui_data.selection_layer]
        if len(s_layer.selected_data) > 0:
            selected_cells = list(s_layer.selected_data)
            cell_ids = s_layer.properties['cell_id']
            orig_cell_ids = s_layer.properties['cell_id_orig']
            for cell in selected_cells:
                if cell_ids[cell] == orig_cell_ids[cell]:
                    cell_ids[cell] = gui_data.template_id
                else:
                    cell_ids[cell] = orig_cell_ids[cell]
            s_layer.properties['cell_id'] = cell_ids
            s_layer.refresh_colors()

    init_selection_layers = gui_data.layer_names[1::]
    template_ids = [
        str(id)
        for id in viewer.layers[gui_data.template_layer].properties['cell_id']
    ]
    mode_widget = ModeControls(
        layer_names=gui_data.layer_names,
        selection_layers=init_selection_layers,
        template_ids=template_ids,
    )

    def update_template_layer(layer_name=None):
        if layer_name is not None:
            if gui_data.template_layer != layer_name:
                gui_data.template_layer = layer_name

                # if the new template layer was the selection layer,
                # choose the first available one
                new_selection_layers = []
                for ln in gui_data.layer_names:
                    if ln != layer_name:
                        new_selection_layers.append(l)
                mode_widget.registration_controls.selection_combo.clear()
                mode_widget.registration_controls.selection_combo.addItems(
                    new_selection_layers
                )

                new_template_cells = [
                    str(id)
                    for id in np.unique(
                        viewer.layers[layer_name].properties['cell_id']
                    )
                ]
                mode_widget.registration_controls.template_cell_combo.clear()
                mode_widget.registration_controls.template_cell_combo.addItems(
                    new_template_cells
                )

                if layer_name == gui_data.selection_layer:
                    gui_data.selection_layer = new_selection_layers[0]

                set_template_layer()

    def update_template_cell(cell_id):
        cell_id = int(cell_id)
        if cell_id != gui_data.template_id and cell_id != '':
            gui_data.template_id = cell_id
            set_template_layer()

    def update_selection_layer(layer_name):
        if layer_name != gui_data.selection_layer and layer_name != '':
            gui_data.selection_layer = layer_name
            set_selection_layer(layer_name)

    mode_widget.registration_button.clicked.connect(set_template_layer)
    mode_widget.registration_controls.assign_button.clicked.connect(
        assign_cell
    )
    mode_widget.registration_controls.template_combo.currentTextChanged.connect(
        update_template_layer
    )
    mode_widget.registration_controls.template_cell_combo.currentTextChanged.connect(
        update_template_cell
    )
    mode_widget.registration_controls.selection_combo.currentTextChanged.connect(
        update_selection_layer
    )
    viewer.window.add_dock_widget(mode_widget, name='mode', area='right')
