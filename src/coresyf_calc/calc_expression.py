#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import rasterio
import shutil
import subprocess
import tempfile
import sys

from pathlib2 import Path


"""This module provide simple raster calucation functionality"""


def get_inputs(folder, pattern="*.img"):
    """Return sorted list of input files matching pattern in folder"""
    return sorted(folder.glob(pattern))


def create_temp_copy(path):
    temp_dir = tempfile.gettempdir()
    temp_path = Path(temp_dir) / 'previous_file.img'
    shutil.copy2(str(path), str(temp_path))
    return temp_path


def build_target_path(input, target_folder):
    """Build target like target_folder/input"""
    return Path(target_folder / input.name)


def get_expression(offset=0, exp=None, scale=None):
    """Get the right expression by differend parameter combinations"""

    if (exp and not offset and not scale):
        return exp
    elif (not exp and not offset and scale):
        return "(A * {0})".format(scale)
    elif (not exp and offset and not scale):
        return "(A + {0})".format(offset)
    else:
        return "(A * {0}) + {1}".format(scale, offset)


def which(pgm):
    """Search for pgm in PATH"""
    path = os.getenv('PATH')
    for p in path.split(os.path.pathsep):
        p = os.path.join(p, pgm)
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p


def build_command(input, target, exp, no_data_value=None, previous=None):
    """build command for gdal_calc
    Set no data value explicitly from input file if not given as parameter.
    """
    if not no_data_value:
        with rasterio.open(str(input)) as ds:
            no_data_value = ds.nodata  # set explicit no_data value

    if exp and 'B' in exp:
        sourceraster = '-A "{}" -B "{}" '.format(input, previous)
    else:
        sourceraster = '-A "{}" '.format(input)

    # TODO: set creation option like comrpession

    command = "".join([
        sys.executable,
        ' ',
        which('gdal_calc.py'),
        ' ',
        sourceraster,
        ' ',
        '--outfile="{}" '.format(target),
        '--calc="{}" '.format(exp),
        '--NoDataValue="{}" '.format(no_data_value),
        '--type="Float32" ',
        '--format="HFA" ',
        '--overwrite ',
    ])
    return command


def accumulate_files(inputs, target):
    """
    This accumulates all input files to one target file.

    Simple expression like target = (A + B) with A is current input and B is the
    privoius result is used. It returns a list of commands.
    """

    pre_file = None
    for i, raster in enumerate(inputs):
        print("Calculate {} from {} files.".format(i, len(inputs)))
        if not pre_file:
            # first run has no privoius file, just copy
            print("Just copy the first file.")
            pre_file = create_temp_copy(str(raster))  # first run only copy input
        else:
            exp = "(A + B)"  # use pre_file file as B
            command = build_command(str(raster), str(target), exp, previous=pre_file)
            call_command(command)
            os.remove(str(pre_file))  # remove pre_file afer processing
            pre_file = create_temp_copy(str(target))


def use_scale_offset(input, target, scale, offset):
    """Scale and offset data"""
    # one file: scal offset only
    exp = get_expression(offset=offset, scale=scale)
    return build_command(str(input), str(target), exp)


def use_custom_expression(input, target, exp):
    """Caluclate data with custom expression"""
    exp = get_expression(exp)
    return build_command(str(input), str(target), exp)


def call_command(command):
    output = subprocess.check_call(
        command,
        stderr=subprocess.STDOUT,
        shell=True,
        universal_newlines=True
    )
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="calc_expression",
        description="""
        This tool use expression to caluclate target from .

        """,
        epilog="""Examples:
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'source',
        nargs='+',
        help='Input file path oder list of pathes')

    parser.add_argument(
        'target',
        help='Target file path')

    parser.add_argument(
        '-s',
        '--scale',
        default=1,
        type=float,
        help='Factor to scale the data')

    parser.add_argument(
        '-x',
        '--offset',
        default=0,
        type=float,
        help='Value to add after scaling')

    parser.add_argument(
        '-e',
        '--exp',
        default=None,
        type=float,
        help='Expression')  # TODO: explian input arguments

    parser.add_argument(
        '-a',
        '--accumulate',
        action='store_true',
        help='Accumulate by y=(A + B) with A = current file and B privoius result.')

    args = parser.parse_args()

    sources = [Path(s) for s in args.source]

    target = Path(args.target)
    if target.is_dir():
        target_folder = target

    offset = args.offset
    scale = args.scale
    exp = args.exp
    accumulate = args.accumulate

    commands = []
    if accumulate:
        accumulate_files(sources, target)
    else:
        for i, raster in enumerate(sources, 1):
            print("Process {} of {}".format(i, len(sources)))

            if target_folder:
                target = build_target_path(raster, target_folder)

            if not exp:
                out = call_command(use_scale_offset(raster, target, scale=scale, offset=offset))
            else:
                out = call_command(use_custom_expression(raster, target, exp=exp))
            print(out)
