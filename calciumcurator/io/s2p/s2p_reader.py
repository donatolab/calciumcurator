from typing import Any, Dict, Tuple

import dask.array as da
import h5py
from napari.layers.utils.layer_utils import calc_data_range
import numpy as np
import pandas as pd

from ...contour_manager import ContourManager
from ...images.masks import make_scalar_mask


def create_cell_mask(
    stat: Dict[str, Any], n_rows: int, n_cols: int, allow_overlap: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    from suite2p:
    https://github.com/MouseLand/suite2p/blob/d08f1a82561330d45142c0b6192ec779254e4533/suite2p/detection/masks.py#L22

    creates cell masks for ROIs in stat and computes radii

    Parameters
    ----------
    stat : dictionary 'ypix', 'xpix', 'lam'
    n_rows : y size of frame
    n_cols : x size of frame
    allow_overlap : whether or not to include overlapping pixels in cell masks

    Returns
    -------
    cell_masks : len ncells, each has tuple of pixels belonging to each cell and weights
    lam_normed
    """
    mask = ... if allow_overlap else ~stat["overlap"]
    cell_mask = np.ravel_multi_index(
        (stat["ypix"], stat["xpix"]), (n_rows, n_cols)
    )
    cell_mask = cell_mask[mask]
    lam = stat["lam"][mask]
    lam_normed = lam / lam.sum() if lam.size > 0 else np.empty(0)
    return cell_mask, lam_normed


def create_cell_labels_ims(
    stat_all: list, is_cell: np.ndarray, ops: dict,
) -> Tuple[np.ndarray, np.ndarray]:
    """Create a label images for the good and bad cells

    Parameters
    ----------
    stat_all : list
        The list of stat for each cell loaded from suite2p
    is_cell : np.ndarray
        This is the contents of the iscell.npy file
    ops : dict
        The options and intermediate outputs from s2p

    Returns
    -------
    good_cell_mask : np.ndarray
        A label image with each cell that passed QC in iscell.npy. Has the same shape
        as the source image.
    bad_cell_mask : np.ndarray
        A label image with each cell that failed QC in iscell.npy. Has the same shape
        as the source image.
    """

    # image shape
    n_rows = ops["Ly"]
    n_cols = ops["Lx"]

    cell_masks = [
        create_cell_mask(
            stat,
            n_rows=n_rows,
            n_cols=n_cols,
            allow_overlap=ops["allow_overlap"],
        )[0]
        for stat in stat_all
    ]

    good_cell_mask = np.zeros((n_rows, n_cols))
    bad_cell_mask = np.zeros((n_rows, n_cols))
    for cell_index, cell in enumerate(is_cell):
        cell_mask_indices = np.unravel_index(
            cell_masks[cell_index], (ops["Ly"], ops["Lx"])
        )
        if cell[0] == 1:
            good_cell_mask[cell_mask_indices] = cell_index
        else:
            bad_cell_mask[cell_mask_indices] = cell_index

    return good_cell_mask, bad_cell_mask


def create_cell_mask_indices(stat_all: list, ops: dict):
    n_rows = ops["Ly"]
    n_cols = ops["Lx"]

    cell_masks = [
        create_cell_mask(
            stat,
            n_rows=n_rows,
            n_cols=n_cols,
            allow_overlap=ops["allow_overlap"],
        )[0]
        for stat in stat_all
    ]

    cell_mask_indices = [
        np.vstack(np.unravel_index(cell, (ops["Ly"], ops["Lx"]))).T
        for cell in cell_masks
    ]

    return cell_mask_indices


def s2p_reader(
    pipeline_params, image_path, snr_path, trace_path, cell_path, spikes_path
):
    stat_all = np.load(pipeline_params, allow_pickle=True)
    is_cell = np.load(cell_path, allow_pickle=True)
    f_traces = np.load(trace_path, allow_pickle=True)
    spikes = np.load(spikes_path)

    # load the shifts
    ops = np.load("ops.npy", allow_pickle=True).item()
    y_offset = ops["yoff"]
    x_offset = ops["xoff"]
    offsets = np.vstack((y_offset, x_offset)).T

    def translate_slice(array, offsets, block_info=None):
        if block_info is not None:
            array_location = block_info[None]["array-location"]
            t_slice = array_location[0][0]
            registered_array = np.roll(
                array,
                (
                    -np.int16(offsets[t_slice][0]),
                    -np.int16(offsets[t_slice][1]),
                ),
                axis=(1, 2),
            )

        else:
            registered_array = array

        return registered_array

    f = h5py.File(image_path, "r")
    im = f["MSession_0/MUnit_0/Channel_0"]
    im_shape = im.shape
    da_im = da.from_array(im, chunks=(1, im_shape[-2], im_shape[-1]))
    data_range = calc_data_range(da_im)
    im_registered = da_im.map_blocks(translate_slice, offsets=offsets)

    # load SNR
    snr_df = pd.read_csv(snr_path)
    snr = snr_df["0"].values

    cell_mask_indicies = create_cell_mask_indices(stat_all, ops)
    initial_state = is_cell[:, 0].astype(np.bool)
    contour_manager = ContourManager(
        cell_mask_indicies,
        initial_state=initial_state,
        im_shape=(im_shape[-2], im_shape[-1]),
    )

    snr_mask = make_scalar_mask(
        cell_mask_indicies, im_shape=(im_shape[-2], im_shape[-1]), values=snr
    )

    return (
        im_registered,
        data_range,
        contour_manager,
        f_traces,
        snr,
        snr_mask,
        spikes,
        is_cell,
    )
