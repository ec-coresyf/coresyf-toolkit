import lib.masking as masking

import numpy as np
from netCDF4 import Dataset

import itertools

path = 'C:/Users/hmrcgen/Projects/coresyf/data/tmp/09-07_data_cube.nc'
flags = [2, 5, 9, 13]

with Dataset(path, 'r') as cube:

    # for s in masking.Slices(cube, dim="date"):
    #    masking.mask_by_flags(s, flags, name="mask")
    mask = masking.aggregate_mask(cube, flags, dim="date", mask_var="mask")

    # print mask
    masking.masking_cube(cube, mask)


with Dataset(path, "r") as cube:
        mask_one = cube.variables["analysed_sst"][1, :, :].mask
        mask_tow = cube.variables["analysed_sst"][2, :, :].mask

        masks = []
        i = 1
        for i in range(1, 7):
            masks.append(cube.variables["analysed_sst"][i, :, :].mask)

        print len(masks)
        compbinations = itertools.combinations(masks, 2)

        for compbination in compbinations:
            assert (compbination[1] == compbination[0]).all()
