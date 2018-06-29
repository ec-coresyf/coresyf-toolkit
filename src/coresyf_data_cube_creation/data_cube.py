# coding: utf-8
# ! /usr/bin/env python2
"""This module collects function to create, modify and save 3D data cube of grid data.

The data cube is a 3D data structure grid with following axes:

    1. time
    2. columns
    3. rows

The 3D data structure is a NetCDF file. Each slice of this axes is array of data for one day.
The grid structure is defined by columns and rows with additional dimensions.

TODO: Extent documentation
"""

__author__ = "Julius Schroeder"
__version__ = "0.0.1"
__copyright__ = "Copyright 2018, MaREI Centre for Marine and Renewable Energy"

# import python modules
import glob
import sys
import numpy as np

from os import path
from collections import namedtuple

# import third party modules
from netCDF4 import Dataset

def search_files(folder, pattern="*.nc"):
    """This searching for files in folder matching pattern parameter
    returns list of path.

    Parameters
    ----------

    folder: str
        Path of folder to search in.

    pattern: regex string
        Pattern for file of interests as regex string.

    Returns
    -------
    files: list
        List of file in the folder matching the pattern.

    Example
    -------
    > search_for_files("data/")
    """

    search_path = path.join(folder, pattern)

    files = glob.glob(search_path)
    # TODO: add results logging

    if not files:
        raise IOError("List of files is empty. No files match {} in {}!".format(pattern, search_path))

    return files


def extract_data(file_path, bounding_box, *variables):
    """Extract spatial data from a tow dimmensional dataset file for a AOI specified by bounding box.

    This gets a netCDF file with spatial data as input file. The AIO is given as bounding box.
    As default all available variables will be extract from dataset, but optional the function get also a list of data variables to extract.

    Parameters
    ----------

    file_path: str
        Path to netCDF file.

    variables: list
        List of variables to extract from dataset. Default all variables will by extract.

    bounding_box: tuple
        bounding_box is a ``(minx, miny, maxx, maxy)`` tuble of geographic coordinates.

    Returns
    -------
    tuple like ``(mask, analysed_sst, analysis_error)``
        Tuple of GHRSST SST data extract by bounding_box.

    Example
    -------
    > # Extract SST data from GHRSST netCDF4 file.
    > extract_var = ["mask", "analysed_sst", "analysis_error"]
    > extract_ghrsst_data("data/ghrsst.nc", (-60,30,0,80), extract_var)

    """

    def upper_lower_index(lat, lon, bounding_box):
        """Find the index for the upper and lower bound in latitude and longitude."""
        # latitude lower and upper index
        latli = np.argmin( np.abs( lats - bounding_box[1] ) )
        latui = np.argmin( np.abs( lats - bounding_box[3] ) )

        # longitude lower and upper index
        lonli = np.argmin( np.abs( lons - bounding_box[0] ) )
        lonui = np.argmin( np.abs( lons - bounding_box[2] ) )

        return (latli, latui, lonli, lonui)

    def subset(var_data, *indexes):

        msg = 'Number of dimension of {} should by 2 but is {}'

        if indexes and len(indexes) != 4:
            raise IndexError("Subset need four indexes like latli, latui, lonli, lonui.")

        if indexes:
            try:
                subset = var_data[latli:latui , lonli:lonui ]
            except ValueError as e:
                raise e(msg.format(var, var_data.ndim))
        else:
            try:
                subset = var_data[ :, :]
            except ValueError as e:
                raise e(msg.format(var, var_data.ndim))

    return subset

    data = {
        'dimensions': {
            'lat': None,
            'lon': None,
        },
    }

    try:
        dataset = Dataset(file_path, "r", format="NETCDF4")
    except IOError as e:
        raise e("Can not open {}.".format(file_path))

    lat = dataset.variables["lat"][:]
    lon = dataset.variables["lon"][:]

    # filter by variable
    if not variables:
        keys = dataset.variables.keys()
        variables = [var for var in keys if dataset.variables[var].ndim == 2] # only 2D variables


    for var in variables:
        try:
            var_data = dataset.variables[var]
        except KeyError as e:
            raise e('{} is not in dataset.'.format(var))


        # clip by bounding box
        try:
            if bounding_box:

                latli, latui, lonli, lonui = upper_lower_index(lat, lon, bounding_box)

                lat = lat[latli:latui]
                lon = lon[lonli:lonui]

                set = subset(var_data, latli, latui, lonli, lonui)
            else:
                set = subset(var_data)

        except ValueError as e:
            print e # TODO: write error message to log
        except IndexError as e:
            raise e
        else:
            data[var] = set

    data['dimensions']['lat'] = lat
    data['dimensions']['lon'] = lon

    dataset.close()

    return data


# TODO: write documentation
def create_netcdf(data, ds_path, dimensions_names=("time", "lat", "lon")):

    with Dataset(ds_path, 'w', format="NETCDF4") as dataset:

        # create dimensions
        for dim in data['dimensions']:
            if data['dimensions'][dim] is None:
                dataset.createDimension(dim, None)  # add as unlimited dimension
            else:
                dataset.createDimension(dim, len(data['dimensions'][dim]))

        # create time dimmension
        dataset.createDimension("time", None)

        # create variables
        for var in data.keys():
            if var == 'dimensions':
                for dim in data['dimensions']:
                    dim_var = dataset.createVariable(dim, data['dimensions'][dim].dtype, (dim,))
                    dim_var[:] = data['dimensions'][dim]
            else:
                dataset.createVariable(var, data[var].dtype, dimensions_names, zlib=True)


def write_netcdf(data, ds_path):

    with Dataset(ds_path, 'a', format="NETCDF4") as dataset:
        # write data variables
        time_slice = len(dataset.dimensions["time"])

        for var in data.keys():
            if var != 'dimensions':
                var_data = dataset.variables[var]
                var_data[time_slice, :, :] = data[var]
