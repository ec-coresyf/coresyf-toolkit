# coding: utf-8
# ! /usr/bin/env python2
"""This module collects tests for masking."""

import itertools
import numpy as np
import os
import tempfile
import unittest

from netCDF4 import Dataset

from lib import masking


# Change if test data is changed
TEST_FOLDER = os.path.join('coresyf_data_cube_creation', 'test_data', 'GHRSST',)


def cube_file():
    _, cube_file = tempfile.mkstemp(suffix=".nc")
    return cube_file


def fill_test_cube(test_ds):
    """create a 3x3 test cube with 8 slices"""

    data = np.ones((3, 3))
    mask = np.zeros((3, 3), dtype=bool)

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

    test_ds.createDimension("date", None)
    test_ds.createDimension("lat", 3)
    test_ds.createDimension("lon", 3)

    data_var = test_ds.createVariable("data", "i4", ("date", "lat", "lon"))

    for idx, data in enumerate(variables):
        data_var[idx, :, :] = data


class TestGetSlice(unittest.TestCase):
    """Test slicing in one dimension order."""
    def setUp(self):
        pass

    def test_get_slice(self):
        """Test if first slice in cube is like input array"""

        data = np.ones((3, 3), dtype=int)
        mask = np.zeros((3, 3), dtype=bool)
        self.origin = np.ma.array(data, mask=mask)
        self.origin[0, 0] = np.ma.masked

        cube = cube_file()
        with Dataset(cube, "w", format="NETCDF4") as cube:
            fill_test_cube(cube)
            data = masking.get_slice(cube, 0)["variables"]["data"]
        self.assertTrue(np.allclose(self.origin, data))


class TestFlagsMasking(unittest.TestCase):
    """Test change masking by flags function."""
    def setUp(self):

        self.flag_value = 10

        data = np.ones((3, 3), dtype=int)
        mask = np.zeros((3, 3), dtype=bool)
        variable = np.ma.array(data, mask=mask)

        data_mask = np.zeros((3, 3), dtype=int)
        data_mask[1, 1] = self.flag_value

        self.test_slice = {
            "dim_ids": 1,
            "variables": {
                "data": variable,
                "mask": data_mask
            },
        }

    def test_flags_invalid(self):
        """Test if elements with flag value 10 are invaid in variable."""
        mask = masking.mask_by_flags(
            self.test_slice,
            flags=[self.flag_value, ],
            name="mask")
        self.assertTrue(mask[1, 1])


class TestMaskAggregation(unittest.TestCase):
    def setUp(self):
        self.cube_file = cube_file()

    def test_aggregate_eight_mask(self):
        """test if aggregated mask has 8 elemens == false"""
        test = [[True, True, True],
                [True, False, True],
                [True, True, True]]
        with Dataset(self.cube_file, "w", format="NETCDF4") as cube:
            fill_test_cube(cube)
            aggregated = masking.aggregate_mask(cube, flags=[], dim="date")
        self.assertTrue(np.array_equal(aggregated, test))


class TestMaskingCube(unittest.TestCase):
    """Test masking cube function"""
    def setUp(self):
        self.cube_file = cube_file()
        self.cube_mask = [[True, True, True],
                          [True, False, True],
                          [True, True, True]]

    def test_all_same_mask(self):
        """Test if all slices in cube have same mask."""

        with Dataset(self.cube_file, "w", format="NETCDF4") as cube:
                fill_test_cube(cube)

                masking.masking_cube(cube, self.cube_mask)

                masks = []
                for i in range(1, len(cube.dimensions["date"])):
                    masks.append(cube.variables["data"][i, :, :].mask)

                compbinations = itertools.combinations(masks, 2)

                for compbination in compbinations:
                    # print compbination[1]
                    # print compbination[0]
                    self.assertTrue(
                        np.array_equal(compbination[1], compbination[0])
                    )


if __name__ == '__main__':
    unittest.main()
