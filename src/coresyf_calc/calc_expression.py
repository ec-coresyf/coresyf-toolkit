#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import rasterio
import shutil
import subprocess
import tempfile

from pathlib2 import Path

""" TODO:
- one input to one target file with offset appleyed
- one accumulated file from multible files
- wait until all files are calculdated
- use target format from input format
- set creation option like comrpession
"""

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

    command = (
        'gdal_calc.py '
        '{}'
        '--outfile="{}" '
        '--calc="{expression}" '
        '--NoDataValue="{no_data}" '
        '--type="Float32" '
        '--format="HFA" '
        '--overwrite '
    ).format(
        sourceraster,
        target,
        expression=exp,
        no_data=no_data_value
    )
    return command


def accumulat_files(inputs, target):
    """
    This accumulates all input files to one target file.

    Simple expression like target = (A + B) with A is current input and B is the
    privoius result is used. It returns a list of commands.
    """

    # accumulated multible files to one file

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
    # one file: scal offset only
    exp = get_expression(offset=offset, scale=scale)
    return build_command(str(one_file), str(out_file), exp)


def use_custom_expression(input, target, exp):
    """Use custom expression with input and target file."""
    exp = get_expression(exp)
    return build_command(str(input), str(target), exp)


def call_commands(commands):
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
        help='Value to add afer scaling')

    parser.add_argument(
        '-e',
        '--exp',
        default=None,
        type=float,
        help='Expression') #TODO: explian input arguments

    args = parser.parse_args()

    # source = Path(args.source)
    source = [Path(s) for s in args.source]
    offset = args.offset
    scale = args.scale
    target = args.target

    commands = []
    if source > 1:
        sources = source
        commands = accumulat_files(sources, target)
    else:
        if not exp:
            commands = use_scale_offset(source, target, scale=scale, offset=offset)
        else:
            commands = use_custom_expression(source, target, exp=exp)

    print commands
    # call_commands(commands)
    # call commands with subprocess
    # call_commands(command)
