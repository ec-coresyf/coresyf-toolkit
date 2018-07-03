# coding: utf-8
# ! python2
"""This module collects function to creates 3D data cube of grid data.

The data cube is a 3D data structure grid with following axes:

    1. time
    2. columns
    3. rows

The 3D data structure is a NetCDF file. Each slice of this axes is array of data for one day.
The grid structure is defined by columns and rows with additional dimensions.
"""

__author__ = "Julius Schroeder"
__version__ = "0.0.1"
__copyright__ = "Copyright 2018, MaREI Centre for Marine and Renewable Energy"

# import python modules
import glob
import itertools
import logging
import numpy as np
import os
import sys

from collections import namedtuple

# import third party modules
from netCDF4 import Dataset

from coresyftools.tool import CoReSyFTool

def get_inputs(folder, pattern="*.nc"):
    """This searching for input files in folder matching pattern parameter
    returns list of path.

    Parameters
    ----------

    folder: str
        Path of folder to search in.

    pattern: regex string
        Pattern for file of interests as regex string.

    Returns
    -------
    inputs: iterator
        List of file in the folder matching the pattern.

    Example
    -------
    > search_for_files("data/")
    """

    search_path = os.path.join(folder, pattern)
    inputs = glob.iglob(search_path)
    # TODO: add results logging

    try:
        first = inputs.next()
    except StopIteration:
        msg = "No files found in {}! Search pattern are {}."
        raise IOError(msg.format(folder, search_path))
    else:
        inputs = itertools.chain([first], inputs)
        return inputs




def extract_slice(file_path, variables=None):
    """Extract data from dataset by given variables.

    This gets a netCDF file with spatial data as input file. As default all available variables will be extract from dataset, but optional the function get also a list of data variables to extract.

    Parameters
    ----------

    file_path: str
        Path to netCDF file.

    variables: list
        List of variables to extract from dataset. Default all variables will by extract.

    Returns
    -------
    data: dict
        Dictionary of extracted data. Variables names used as keys. Data are numpy.ma.MaskedArray instances. Additional dimensions key is used to save latitude and longitude dimensions.

    Example
    -------
    > # Extract SST data from GHRSST netCDF4 file.
    > extract_var = ["mask", "analysed_sst", "analysis_error"]
    > extract_data("data/ghrsst.nc", extract_var)

    """


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

    data['dimensions']['lat'] = lat
    data['dimensions']['lon'] = lon

    # filter by variable
    if not variables:
        keys = dataset.variables.keys()
        variables = [var for var in keys if dataset.variables[var].ndim == 2] # only 2D variables

    for var in variables:
        try:
            set = dataset.variables[var][:, :]
        except KeyError:
            msg = 'Variable {} is not in dataset.'
            logging.debug(KeyError(msg.format(var)))
        except ValueError:
            msg = 'Variable {} number of dimension < 2.'
            logging.debug(ValueError(msg.format(var)))
        except IndexError as e:
            raise e
        else:
            data[var] = set

    dataset.close()

    return data


# TODO: write documentation
def create_stack_file(data, ds_path, dimensions_names=("time", "lat", "lon")):

    # TODO: add IOError messages in log
    try:
        dataset = Dataset(ds_path, 'w', format="NETCDF4")
    except IOError:
        raise
    else:
        with dataset:

            # create dimensions
            for dim in data['dimensions']:
                if data['dimensions'][dim] is None:
                    dataset.createDimension(dim, None)  # add as unlimited dimension
                else:
                    dataset.createDimension(dim, len(data['dimensions'][dim]))

            # create infinite time dimmension
            dataset.createDimension("time", None)

            # create variables
            for var in data.keys():
                if var == 'dimensions':
                    for dim in data['dimensions']:
                        dim_var = dataset.createVariable(dim, data['dimensions'][dim].dtype, (dim,))
                        dim_var[:] = data['dimensions'][dim]
                else:
                    dataset.createVariable(var, data[var].dtype, dimensions_names, zlib=True)

def write_slice(slice, ds_path):

    try:
        dataset = Dataset(ds_path, 'a', format="NETCDF4")
    except IOError as e:
        raise
    else:
        with dataset:
            # create stack by adding layers
            slice_time = len(dataset.dimensions["time"])

            for var in slice.keys():
                if var != 'dimensions':
                    var_data = dataset.variables[var]
                    var_data[slice_time, :, :] = slice[var]

def stacking(inputs, variables, output):
    """This go over alle inputs, extract data and write results to file."""

    for input__ in inputs:
        logging.info('Extracting data from {}'.format(set))
        slice = extract_slice(input__, variables=variables)

        # run masking
        # TODO: fix masking to zero and one
        # data = masked_by_flags(data, mask_var="mask", flags=[2,5,9,13])

        if os.path.exists(output) is False:
            logging.info('Create {} file.'.format(output))

            try:
                create_stack_file(slice, output)
            except EnvironmentError as e:
                logging.error("Can't create {}".format(output))
                logging.debug((os.strerror(e.errno)))
                raise e

        try:
            write_slice(slice, output)
        except EnvironmentError as e:
            os.remove(output)

            logging.error("Can't write to {}".format(output))
            logging.debug((os.strerror(e.errno)))
            raise e


class CoReSyFDataCubeCreation(CoReSyFTool):

    def run(self, bindings):

        # parse Parameters
        input_folder = bindings['Ssource']
        variables = tuple(bindings['var'].split(','))
        output = bindings['Ttarget']

        try:
            inputs = get_inputs(input_folder, pattern="*.nc")
        except IOError as e:
            logging.error("No inputs found.".format(output))
            logging.debug((os.strerror(e.errno)))
            sys.exit()

        try:
            stacking(inputs, variables, output)
        except Exception as e:
            raise e
            sys.exit()
