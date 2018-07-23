#!/usr/bin/env python
"""Produce a data cube masked by flags with a certain value.

Each element in the maske variable will by checked aginst values in flag list.
It produces a new tow dimensional mask array for each slice. Thise arrays will
by aggregated to a global mask and will by applied to all variables.

This produces a clean data cube with Missing vlaues filled by fix values.

"""

import logging
import numpy as np
import collections


def Slices(cube, var_name, dim="date"):
    """
    Generator object to iterate for `var_name` over slices in cube in `dim` direction.

    Retunrs a dictionary with slice for `var_name` and dimmension index.

    Attention!
    The `dim` deimension to iterate over must by on the first position in
    `variabe.shape` tuple.

    Parameters
    ----------
    cube : netCDF4 Dataset handle
        Open cube file handle.
    var_name: string
        Variable to return data for.
    dim : type
        Dimension to interate.

    Returns
    -------
    nasted dictionary
        Keys are `dim`, variables. Variables is a nasted dictionary
        holding with key `var_name` and data. Data are masked numpy array.

    """

    try:
        cube.dimensions[dim]
    except KeyError as e:
        msg = "Dimension {} is no a cube dimension."
        raise KeyError(msg.format(dim))
    else:
        stop = len(cube.dimensions[dim])

    for dim_ids in range(0, stop):

        if cube[var_name].ndim == 3:
            data = cube[var_name][dim_ids, :, :]
        else:
            data = cube[var_name][:] # e.g date variabe

        slice_ = dict([(var_name, data)])
        yield dict(dim_ids=dim_ids, variables=slice_)


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
        mask = np.isin(int_mask, flags)  # get boolean array of element are in flags
    else:
        try:
            one_var = next(iter(slice_["variables"]))
            mask = slice_["variables"][one_var].mask  # use mask from one variable
        except AttributeError as e:
            raise AttributeError("No mask found.")
    return mask


def aggregated_mask(cube, flags, dim="date", mask_var="mask"):
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

    # init mask array with first slice
    slices = Slices(cube, mask_var, dim)
    one_slice = slices.next()
    new_mask = mask_by_flags(one_slice, flags, name=mask_var)

    for nr, s in enumerate(Slices(cube, mask_var, dim)):
        logging.debug("Aggregate slice number: {}".format(nr))

        mask = mask_by_flags(s, flags, name=mask_var)
        new_mask = new_mask | mask

    Mask = collections.namedtuple('Mask', ['name', 'values'])
    return Mask(mask_var, values=new_mask)


def masking_cube(in_cube, out_cube, mask, dim='date'):
    """Change variable mask in `cube` to aggregated version given by `mask`.

    Set variabe used for time Slices by `dim` parameter. This musst by a
    dimmension and variable in the `cube`. The default is 'date'.

    Parameters
    ----------
    cube : netCDF4 Dataset handle
        File handle to read from.
    mask : Mask tuple with Mask.name and Mask.values
        Mask to apply on each cube variabe.
    dim : string
        Dimension direction to interate.

    Returns
    -------
    side effect
        Wirte new mask to each slice in cube.

    """
    for v_name, varin in in_cube.variables.iteritems():

        for s in Slices(in_cube, v_name, dim):

            # create dimension if necessary
            for dname, the_dim in in_cube.dimensions.iteritems():
                if dname not in out_cube.dimensions:
                    out_cube.createDimension(
                        dname,
                        len(the_dim) if not the_dim.isunlimited() else None
                    )

            if v_name not in out_cube.variables:

                if v_name == mask.name:
                    dtype = varin.datatype
                    dims = ('lat', 'lon')

                else:
                    dtype = varin.datatype
                    dims = varin.dimensions

                outVar = out_cube.createVariable(
                    v_name,
                    dtype,
                    dims,
                    fill_value=-999,
                    zlib=True
                    )

                outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})

            # masking only variables with data records
            dim_ids = s["dim_ids"]
            data = s["variables"][v_name]

            if v_name == mask.name:
                outVar[:, :] = data
            elif data.ndim == 1:
                outVar[:] = data
            else:
                data[mask.values] = -999
                outVar[dim_ids, :, :] = data
