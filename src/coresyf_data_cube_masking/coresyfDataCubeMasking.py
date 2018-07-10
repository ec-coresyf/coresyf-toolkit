# coding: utf-8
# ! python2

from lib import masking

class CoReSyFDataCubeMasking(CoReSyFTool):

    def run(self, bindings):
        input = bindings['Ssource']
        flags = list(bindings['flags'])

        with Dataset(input, 'r', format="NETCDF4") as in_cube:

            # for s in masking.Slices(cube, dim="date"):
            #    masking.mask_by_flags(s, flags, name="mask")
            mask = masking.aggregate_mask(in_cube, flags, dim="date", mask_var="mask")

        with Dataset(Ttarget, "w", format="NETCDF4") as out_cube:
            # TODO: create copy of input cube and change variables to masked version
            masking.masking_cube(cube, mask)
        # parse Parameters
        # masking data cube
        pass
