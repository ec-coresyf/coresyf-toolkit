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
        mask = masking.aggregate_mask(in_cube, flags, dim="date", mask_var="mask")

        out_cube = Dataset(target, "w", format="NETCDF4")

        # copy in cube to out_cube
        for dname, the_dim in in_cube.dimensions.iteritems():
            out_cube.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)

        for v_name, varin in in_cube.variables.iteritems():
            outVar = out_cube.createVariable(v_name, varin.datatype, varin.dimensions, fill_value=-999)

            # Copy variable attributes
            outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})

            outVar[:] = varin[:]

        masking.masking_cube(out_cube, mask)

        in_cube.close()
        out_cube.close()


        # TODO: create copy of input cube and change variables to masked version
