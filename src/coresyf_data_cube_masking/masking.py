#!/usr/bin/env python
"""
This aggregates the masks of all slices in a data cube to one tow dimension mask
and applie this to all slices.

"""

import netCDF4


def get_slice(cube):
    """Short summary.

    Parameters
    ----------
    cube : netCDF file handle
        File handle to read from.

    Returns
    -------
    dict
        Dictionary with key == variable names and values numpy arrays.

    """

    slice = {}

    return slice
