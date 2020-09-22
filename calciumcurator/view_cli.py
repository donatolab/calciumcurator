import argparse
import os

from .calcium_curator import calcium_curator
from .io.caiman.caiman_reader import caiman_reader
from .io.caiman._vendored import load_dict_from_hdf5


def parse_args():
    parser = argparse.ArgumentParser(description="view-caiman")
    parser.add_argument("--results", default="", type=str, help="options")
    parser.add_argument("--image", default="", type=str, help="options")
    parser.add_argument("--output", default="", type=str, help="options")

    args = parser.parse_args()
    results_file = args.results
    image_path = args.image
    output_dir = args.output

    return results_file, image_path, output_dir


def view_caiman():
    results_file, image_path, output_dir = parse_args()

    cnm_obj = load_dict_from_hdf5(results_file)

    if image_path == "":
        im_name_base = os.path.basename(
            os.path.splitext(cnm_obj['mmap_file'])[0]
        )
        results_dir = os.path.dirname(results_file)
        image_path_base = os.path.join(results_dir, im_name_base)
        # first check if there's a motion corrected hdf5 file
        # if not, try the caiman mmap file
        if os.path.isfile(image_path_base + '_mcorr.hdf5'):
            image_path = image_path_base + '_mcorr.hdf5'
        else:
            image_path = image_path_base + '.mmap'
        if not os.path.isfile(image_path):
            raise FileNotFoundError(
                "Image file not found in results directory.\n"
                "Try passing the image file path with the --image argument"
            )

    (
        im_registered,
        data_range,
        contour_manager,
        f_traces,
        snr,
        snr_mask,
        spikes,
        is_cell,
    ) = caiman_reader(results_file, image_path)

    calcium_curator(
        img=im_registered,
        data_range=data_range,
        contour_manager=contour_manager,
        f=f_traces,
        snr=snr,
        snr_mask=snr_mask,
        spikes=spikes,
        output=output_dir,
        cells=is_cell,
    )
