#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This python script Python script to provide simple raster calculation functionality.
The inputs required can be:
    1) 1 raster image file, or
    2) A list of raster image files, or
    3) A folder containing at least 1 (or more) raster image files.

This script uses GDAL expressions/formula (e.g y= A + 230, where A is a raster array) which can be applied to every element, i.e. pixel, in your raster image.

Note:
1) This workflow assumes that the filename contains a date, in the form YYYYMMDD (e.g. 20180802).

In terms of outputs,
A single output file will be generated for each file input.
    1) The filename of the output file in the target folder will be the same as the input filename. You need to create a target folder and allocate it as the target location (otherwise the script will not work). This is particularly relevant when the script is processing a list of files contained in a folder (option 3 above).
    2) Helptext will be produced by using the scriptname and "-h" (i.e. python calc_expression.py -h) which contains lots of information on usage, and how to use it most effectively.

Arguments:
positional arguments (i.e. the order you write them in is CRITICAL):
  source                Input file path, or list of paths, or input folder path
  target                Target file path, or target folder to be populated with generated files

optional arguments:
  -h,   --help
                    Show a detailed help message in the command line interface, and exit
  -p,   --pattern
                    Designate a filename pattern to search for, in the case where an input folder path contains a range of files (such as mask files and measurement files). For example, if a folder contains a number of files with the string "analysed_SST" in their filename, the script will only process those files with "analysed_SST" in their filename.
  -s,   --scale
                    Factor to scale the data, i.e. a float number by which all pixels are multiplied. For example for storage reasons temperature in Kelvin is often stored as an integer (e.g.27415 as opposed to 274.15), so we multiply the data by a scaling factor of 0.01 to get it to the correct value.
  -x,   --offset
                    Define a value to add after scaling. For example, if we wanted to convert Kelvin to degrees Celsius, we could subtract 273.15 from the scaled Kelvin value to get the Celsius value
  -e,   --exp
                    Define a simple expression (formula) to apply to your data. This formula is  applied to the input pixel values to get the target values. For example, Pixel value = a, we want the value b to be produced. The Expression we use is "b = 2a + 123"
  -a, --accumulate
                    This lovely little piece of script allows you to cumulatively sum all the raster images in a source folder, and produce a single file in the target folder. For example if you have a set of five 1/0 mask files, with different mask extents in a source folder, the script will sum all of them together. This produces a single mask file in the target folder with values of 1,2,3,4 and 5.

This script was written using Python 2.7.

It was created by Julius Schroeder, during his internship at the MaREI Centre for Marine and Renewable Energy, ERI, UCC, in July 2018. This was done as part of work under the H2020-CoReSyF initiatives Research Applications package.
"""

#Step 1) Import required python modules


import argparse     # Gives usage instructions and tool details via the command line interface
import os           # Enables a suite of miscellaneous operating system interfaces (extra to the sys module) which expands the range of system functionalities you can use)
import rasterio     # Enables a set of raster processing functionalities (which are based on GDAL functions)
import shutil       # Enables a suite of file management capabilities
import subprocess   # Enables the python script here to call an external programme to do some work
import sys          # Enables a suite of system-specific functions and parameters (to help run things)
import tempfile     # Creates temporary files and dictionaries (e.g. hold information from a previous image)
from pathlib2 import Path   # Enables a set of object-based path functionalities, i.e. setting file paths and being able to manipulate them.


#Step 2) Define a set of functions to be called upon


def get_inputs(folder, pattern="*.img"):
    """Return sorted list of input files matching pattern in folder"""
    return sorted(folder.glob(pattern))


def create_temp_copy(path):
    temp_dir = tempfile.gettempdir()
    temp_path = Path(temp_dir) / 'previous_file.img'
    shutil.copy2(str(path), str(temp_path))
    return temp_path


def build_target_path(input, target_folder):
    """Build target-like target_folder/input"""
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
        This script uses GDAL expressions/formula (e.g y= A + 230, where A is a raster array) which can be applied to every element, i.e. pixel, in your raster image.

        This workflow assumes that the filename contains a date, in the form YYYYMMDD (e.g. 20180802).

        The filename of the output file in the target folder will be the same as the input filename. You need to create a target folder and allocate it as the target location (otherwise the script will not work). This is particularly relevant when the script is processing a list of files contained in a folder (option 3 above).
        """,
        epilog="""Examples:
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'source',
        nargs='+',
        help='Input file path, or list of paths, or input folder path'
    )

    parser.add_argument(
        'target',
        help='Target file path, or target folder to be populated with generated files'
    )

    parser.add_argument(
        '-p',
        '--pattern',
        default="*.img",
        type=str,
        help='A filename pattern to search for, in the case where an input folder path contains a range of files (such as mask files and measurement files). For example, if a folder contains a number of files with the string "analysed_SST" in their filename, the script will only process those files with "analysed_SST" in their filename.'
    )

    parser.add_argument(
        '-s',
        '--scale',
        default=1,
        type=float,
        help='Factor to scale the data, i.e. a float number by which all pixels are multiplied. For example for storage reasons temperature in Kelvin is often stored as an integer (e.g.27415 as opposed to 274.15), so we multiply the data by a scaling factor of 0.01 to get it to the correct value.'
    )

    parser.add_argument(
        '-x',
        '--offset',
        default=0,
        type=float,
        help='Value to add after scaling. For example, if we wanted to convert Kelvin to degrees Celsius, we could subtract 273.15 from the scaled Kelvin value to get the Celsius value'
    )

    parser.add_argument(
        '-e',
        '--exp',
        default=None,
        type=float,
        help='Expression. Formula which is applied to the input pixel values to get the target values. For example, Pixel value = a, we want the value b to be produced. The Expression we use is "b = 2a + 123"')  # TODO: explian input arguments

    parser.add_argument(
        '-a',
        '--accumulate',
        action='store_true',
        help='Accumulate by y=(A + B) when A = current file and B is the previous file, or result of a previous addition. This awesome tool allows you to cumulatively sum all the raster images in a source folder, and produce a single file in the target folder. For example if you have a set of five 1/0 mask files, with different mask extents in a source folder, the script will sum all of them together. This produces a single mask file in the target folder with values of 1,2,3,4 and 5.'
        )

    args = parser.parse_args()

    pattern = args.pattern

    if len(args.source) == 1:
        source = Path(args.source[0])
        if source.is_dir():
            sources = list(source.glob(pattern))
        else:
            sources = [source]
    else:
        sources = [Path(s) for s in args.source]

    target = Path(args.target)
    if target.is_dir():
        target_folder = target
    else:
        target_folder = None

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
