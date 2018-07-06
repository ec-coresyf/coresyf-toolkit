# coding: utf-8
# ! /usr/bin/env python2
"""This module collects tests for create data cube."""

import numpy as np
import unittest
import tempfile
import os

from netCDF4 import Dataset

from coresyf_data_cube_creation.coresyfDataCubeCreation import get_inputs
from coresyf_data_cube_creation.coresyfDataCubeCreation import extract_slice
from coresyf_data_cube_creation.coresyfDataCubeCreation import create_stack
from coresyf_data_cube_creation.coresyfDataCubeCreation import write_slice
from coresyf_data_cube_creation.coresyfDataCubeCreation import stacking
from coresyf_data_cube_creation.coresyfDataCubeCreation import sorted_inputs


# Change if test data is changed
TEST_FOLDER = os.path.join('coresyf_data_cube_creation',
        'test_data',
        'GHRSST',)

TEST_DATA = os.path.join('coresyf_data_cube_creation',
        'test_data',
        'GHRSST',
        '20170101090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc')

VARIABLES = ['mask', 'analysed_sst', 'analysis_error']


# helper functions

def get_data_dict():
    """Return data dict by using extract_data()"""
    file_path = os.path.abspath(TEST_DATA)
    return extract_slice(file_path, variables=VARIABLES)

def get_dest_path(f_path='output.nc'):
    tempdir = tempfile.mkdtemp()
    return os.path.join(tempdir, f_path)

def create_netcdf_file(data, dest_path):
    create_stack_file(data, dest_path)

class TestGetInputs(unittest.TestCase):
    def setUp(self):
        self.inputdir = tempfile.mkdtemp()

    def test_input_folder_empty(self):
        empty = self.inputdir
        with self.assertRaises(IOError):
            inputs = get_inputs(empty, pattern="*.nc")

    def test_inputs_found(self):
        inputs = get_inputs(TEST_FOLDER)


class TestSortedInputs(unittest.TestCase):
    """docstring for TestSortedInputs."""
    def setUp(self):
        self.inputs = get_inputs(TEST_FOLDER)

    def test_file_not_found(self):
        self.inputs[0] = "broken.nc"
        with self.assertRaises(IOError):
            inputs = sorted_inputs(self.inputs)

    def test_sorted_inputs(self):
        inputs = sorted_inputs(self.inputs)
        self.assertTrue(inputs)

    def test_youngest_first(self):
        inputs = sorted_inputs(self.inputs)
        first = inputs[0][1]
        secound = inputs[1][1]
        self.assertGreater(first, secound)

    def test_key_attribut_not_found(self):
        inputs = sorted_inputs(self.inputs, key="not_found_attribut")
        inputs_range = range(inputs[-1][1], inputs[0][1])
        self.assertEqual(inputs_range, range(0,6))

class TestExtractData(unittest.TestCase):
    def setUp(self):
        self.file_path = os.path.abspath(TEST_DATA)

    def test_get_date_created(self):
        """This tests getting date created from input dataset"""
        data = extract_slice(self.file_path)
        self.assertEqual(data['date'], 736333)

    def test_dimensions(self):
        """This tests if data dict has dimensions."""

        data = extract_slice(self.file_path)
        self.assertIsNotNone(data['dimensions']['lat'], "Latitude dimension is undefined!")
        self.assertIsNotNone(data['dimensions']['lon'], "Longitude dimension is undefined")
        self.assertTrue(data['dimensions']['lat'].size > 0, "Latitude dimension is empty!")
        self.assertTrue(data['dimensions']['lon'].size > 0, "Longitude dimension is empty!")

    def test_one_variables(self):
        """This tests if data dict has variables."""
        data = extract_slice(self.file_path, variables=['analysed_sst'])
        self.assertIsNotNone(data['variables']['analysed_sst'], "Variable is not in data dict!")
        self.assertTrue(data['variables']['analysed_sst'].size > 0, "Variable is empty!")

    def test_extract_variables_list(self):
        """This tests if data dict has variables."""
        data = extract_slice(self.file_path, variables=['analysed_sst','analysis_error'])
        self.assertIsNotNone(data['variables']['analysed_sst'], "Variable is not in data dict!")
        self.assertTrue(data['variables']['analysed_sst'].size > 0, "Variable is empty!")

    def test_variables_are_2D(self):
        """This tests if data dict has variables."""
        data = extract_slice(self.file_path)
        self.assertTrue(data['variables']['analysed_sst'].ndim == 2, "Variable is not 2D!")

    def test_variable_not_in_dataset(self):
        """Test print error message if variable is not in dataset."""
        data = extract_slice(self.file_path, variables=['not_in_dataset'])
        with self.assertRaises(KeyError):
            data['not_in_dataset']

    def test_skipping_not_in_dataset_variables(self):
        """Test print error message if variable is not in dataset."""
        data = extract_slice(self.file_path, variables=['not_in_dataset', 'analysed_sst'])
        self.assertIsNotNone(data['variables']['analysed_sst'], "Skipping of not in dataset failed.")

    def test_skipping_not_2D_variables(self):
        """Test print error message if variable is not in dataset."""
        data = extract_slice(self.file_path, variables=['lat'])
        with self.assertRaises(KeyError):
            data['lat']


class TestCreateStack(unittest.TestCase):
    def setUp(self):
        self.data = get_data_dict()
        self.dest_path = get_dest_path()

    def tearDown(self):
        if os.path.exists(self.dest_path):
            os.remove(self.dest_path)

    def test_create_netcdf(self):
        dest_path = self.dest_path
        data = self.data
        stack = create_stack(data, dest_path)
        self.assertTrue(os.path.exists(dest_path), "File {} not created.".format(dest_path))
        stack.close()

class TestStackStructure(unittest.TestCase):
    def setUp(self):
        data = get_data_dict()
        self.variables = data['variables']
        self.dimmensions = data['dimensions']
        self.dest_path = get_dest_path()
        self.stack = create_stack(data, self.dest_path)

    def tearDown(self):
        self.stack.close()
        if os.path.exists(self.dest_path):
            os.remove(self.dest_path)

    def test_lat_lon_dimensions_filled(self):
        dim = self.stack.dimensions
        self.assertTrue(dim['lat'].size > 0)
        self.assertTrue(dim['lon'].size > 0)

    def test_variables_in_dataset(self):
        msg = "Variable {} not in dataset."
        for var in self.stack.variables:
            self.assertTrue(var in self.stack.variables.keys(), msg.format(var))


class TestWriteSlice(unittest.TestCase):
    def setUp(self):
        self.data = get_data_dict()
        self.dest_path = get_dest_path()
        self.stack = create_stack(self.data, self.dest_path)
        self.variables = self.data["variables"]

    def tearDown(self):
        self.stack.close()
        if os.path.exists(self.dest_path):
            os.remove(self.dest_path)

    def test_write_variable(self):
        msg = "Variable {} is empty in dataset."
        write_slice(self.data, self.stack, index=1)
        for var in self.variables:
            self.assertTrue(self.stack.variables[var].size > 0, msg.format(var))

    def test_time_dimension_is_three(self):
        msg = "Time dimension size is {} not {}."
        times = 3
        for step in range(0,times):
            write_slice(self.data, self.stack, index=step)

        time_dimension = self.stack.dimensions['date']
        self.assertTrue(time_dimension.size == times, msg.format(time_dimension.size, times))

class TestStacking(unittest.TestCase):
    def setUp(self):
        self.inputs = sorted_inputs(get_inputs(TEST_FOLDER))
        self.empty_dir = tempfile.mkdtemp()
        self.output = get_dest_path()

    def test_number_stack_slices_same_as_input(self):
        """test number of time slices equal to number of files"""
        stacking(self.inputs, VARIABLES, self.output)
        with Dataset(self.output, 'r') as stack:
            slices = stack.dimensions['date']
            self.assertEqual(len(slices), 7)

    def test_number_variables(self):
        stacking(self.inputs, VARIABLES, self.output)
        with Dataset(self.output, 'r') as stack:
            var_in = stack.variables.keys()
            contains = all(elem in var_in for elem in VARIABLES)
            self.assertTrue(contains)

if __name__ == '__main__':
    unittest.main()
