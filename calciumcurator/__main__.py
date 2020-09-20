import argparse

from .calcium_curator import calcium_curator
from .io.caiman.caiman_reader import caiman_reader
from .io.s2p.s2p_reader import s2p_reader


READER_FUNCS = {"s2p": s2p_reader, "caiman": caiman_reader}


def parse_args():
    parser = argparse.ArgumentParser(description="CalciumCurator")
    parser.add_argument("--pipeline", default="", type=str, help="options")
    parser.add_argument(
        "--pipeline-params", default="", type=str, help="options"
    )
    parser.add_argument("--image", default="", type=str, help="options")
    parser.add_argument("--snr", default="", type=str, help="options")
    parser.add_argument("--trace", default="", type=str, help="options")
    parser.add_argument("--cell", default="", type=str, help="options")
    parser.add_argument("--spikes", default="", type=str, help="options")
    parser.add_argument("--output", default=".", type=str, help="options")

    args = parser.parse_args()

    pipeline_name = args.pipeline
    pipeline_params = args.pipeline_params
    image_path = args.image
    snr_path = args.snr
    trace_path = args.trace
    cell_path = args.cell
    spikes_path = args.spikes
    output_dir = args.output

    return (
        pipeline_name,
        pipeline_params,
        image_path,
        snr_path,
        trace_path,
        cell_path,
        spikes_path,
        output_dir,
    )


def main():
    (
        pipeline_name,
        pipeline_params,
        image_path,
        snr_path,
        trace_path,
        cell_path,
        spikes_path,
        output_dir,
    ) = parse_args()

    try:
        reader_func = READER_FUNCS[pipeline_name]
    except KeyError:
        raise KeyError("unknown pipline. valid options are s2p and caiman")

    (
        im_registered,
        data_range,
        contour_manager,
        f_traces,
        snr,
        snr_mask,
        spikes,
        is_cell,
    ) = reader_func(
        pipeline_params,
        image_path,
        snr_path,
        trace_path,
        cell_path,
        spikes_path,
    )

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
