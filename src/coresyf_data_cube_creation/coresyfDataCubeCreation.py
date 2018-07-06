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
import dateutil.parser
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
    inputs_iter = glob.iglob(search_path)
    inputs = sorted(inputs_iter) # sort by file name

    if inputs:
        logging.info("Fount {} inputs in {}.".format(len(inputs), folder))
        return inputs
    else:
        msg = "No files found in {}! Search pattern are {}."
        raise IOError(msg.format(folder, search_path))

def sorted_inputs(paths, key="date_created"):
    """Return one by date sorted list of paths as tuples like (path, date).
    Key parameter is used to find attribut in netCDF to sort by.

    Returns
    -------

    list of tuple
        Sorted list of tuples holding input files path as string and date as integar e.g. (path, date).
        List ist sorted afer date. Date is integar in dayes based on January 1 of year 1 (see date.toordinal() for more info).

    """
    inputs = []

    # get date
    for i, path in enumerate(paths):
        try:
            dataset = Dataset(path, "r", format="NETCDF4")
        except IOError as e:
            raise e
        else:
            with dataset:
                try:
                  date_attr = dataset.getncattr(key)
                except AttributeError as e:
                  logging.warning("No date_created attribut found in input dataset, file name order to sort.")
                  logging.debug(e)
                  date = i
                else:
                  date = dateutil.parser.parse(date_attr).toordinal()

        item = (path, date)
        inputs.append(item)

    # sort list after date attribut
    return sorted(inputs, key=lambda item: item[1], reverse=True)

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
        'date': None,
        'dimensions': {
            'lat': None,
            'lon': None,
        },
        'variables': {
        }
    }

    try:
        dataset = Dataset(file_path, "r", format="NETCDF4")
    except IOError as e:
        raise e

    lat = dataset.variables["lat"][:]
    lon = dataset.variables["lon"][:]

    data['dimensions']['lat'] = lat
    data['dimensions']['lon'] = lon

    # read date and write in dict
    try:
      date_attr = dataset.date_created
    except AttributeError as e:
      logging.warning("No date_created attribut found in input dataset.")
      logging.debug(e)
    else:
      date = dateutil.parser.parse(date_attr)
      data['date'] = date.toordinal()

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
            data['variables'][var] = set

    dataset.close()

    return data

def create_stack(slice, ds_path):
    """This open a NetCDF4 file and creates basic stack structure.

    Parameters
    ----------

    slice: dict
        Dictionary holding dimmensions information.

    ds_path: string
        Destination Path for stack file.

    Returns
    -------
    stack: file object
        Stack as open file handle.

    """

    dimensions = slice['dimensions']
    variables = slice['variables']

    stacking_dimmension = "date"
    stack_dimmensions = (stacking_dimmension,'lat', 'lon',)

    try:
        stack = Dataset(ds_path, 'w', format="NETCDF4")
    except IOError:
        raise
    else:

        stack.createDimension(stacking_dimmension, None)
        stack.createVariable(stacking_dimmension, "i4", (stacking_dimmension,))

        # create and fill additional dimmensions (e.g. lat, lon)
        for dim, dim_data in dimensions.items():
            if len(dim_data):
                stack.createDimension(dim, len(dim_data))
            else:
                stack.createDimension(dim, None) # add as unlimited dimension

            dim_var = stack.createVariable(dim, dim_data.dtype, (dim,))
            dim_var[:] = dim_data

        for var, var_data in variables.items():
            stack.createVariable(var, var_data.dtype, stack_dimmensions, zlib=True)
    return stack

def write_slice(slice, stack, index):
    """
    This write slice to a netCDF file to create a stack.

    Slice is an numpy array holding the data. The destination file is a path in string
    by the ds_path. Use index parameter to specify the position in the stack.


    Parameters
    ----------

    slice: dict
        Dictionary of numpy arrays and variable names as Keys.

    stack: file object
        File handel to stack file.

    index: int
        Position of slice in data stack.

    Side effect
    -------
    Write slice to file stacked by index.

    Example
    -------

    """
    variables = slice['variables']

    for var, data in variables.items():
        var_data = stack.variables[var]
        var_data[index, :, :] = data

def stacking(inputs, variables, output):
    """This loob over inputs, extract data, write slices to file.

    Parameters
    ----------

    inputs: list of tuple
        List of tuples holding input files and date e.g. (path, date).

    variables: list
        Variables to stack. Must be same as variables in the input files.

    output: string
        Path to the 3D file.

    Side effect
    -------
    Create 3D stack file from inputs file.

    Example
    -------
    """

    print inputs

    for count, input__ in enumerate(inputs):

        input_path = input__[0] # unpack input tuple

        logging.info('Extracting data from {}'.format(input_path))
        slice = extract_slice(input_path, variables=variables)

        # run masking
        # TODO: fix masking to zero and one
        # data = masked_by_flags(data, mask_var="mask", flags=[2,5,9,13])

        if os.path.exists(output) is False:
            logging.info('Create {} file.'.format(output))

            try:
                stack = create_stack(slice, output)
            except EnvironmentError as e:
                logging.error("Can't create {}".format(output))
                logging.debug((os.strerror(e.errno)))
                raise e

        try:
            write_slice(slice, stack, index=count)
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
            inputs = sorted_inputs(inputs)
        except IOError as e:
            logging.error("No inputs found.".format(output))
            logging.debug((os.strerror(e.errno)))
            sys.exit()

        try:
            stacking(inputs, variables, output)
        except Exception as e:
            raise e
            sys.exit()
