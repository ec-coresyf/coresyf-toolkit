#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import rasterio
import shutil
import subprocess
import tempfile

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


def accumulat_files(inputs, target):
    """
    This accumulates all input files to one target file.

    Simple expression like target = (A + B) with A is current input and B is the
    privoius result is used. It returns a list of commands.
    """


    commands = []
    pre_file = None
    for raster in inputs:
        if not pre_file:
            # first run has no privoius file, just copy
            pre_file = create_temp_copy(str(raster))  # first run only copy input
        else:
            exp = "(A + B)"  # use pre_file file as B
            command = build_command(str(raster), str(target), exp, previous=pre_file)
            commands.append(command)
    return commands


def use_scale_offset(input, target, scale, offset):
    """Scale and offset data"""
    # one file: scal offset only
    exp = get_expression(offset=offset, scale=scale)
    return build_command(str(input), str(target), exp)


def use_custom_expression(input, target, exp):
    """Caluclate data with custom expression"""
    exp = get_expression(exp)
    return build_command(str(input), str(target), exp)


def call_commands(commands):
    """Call command is list with subprocess"""
    for i, command in enumerate(commands, 1):
        print("\n Call command number {0} from {1}".format(i, len(commands)))
        print(command)
        output = subprocess.check_call(
            command,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True
        )


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

    args = parser.parse_args()

    sources = [Path(s) for s in args.source]
    offset = args.offset
    scale = args.scale
    target = args.target
    exp = args.exp

    commands = []
    if len(sources) > 1:
        commands = accumulat_files(sources, target)
    else:
        source = sources[0]
        if not exp:
            commands.append(use_scale_offset(source, target, scale=scale, offset=offset))
        else:
            commands.append(use_custom_expression(source, target, exp=exp))

    call_commands(commands)
