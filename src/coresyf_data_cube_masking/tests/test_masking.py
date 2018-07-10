# coding: utf-8
# ! /usr/bin/env python2
"""This module collects tests for masking."""

import numpy as np
import os
import tempfile
import unittest

from netCDF4 import Dataset

from lib import masking


# Change if test data is changed
TEST_FOLDER = os.path.join('coresyf_data_cube_creation', 'test_data', 'GHRSST',)


def get_test_cube():
    """create a 3x3 test cube with 8 slices"""

    data = np.ones((3,3))
    mask = np.zeros((3,3), dtype=bool)

    variables = []

    index = 1
    for i in range(len(mask)):
        for j in range(len(data[i])):
            if not (i == 1 and j == 1):
                mask[i][j] = True
                index += 1
                variable = np.ma.array(data, mask=mask)

                variables.append(variable)
            mask = np.zeros((3, 3), dtype=bool)

    with Dataset("test.nc", 'w') as test_ds:
        test_ds.createDimension("date", None)
        test_ds.createDimension("lat", 3)
        test_ds.createDimension("lon", 3)

        data_var = test_ds.createVariable("data", "i4", ("date", "lat", "lon"))

        for idx, data in enumerate(variables):
            data_var[idx, :, :] = data
    return test_ds


# helper functions
class TestFlagsMasking(unittest.TestCase):
    """Test change masking by flags function."""

    def test_flags_invalid(self):
        """Test if elements with flag value 10 are invaid in variable."""


class TestMaskAggregation(unittest.TestCase):
    def setUp(self):
        pass

    def test_aggregate_eight_mask(self):
        """test if aggregated mask has 8 elemens == false"""
        test_cube = get_test_cube()
        masking.aggregate_mask(test_cube, flags=[], dim="date")
        pass


class TestMaskingCube(unittest.TestCase):
    """Test masking cube function"""

    def test_all_same_mask(self):
        """Test if all slices in datacube have same mask."""
        pass


if __name__ == '__main__':
    unittest.main()
