# coding: utf-8
# ! python2

from coresyftools.tool import CoReSyFTool
from lib import masking
from netCDF4 import Dataset


class CoReSyFDataCubeMasking(CoReSyFTool):

    def run(self, bindings):
        input = bindings['Ssource']
        flags = list(bindings['flags'].split(","))
        target = bindings['Ttarget']

        with Dataset(input, 'r', format="NETCDF4") as in_cube:
            mask = masking.aggregate_mask(in_cube, flags, dim="date", mask_var="mask")

        with Dataset(target, "w", format="NETCDF4") as out_cube:
            masking.masking_cube(cube, mask)
            # TODO: create copy of input cube and change variables to masked version
