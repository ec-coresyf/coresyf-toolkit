#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib2 import Path

"""This module provide simple raster calucation functionality"""

"""input
- read from one file or multible files/folder
- offest as inteagar
- optional cutom equation expression to apply
- scalfactor
"""

"""build command
- if offset is one number y = x + offset
- if custom equation, use this for calucation (same as gdal calc)
- use only one band per file
- create comand string for gdal_calc
- scal data of scal factor is given
"""

"""output
- one input to one output file with offset appleyed
- one accumulated file from multible files
- wait until all files are calculdated
"""


if __name__ == '__main__':
    one_file = Path("test_data/20110102-IFR-L4_GHRSST-SSTfnd-ODYSSEA-GLOB_010-v2.0-fv1.0_analysed_sst.img")
