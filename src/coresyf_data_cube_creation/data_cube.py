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


def bounding_box_2_indexes(lat, lon, bounding_box):
    """This convert from bounding box coordinates to row and column indexes.

    Parameters
    ----------

    lat: netCDF4 variable
        Latitude variable of a NETCDF4 dataset

    lon: netCDF4 variable
        Longitude variable of a NETCDF4 dataset

    bounding_box: tuple
        bounding_box is a ``(minx, miny, maxx, maxy)`` tuble of geographic coordinates in eastern dregree.

    Returns
    -------
    LatLonIndexes with keys 'col_idx_l', 'row_idx_l', 'col_idx_u' and 'row_idx_u'.
        Named tuple with columns and row index for upper and lower corner.

    Example
    -------
    > bounding_box_2_indexes(lat, lon, (-60,30,0,80))
    """
    # print lat, lon, bounding_box

    # latitude lower and upper index
    row_idx_l = np.argmin(np.abs(lat - float(bounding_box[1])))
    row_idx_u = np.argmin(np.abs(lat - float(bounding_box[3])))

    # longitude lower and upper index
    col_idx_l = np.argmin(np.abs(lon - float(bounding_box[0])))
    col_idx_u = np.argmin(np.abs(lon - float(bounding_box[2])))

    Indexes = namedtuple("LatLonIndexes", ['col_idx_l', 'row_idx_l', 'col_idx_u', 'row_idx_u'])

    return Indexes(col_idx_l, row_idx_l, col_idx_u, row_idx_u)


def extract_data(sc_path, bounding_box, extract_var=None):
    """Extract spatial data from dataset file for a AOI specified by bounding box.

    This gets a netCDF file with spatial data as input file. The AIO is given as bounding box.
    As default all available variables will be extract from dataset, but optional the function get also a list
    of data variables to extract.

    Parameters
    ----------

    sc_path: str
        Path to netCDF file.

    extract_var: list
        List of variables to extract from dataset.

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

    try:
        with Dataset(sc_path, "r", format="NETCDF4") as dataset:

            lat = dataset.variables["lat"][:]
            lon = dataset.variables["lon"][:]

            indexes = bounding_box_2_indexes(lat, lon, bounding_box)

            row_idx_l = indexes.row_idx_l
            row_idx_u = indexes.row_idx_u

            col_idx_l = indexes.col_idx_l
            col_idx_u = indexes.col_idx_u


            # TODO: change to calculate lat, lon dimensions from bounding box and pixel size
            data = {
                'dimensions': {
                    'lat': lat[row_idx_l:row_idx_u],
                    'lon': lon[col_idx_l:col_idx_u],
                },
            }

            if not extract_var:
                extract_var = dataset.variables.keys()

            for var in extract_var:
                var_data = dataset.variables[var]
                if var_data.ndim > 2:
                    data[var] = var_data[0,row_idx_l:row_idx_u, col_idx_l:col_idx_u]

    except IOError as e:
        raise e("Can not open {}.".format(sc_path))
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
