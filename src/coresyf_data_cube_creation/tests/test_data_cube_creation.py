# coding: utf-8
# ! /usr/bin/env python2
"""This module collects tests for create data cube."""

import numpy as np
import unittest
import tempfile
import os

from netCDF4 import Dataset

from coresyfDataCubeCreation import get_inputs
from coresyfDataCubeCreation import create_stack
from coresyfDataCubeCreation import stacking
from coresyfDataCubeCreation import sorted_inputs


# Change if test data is changed
TEST_FOLDER = os.path.join(
    'test_data',
    'GHRSST',)

TEST_DATA = os.path.join(
    'test_data',
    'GHRSST',
    '20170101090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc')

VARIABLES = ['analysed_sst', 'analysis_error', 'mask']


# helper functions

def get_dest_path(f_path='output.nc'):
    tempdir = tempfile.mkdtemp()
    return os.path.join(tempdir, f_path)


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
        self.assertEqual(inputs_range, range(0, 6))


class CreateStack(unittest.TestCase):
    def setUp(self):
        self.in_file = TEST_DATA
        self.ds_path = get_dest_path()
        self.variables = VARIABLES

    def test_all_variables(self):
        stack = create_stack(
            self.in_file,
            self.ds_path,
            self.variables
        )
        self.assertIs(len(stack.variables), len(VARIABLES))


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
