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

        in_cube = Dataset(input, 'r', format="NETCDF4")
        mask = masking.aggregated_mask(in_cube, flags, dim="date", mask_var="mask")
        out_cube = Dataset(target, "w", format="NETCDF4")
        masking.masking_cube(out_cube, mask)

        in_cube.close()
        out_cube.close()


        # TODO: create copy of input cube and change variables to masked version
