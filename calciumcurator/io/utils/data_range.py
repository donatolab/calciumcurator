import numpy as np


def calc_data_range(data):
    """Calculate range of data values. If all values are equal return [0, 1].
    Parameters

    Adapted from
    https://github.com/napari/napari/blob/master/napari/layers/utils/layer_utils.py
    ----------
    data : array
        Data to calculate range of values over.
    Returns
    -------
    values : list of float
        Range of values.
    """
    bottom_plane_idx = (0,) * (data.ndim - 2)
    middle_plane_idx = tuple(s // 2 for s in data.shape[:-2])
    top_plane_idx = tuple(s - 1 for s in data.shape[:-2])
    idxs = [bottom_plane_idx, middle_plane_idx, top_plane_idx]
    reduced_data = [
        [np.max(data[idx]) for idx in idxs],
        [np.min(data[idx]) for idx in idxs],
    ]

    min_val = np.min(reduced_data)
    max_val = np.max(reduced_data)

    if min_val == max_val:
        min_val = 0
        max_val = 1
    return [float(min_val), float(max_val)]
