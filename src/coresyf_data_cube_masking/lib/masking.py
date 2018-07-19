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
        cube.dimensions[dim]
    except KeyError as e:
        msg = "Dimension {} is no a cube dimension."
        raise KeyError(msg.format(dim))
    else:
        stop = len(cube.dimensions[dim])

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

    slice_ = {
        "dim_ids": dim_ids,
        "variables": {},
    }
    for name, var in cube.variables.items():
        if var.ndim == 3:
            # TODO: handle IndexError
            data = var[dim_ids, :, :]
            slice_["variables"][name] = data

    return slice_


def mask_by_flags(slice_, flags=[], name="mask"):
    """Returns new `numpy.array` masked by flags.

    This select mask variable in `slice_` by `name` and extend mask by flags.
    If variable called `name` not founed try find mask from random variable
    and raise AttributeError if failed.

    Parameters
    ----------
    slice_ : dictionary
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

    if name in slice_["variables"].keys():
        int_mask = slice_["variables"][name]
        mask = np.isin(int_mask, flags)
    else:
        try:
            one_var = next(iter(slice_["variables"]))
            mask = slice_["variables"][one_var].mask  # use mask from one variable
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
    random_slice = slices.next()
    aggregate_mask = mask_by_flags(random_slice, flags, name=mask_var)

    for nr, s in enumerate(Slices(cube, dim)):
        logging.debug("Aggregate slice number: {}".format(nr))

        mask = mask_by_flags(s, flags, name=mask_var)
        aggregate_mask = aggregate_mask | mask

    return aggregate_mask


def masking_cube(cube, mask, dim='date'):
    """Change variable mask in `cube` to aggregated version given by `mask`.

    Set variabe used for time Slices by `dim` parameter. This musst by a
    dimmension and variable in the `cube`. The default is 'date'.

    Parameters
    ----------
    cube : netCDF4 Dataset handle
        File handle to read from.
    mask : numpy array
        Mask to applie on cube.
    dim : string
        Dimension direction to interate.

    Returns
    -------
    side effect
        Wirte new mask to each slice in cube.

    """
    for s in Slices(cube, dim):
        dim_ids = s["dim_ids"]
        for name, data in s["variables"].items():
            data[mask] = -999
            cube.variables[name][dim_ids, :, :] = data
