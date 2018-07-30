#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module provide simple raster calucation functionality"""

"""input
- read from one file or multible files/folder
- offest as inteagar
- optional cutom equation function to apply
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
