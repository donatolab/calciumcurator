import warnings

import numpy as np
from napari.layers.utils.layer_utils import calc_data_range
from skimage import measure

from ...contour_manager import ContourManager
from ...images.masks import make_scalar_mask


def make_caiman_contour_manager(img_components: np.ndarray) -> ContourManager:
    contours = [measure.find_contours(comp, 40)[0] for comp in img_components]
    contour_manager = ContourManager(
        contours, initial_state="good", im_shape=img_components[0, ...].shape
    )

    return contour_manager


def caiman_reader(
    pipeline_params,
    image_path,
    snr_path=None,
    trace_path=None,
    cell_path=None,
    spikes_path=None,
):
    # we lazy load the caiman dependencies so it is not required
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)
        from caiman import load as cm_load
        from caiman.source_extraction.cnmf.cnmf import load_CNMF

    # Load the image
    print(image_path)
    im_registered = cm_load(image_path)
    data_range = calc_data_range(im_registered)

    # load the pipeline output object
    cnm_obj = load_CNMF(pipeline_params)

    # make the contours
    estimates = cnm_obj.estimates
    estimates.img_components = (
        estimates.A.toarray()
        .reshape((estimates.dims[0], estimates.dims[1], -1), order="F")
        .transpose([2, 0, 1])
    )
    estimates.img_components /= estimates.img_components.max(axis=(1, 2))[:, None, None]
    estimates.img_components *= 255
    estimates.img_components = estimates.img_components.astype(np.uint8)
    contour_manager = make_caiman_contour_manager(estimates.img_components)

    # calculate the SNR and make the mask
    snr = cnm_obj.estimates.SNR_comp
    im_shape = im_registered.shape
    contours = [measure.find_contours(comp, 40)[0] for comp in estimates.img_components]
    snr_mask = make_scalar_mask(
        contours, im_shape=(im_shape[-2], im_shape[-1]), values=snr
    )

    # get the fluorescence data
    f_traces = estimates.C + estimates.YrA

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