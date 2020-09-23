from typing import Union
import os

import dask.array as da
import h5py
import numpy as np
from skimage import measure

from ...contour_manager import ContourManager
from ...images.masks import make_scalar_mask
from ..utils.data_range import calc_data_range
from ._vendored import load_dict_from_hdf5, load_memmap


def make_caiman_contour_manager(
    img_components: np.ndarray, good_indices: Union[list, np.ndarray]
) -> ContourManager:
    contours = [measure.find_contours(comp, 40)[0] for comp in img_components]
    initial_state = np.zeros((len(contours),), dtype=np.bool)
    initial_state[good_indices] = True
    contour_manager = ContourManager(
        contours,
        initial_state=initial_state,
        im_shape=img_components[0, ...].shape,
    )

    return contour_manager


def load_movie(filename: str, dataset_name: str = 'mov'):
    """Adapted from caiman


    """
    file_ext = os.path.splitext(filename)[-1]

    if file_ext in ['.hdf5', '.hdf']:
        image_path = filename
        f = h5py.File(image_path, "r")
        im = f[dataset_name]
        im_shape = im.shape
        images = da.from_array(im, chunks=(1, im_shape[-2], im_shape[-1]))
    elif file_ext == '.mmap':
        Yr, dims, T = load_memmap(filename)
        images = np.reshape(Yr.T, [T] + list(dims), order="C")
    else:
        raise IOError(f'{file_ext} files cannot be read')

    return images


def caiman_reader(
    pipeline_params,
    image_path,
    snr_path=None,
    trace_path=None,
    cell_path=None,
    spikes_path=None,
):

    # Load the image
    im_registered = load_movie(image_path)
    data_range = calc_data_range(im_registered)

    # load the pipeline output object
    cnm_obj = load_dict_from_hdf5(pipeline_params)

    # make the contours
    estimates = cnm_obj["estimates"]
    if estimates["dims"] is None:
        estimates["dims"] = im_registered.shape[1::]
    img_components = (
        estimates["A"]
        .toarray()
        .reshape((estimates["dims"][0], estimates["dims"][1], -1), order="F")
        .transpose([2, 0, 1])
    )
    img_components = (
        img_components / img_components.max(axis=(1, 2))[:, None, None]
    )
    img_components = img_components * 255
    estimates["img_components"] = img_components.astype(np.uint8)
    contour_manager = make_caiman_contour_manager(
        estimates["img_components"], good_indices=estimates["idx_components"]
    )

    # calculate the SNR and make the mask
    snr = estimates["SNR_comp"]
    im_shape = im_registered.shape
    contours = [
        measure.find_contours(comp, 40)[0]
        for comp in estimates["img_components"]
    ]
    snr_mask = make_scalar_mask(
        contours, im_shape=(im_shape[-2], im_shape[-1]), values=snr
    )

    # get the fluorescence data
    f_traces = estimates["C"] + estimates["YrA"]

    # caiman doesn't use spikes and is_cell for now
    is_cell = None
    spikes = None

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
