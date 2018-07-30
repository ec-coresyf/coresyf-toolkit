#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib2 import Path
import rasterio

"""This module provide simple raster calucation functionality"""

"""input
- read from one file or multible files/folder
- offest as inteagar
- optional cutom equation expression to apply
- scalfactor

"""


    - if offset is one number use expression = y = x + offset
    - if custom equation, use this for calucation (same as gdal calc)
    - use only one band per file
    - scal data of scal factor is given
    """
def build_command(input, output, exp, no_data_value=None):
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
        output,
        expression=exp,
        no_data=no_data_value
    )
    return command


"""output
- one input to one output file with offset appleyed
- one accumulated file from multible files
- wait until all files are calculdated
"""


if __name__ == '__main__':
    one_file = Path("test_data/20110102-IFR-L4_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v2.0-fv1.0_analysed_sst.img")
