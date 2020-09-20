from typing import Tuple

import numpy as np


def make_scalar_mask(
    masks, im_shape: Tuple[int, int], values: np.ndarray
) -> np.ndarray:
    mask_im = np.zeros(im_shape)

    for mask, value in zip(masks, values):
        mask_im[
            np.round(mask[:, 0]).astype("int"),
            np.round(mask[:, 1]).astype("int"),
        ] = value

    return mask_im
