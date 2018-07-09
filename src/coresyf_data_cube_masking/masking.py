#!/usr/bin/env python
"""
This aggregates the masks of all slices in a data cube to one tow dimension mask
and applie this to all slices.

"""

import logging
import numpy as np


def Slices(cube, dim="date"):
    """Create interator for `dim` dimension by using `get_slice` function.

    Attention!
    The `dim` deimension to iterate over must by on the first position in
    `variabe.shape` tuple.

    Parameters
    ----------
    cube : netCDF4 Dataset handle
        Open cube file handle.
    dim : type
        Dimension to interate.

    Returns
    -------
    interator
        Interate over `dim` dimension.

    """

    try:
        stop = len(cube.dimensions[dim])
    except KeyError as e:
        msg = "Dimension {} is no a cube dimension."
        e(msg.format(dim))

    for dim_ids in range(0, stop):
        yield get_slice(cube, dim_ids)


def get_slice(cube, dim_ids):
    """Returns slice dictionary at index `dim_ids` from a three dimensional cube.

    Parameters
    ----------
    cube : netCDF file handle
        File handle to read from.

    dim_ids : int
        Slice to select from `dim`.

    Returns
    -------
    dict
        Dictionary with key == variable names and values numpy arrays.

    """

    slice = {}
    for name, var in cube.variables.items():
        if var.ndim == 3:
            data = var[dim_ids, :, :]
            slice[name] = data

    return slice


