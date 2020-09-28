import os

import dask.array as da
import h5py
import numpy as np
from skimage import measure

from ...images.masks import make_scalar_mask
from ..utils.data_range import calc_data_range
from ._vendored import load_dict_from_hdf5, load_memmap


def make_caiman_cell_masks(img_components: np.ndarray) -> list:
    cell_masks = [
        measure.find_contours(comp, 40)[0] for comp in img_components
    ]

    return cell_masks


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
    cell_masks = make_caiman_cell_masks(estimates["img_components"])

    good_indices = estimates["idx_components"]
    initial_cell_masks_state = np.zeros((len(cell_masks),), dtype=np.bool)
    initial_cell_masks_state[good_indices] = True

    # calculate the SNR and make the mask
    snr = estimates["SNR_comp"]
    im_shape = im_registered.shape
    snr_mask = make_scalar_mask(
        cell_masks, im_shape=(im_shape[-2], im_shape[-1]), values=snr
    )

    # get the fluorescence data
    f_traces = estimates["C"] + estimates["YrA"]

    # caiman doesn't use spikes and is_cell for now
    is_cell = None
    spikes = None

    return (
        im_registered,
        data_range,
        cell_masks,
        initial_cell_masks_state,
        f_traces,
        snr,
        snr_mask,
        spikes,
        is_cell,
    )
