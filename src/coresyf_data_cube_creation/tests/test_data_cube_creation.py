# coding: utf-8
# ! /usr/bin/env python2
"""This module collects tests for create data cube."""

import numpy as np
import unittest
from os import path


from coresyf_data_cube_creation.data_cube import search_files
from coresyf_data_cube_creation.data_cube import extract_data


# Change if test data is changed
TEST_DATA = path.join('coresyf_data_cube_creation',
        'test_data',
        'GHRSST',
        '20170101090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc')
VARIABLES = ['mask', 'analysed_sst', 'analysis_error']



class TestExtractData(unittest.TestCase):
    def setUp(self):
        self.file_path = TEST_DATA
        pass

    def test_extract_data_has_dimensions(self):
        """This text data extraction by variable."""
        file_path = path.abspath(self.file_path)
        no_bbox = None

        data = extract_data(file_path, no_bbox)
        self.assertIsNotNone(data['dimensions']['lat'])
        self.assertIsNotNone(data['dimensions']['lon'])
        self.assertTrue(data['dimensions']['lat'].size > 0)
        self.assertTrue(data['dimensions']['lon'].size > 0)

    
if __name__ == '__main__':
    unittest.main()
