import argparse
import os

import napari
from skimage import io

from .calcium_curator import CalciumCurator
from .io.caiman.caiman_reader import caiman_reader
from .io.caiman._vendored import load_dict_from_hdf5


def parse_args():
    parser = argparse.ArgumentParser(description="view-caiman")
    parser.add_argument("--results", default="", type=str, help="options")
    parser.add_argument("--image", default="", type=str, help="options")
    parser.add_argument("--mip", default="", type=str, help="options")
    parser.add_argument("--output", default="", type=str, help="options")

    args = parser.parse_args()
    results_file = args.results
    image_path = args.image
    mip_path = args.mip
    output_dir = args.output

    return results_file, image_path, output_dir, mip_path


def view_caiman():
    results_file, image_path, output_dir, mip_path = parse_args()

    cnm_obj = load_dict_from_hdf5(results_file)

    if image_path == "":
        # first check if there's a motion corrected hdf5 file
        # if not, try the caiman mmap file
        results_base = os.path.splitext(results_file)[0]
        image_path = results_base + '_mcorr.hdf5'
        if not os.path.isfile(image_path):
            results_dir = os.path.dirname(results_file)
            im_name_base = os.path.basename(
                os.path.splitext(cnm_obj['mmap_file'])[0]
            )
            image_path_base = os.path.join(results_dir, im_name_base)
            image_path = image_path_base + '.mmap'

            if not os.path.isfile(image_path):
                raise FileNotFoundError(
                    "Image file not found in results directory.\n"
                    "Try passing the image file path with the --image argument"
                )

    (
        im_registered,
        data_range,
        cell_masks,
        initial_cell_masks_state,
        f_traces,
        snr,
        snr_mask,
        spikes,
        is_cell,
    ) = caiman_reader(results_file, image_path)

    if mip_path == "":
        mip = None
    else:
        mip = io.imread(mip_path)

    with napari.gui_qt():
        CalciumCurator(
            img=im_registered,
            data_range=data_range,
            cell_masks=cell_masks,
            mip=mip,
            initial_cell_masks_state=initial_cell_masks_state,
            f=f_traces,
            snr=snr,
            snr_mask=snr_mask,
            spikes=spikes,
            output=output_dir,
            cells=is_cell,
        )
