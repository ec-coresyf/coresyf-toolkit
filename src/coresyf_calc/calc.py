#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib2 import Path
import rasterio

"""This module provide simple raster calucation functionality"""


def get_inputs(input_folder, pattern="*.img"):
    """Return sorted list of input files matching pattern in folder"""
    return sorted(source.glob(pattern))


def get_expression(offset=0, exp=None, scale=None):
    """Get the right expression by differend parameter combinations"""

    if (exp and not offset and not scale):
        return exp
    elif (exp and offset and not scale):
        return "(({0}) + {1})".format(exp, offset)
    elif (exp and offset and scale):
        return "(({0}) + {1})*{2}".format(exp, offset, scale)
    elif (exp and not offset and scale):
        return "(({0}))*{1}".format(exp, scale)
    elif (not exp and offset and scale):
        return "(A + {0})*{1}".format(offset, scale)
    elif (not exp and not offset and scale):
        return "(A * {0})".format(offset, scale)
    elif (not exp and offset and mot scale):
        return "(A + {0})".format(scale)


def build_command(input, target, exp, no_data_value=None):
    """build command for gdal_calc
    Set no data value explicitly from input file if not given as parameter.
    """
    if not no_data_value:
        with rasterio.open(str(input)) as ds:
            no_data_value = ds.nodata  # set explicit no_data value

    command = (
        'gdal_calc'
        '-A {}'
        '--outfile={}'
        '--calc={expression}'
        '--NoDataValue {no_data}'
    ).format(
        input,
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

"""
- one input to one target file with offset appleyed
- one accumulated file from multible files
- wait until all files are calculdated
- use target format from input format
- set creation option like comrpession
"""


if __name__ == '__main__':
    one_file = Path("test_data/20110102-IFR-L4_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v2.0-fv1.0_analysed_sst.img")
    out_file = Path("test_data/20110102-IFR-L4_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v2.0-fv1.0_analysed_sst_scaled.img")
