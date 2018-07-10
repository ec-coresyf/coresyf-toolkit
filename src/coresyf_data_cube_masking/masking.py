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

    slice = {
        "dim_ids": dim_ids,
        "variables": {},
    }
    for name, var in cube.variables.items():
        if var.ndim == 3:
            data = var[dim_ids, :, :]
            slice["variables"][name] = data

    return slice


def mask_by_flags(slice, flags=[], name="mask"):
    """Returns new `numpy.array` masked by flags.

    This select mask variable in `slice` by `name` and extend mask by flags.
    If variable called `name` not founed try find mask from random variable
    and raise AttributeError if failed.

    Parameters
    ----------
    slice : dictionary
        Keys are variables names and values are np.ma.array.
    flags : list
        List of integar to masked out by.
    name : string
        Name of the mask variable.

    Returns
    -------
    type
        Description of returned object.

    """
    mask = []

    if name in slice["variables"].keys():
        int_mask = slice["variables"][name]
        mask = np.isin(int_mask, flags)
    else:
        try:
            one_var = next(iter(slice["variables"]))
            mask = slice[variables][one_var].mask  # use mask from one variable
        except AttributeError as e:
            raise e("No mask found.")
    return mask


def aggregate_mask(cube, flags, dim="date", mask_var="mask"):
    """Returns one aggregated mask for all slices.

    Parameters
    ----------
    cube : netCDF4 Dataset handle
        File handle to read from.
    flags : list
        List of integar to masked out by.
    dim : string
        Dimension direction to aggregated.
    mask_var : string
        Name of the mask variable in `cube`.

    Returns
    -------
    numpy.array
        Aggregated mask for cube.
    """

    # first slice
    slices = Slices(cube, dim)
    aggregate_mask = mask_by_flags(slices.next(), flags, name=mask_var)

    for nr, s in enumerate(Slices(cube, dim)):
        logging.debug("Aggregate slice number: {}".format(nr))

        mask = mask_by_flags(s, flags, name=mask_var)
        aggregate_mask = aggregate_mask | mask

    return aggregate_mask


def masking_cube(cube, mask, dim='date'):
    for s in Slices(cube, dim):
        for _, var in s.items():
            var.mask = mask
            print var.mask
    pass
