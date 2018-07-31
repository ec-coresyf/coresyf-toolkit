#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib2 import Path
import rasterio
import subprocess

"""This module provide simple raster calucation functionality"""


def get_inputs(folder, pattern="*.img"):
    """Return sorted list of input files matching pattern in folder"""
    return sorted(folder.glob(pattern))


def get_expression(offset=0, exp=None, scale=None):
    """Get the right expression by differend parameter combinations"""

    if (exp and not offset and not scale):
        return exp
    elif (not exp and not offset and scale):
        return "(A * {0})".format(scale, offset)
    elif (not exp and offset and not scale):
        return "(A + {0})".format(scale)


def build_command(input, target, exp, no_data_value=None):
    """build command for gdal_calc
    Set no data value explicitly from input file if not given as parameter.
    """
    if not no_data_value:
        with rasterio.open(str(input)) as ds:
            no_data_value = ds.nodata  # set explicit no_data value

    input_raster = '-A "{}" '.format(input)

    if exp and 'B' in exp :
        input_raster = '-A "{}" -B "{}" '.format(input, target)

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
        input_raster,
        target,
        expression=exp,
        no_data=no_data_value
    )
    return command


def build_target_path(input, target):
    """Build target"""
    if target.is_dir():
        target_path = Path(target / input)
    else:
        return target


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

"""
- one input to one target file with offset appleyed
- one accumulated file from multible files
- wait until all files are calculdated
- use target format from input format
- set creation option like comrpession
"""


if __name__ == '__main__':
    input_folder = Path("test_data/imgs")
    one_file = Path("test_data/20110102-IFR-L4_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v2.0-fv1.0_analysed_sst.img")
    out_file = Path("test_data/20110102-IFR-L4_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v2.0-fv1.0_analysed_sst_scaled.img")
    offset = 273.15
    scale = 0.01

    # parse input parameter and save in list
    # parse output as one file path

    input_ = input_folder
    target = out_file
    exp = None

    if input_.is_dir():
        inputs = get_inputs(folder=input_)
    else:
        inputs = [input_,]

    commands = []
    if len(inputs) > 1:
        # multible files to one file
        if not target.is_file():
            exp = "A"  # create copy in tempfolder
            command = build_command(str(one_file), str(out_file), exp)
        else:
            exp = "(A + B)"
            # use tempfolder file as B
            command = build_command(str(one_file), str(out_file), exp)
    elif not exp:
        # one file: scal offset only
        exp = get_expression(offset=offset, scale=scale)
        command = build_command(str(one_file), str(out_file), exp)
    else:
        # one file: custom expression
        exp = get_expression(exp)
        command = build_command(str(one_file), str(out_file), exp)

    commands.append(command)
    print commands[0]
    # call_commands(commands)
    # call commands with subprocess
    # call_commands(command)
