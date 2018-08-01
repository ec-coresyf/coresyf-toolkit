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



from dateutil.parser import parse
from pathlib2 import Path
from collections import namedtuple

# import third party modules
from netCDF4 import Dataset

from coresyftools.tool import CoReSyFTool


def get_inputs(folder, data="", mask="", extension=".img"):
    """Find inputs files by names and extention.

    Parameters
    ----------

    folder: str
        Path of folder to search in

    data: str
        Data file name

    mask: str
        Data file name

    extension: str
        Image file type extension
        Default: ".img"

    Returns
    -------
    inputs: iterator
        List of tuple file pahtes like (data_oath, maks_path)

    Example
    -------
    > get_inputs("data/")
    """
    # get list of all files with extension
    inputs = Path(folder).glob("*{}".format(extension))

    search_path = os.path.join(folder, extension)
    inputs_iter = glob.iglob(search_path)
    inputs = sorted(inputs_iter)  # sort by file name

    if inputs:
        logging.info("Fount {} inputs in {}.".format(len(inputs), folder))
        return inputs
    else:
        msg = "No files found in {}! Search extension are {}."
        raise IOError(msg.format(folder, search_path))


def sorted_inputs(paths, key="date_created"):
    """Return one by date sorted list of paths as tuples like (path, date).
    Key parameter is used to find attribut in netCDF to sort by.

    Returns
    -------

    list of tuple
        Sorted list of tuples holding input files path as string and date as integar e.g. (path, date).
        List ist sorted afer date. Date is integar in dayes based on January 1 of year 1
        (see date.toordinal() for more info).

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


def create_stack(template_file, ds_path, variables):
    """This open a NetCDF4 file and creates basic stack structure.

    Parameters
    ----------

    template: open netCDF4 handle

    ds_path: string
        Destination Path for stack file.

    Returns
    -------
    stack: file object
        Stack as open file handle.

    """

    dim_stacking = "date"

    # open target file
    try:
        stack = Dataset(ds_path, 'w', format="NETCDF4")
    except IOError:
        raise
    else:
        template = Dataset(template_file, "r")
        # use first input dataset as template

        temp_dim_lat = template.dimensions["lat"]
        temp_dim_lon = template.dimensions["lon"]

        # create dimmensions
        stack.createDimension(dim_stacking, None)
        stack.createDimension("lat", len(temp_dim_lat))
        stack.createDimension("lon", len(temp_dim_lon))

        # create variable in variables in stack file

        date = stack.createVariable(dim_stacking, "i8", (dim_stacking,))
        date.units = "days since 1-01-01 00:00:00 UTC"
        date.calendar = "gregorian"

        temp_var_lat = template.variables["lat"]
        temp_var_lon = template.variables["lon"]

        stack_lat = stack.createVariable("lat", temp_var_lat.datatype, ("lat",))
        stack_lon = stack.createVariable("lon", temp_var_lon.datatype, ("lon",))

        stack_lat[:] = temp_var_lat[:]
        stack_lon[:] = temp_var_lon[:]

        # create data Variables
        for name in variables:
            var = template.variables[name]
            stack_var = stack.createVariable(name, var.datatype, ("date", "lat", "lon"), zlib=True)

            # copy meta data for this variables
            stack_var.setncatts({k: var.getncattr(k) for k in var.ncattrs()})

        template.close()
        return stack


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

    logging.info('Create {} file.'.format(output))
    try:
        stack = create_stack(inputs[0][0], output, variables)
    except EnvironmentError as e:
        logging.error("Can't create {}".format(output))
        logging.debug((os.strerror(e.errno)))
        raise e

    for index, input__ in enumerate(inputs):

        input_path = input__[0]  # unpack input tuple
        logging.info('Extracting data from {}'.format(input_path))

        with Dataset(input_path, "r") as input:
            for name in variables:
                in_var = input.variables[name]
                stack.variables[name][index, :, :] = in_var[:]
                stack.variables["date"][index] = input__[1]

    stack.close()


class CoReSyFDataCubeCreation(CoReSyFTool):

    def run(self, bindings):

        # parse Parameters
        input_folder = bindings['Ssource']
        variables = tuple(bindings['var'].split(','))
        output = bindings['Ttarget']

        try:
            inputs = get_inputs(input_folder, extension="*.nc")
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
