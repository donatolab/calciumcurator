import os
import pathlib
from typing import Any, Dict, Tuple

import h5py
import numpy as np
from scipy import sparse

"""
Code from Caiman utils

https://github.com/flatironinstitute/CaImAn/blob/e2de6f3350342f2f5762279b7059bdb739d58d84/caiman/utils/utils.py


"""

# \package Caiman/utils
# \version   1.0
# \bug
# \warning
# \copyright GNU General Public License v2.0
# \date Created on Tue Jun 30 21:01:17 2015
# \author: andrea giovannucci
# \namespace utils
# \pre none


def load_dict_from_hdf5(filename: str) -> Dict:
    """ Load dictionary from hdf5 file
    Args:
        filename: str
            input file to load
    Returns:
        dictionary
    """

    with h5py.File(filename, "r") as h5file:
        return recursively_load_dict_contents_from_group(h5file, "/")


def recursively_load_dict_contents_from_group(
    h5file: h5py.File, path: str
) -> Dict:
    """load dictionary from hdf5 object
    Args:
        h5file: hdf5 object
            object where dictionary is stored
        path: str
            path within the hdf5 file
    """

    ans: Dict = {}
    for key, item in h5file[path].items():

        if isinstance(item, h5py._hl.dataset.Dataset):
            val_set = np.nan
            if isinstance(item[()], str):
                if item[()] == "NoneType":
                    ans[key] = None
                else:
                    ans[key] = item[()]

            elif key in [
                "dims",
                "medw",
                "sigma_smooth_snmf",
                "dxy",
                "max_shifts",
                "strides",
                "overlaps",
            ]:

                if type(item[()]) == np.ndarray:
                    ans[key] = tuple(item[()])
                else:
                    ans[key] = item[()]
            else:
                if type(item[()]) == np.bool_:
                    ans[key] = bool(item[()])
                else:
                    ans[key] = item[()]

        elif isinstance(item, h5py._hl.group.Group):
            if key in ("A", "W", "Ab", "downscale_matrix", "upscale_matrix"):
                data = item[path + key + "/data"]
                indices = item[path + key + "/indices"]
                indptr = item[path + key + "/indptr"]
                shape = item[path + key + "/shape"]
                ans[key] = sparse.csc_matrix(
                    (data[:], indices[:], indptr[:]), shape[:]
                )
                if key in ("W", "upscale_matrix"):
                    ans[key] = ans[key].tocsr()
            else:
                ans[key] = recursively_load_dict_contents_from_group(
                    h5file, path + key + "/"
                )
    return ans


def prepare_shape(mytuple: Tuple) -> Tuple:
    """ This promotes the elements inside a shape into np.uint64. It is intended to prevent overflows
        with some numpy operations that are sensitive to it, e.g. np.memmap """
    if not isinstance(mytuple, tuple):
        raise Exception("Internal error: prepare_shape() passed a non-tuple")
    return tuple(map(lambda x: np.uint64(x), mytuple))


def load_memmap(filename: str, mode: str = "r") -> Tuple[Any, Tuple, int]:
    """ Load a memory mapped file created by the function save_memmap
    Args:
        filename: str
            path of the file to be loaded
        mode: str
            One of 'r', 'r+', 'w+'. How to interact with files
    Returns:
        Yr:
            memory mapped variable
        dims: tuple
            frame dimensions
        T: int
            number of frames
    Raises:
        ValueError "Unknown file extension"
    """
    if pathlib.Path(filename).suffix != ".mmap":
        raise ValueError("Unknown file extension (should be .mmap)")
    # Strip path components and use CAIMAN_DATA/example_movies
    # TODO: Eventually get the code to save these in a different dir
    file_to_load = filename
    filename = os.path.split(filename)[-1]
    fpart = filename.split("_")[
        1:-1
    ]  # The filename encodes the structure of the map
    d1, d2, d3, T, order = (
        int(fpart[-9]),
        int(fpart[-7]),
        int(fpart[-5]),
        int(fpart[-1]),
        fpart[-3],
    )
    Yr = np.memmap(
        file_to_load,
        mode=mode,
        shape=prepare_shape((d1 * d2 * d3, T)),
        dtype=np.float32,
        order=order,
    )
    if d3 == 1:
        return (Yr, (d1, d2), T)
    else:
        return (Yr, (d1, d2, d3), T)
