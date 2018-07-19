
from netCDF4 import Dataset

import lib.masking as masking
import numpy as np

def show_data(data):
    print "Min: {}".format(data.min())
    print "Max: {}".format(data.max())
    print "Mean: {}".format(data.mean())
    print "\n"
    print "Data:"
    print data
    print type(data)


def main():

    in_cube = Dataset("test_data/13-07-2018_cork_data_cube.nc", 'r', format="NETCDF4")
    #print in_cube.variables["analysed_sst"][0, 52:56, 22:26]
    # sst = in_cube.variables["analysed_sst"]
    # print "Data will by masked on export: {}".format(sst.mask)
    # print "Fill value: {}".format(sst._FillValue)


    # sst_arry = in_cube.variables["analysed_sst"][0, :, :]
    # np.ma.set_fill_value(sst_arry, -999)
    # print sst_arry.filled(-999)

    slice_ = {
        'variables': {
            "analysed_sst": in_cube.variables["analysed_sst"][0, :, :],
            "mask": in_cube.variables["mask"][0, :, :]
        }
    }
    # print slice_["variables"]["mask"][0, 0]
    # slice_["variables"]["mask"][0, 0] = 5
    # print slice_["variables"]["mask"][0, 0]

    mask = masking.mask_by_flags(slice_, flags=[2,])

    # TODO: Manipulaed on slice for north atlantik
    print mask[79:139,46:82]
    ######
    mask[79:139,46:82] = True
    ######
    print mask[79:139,46:82]

    out_cube = Dataset("test_data/out_cube.nc", "w", format="NETCDF4",)
    out_cube.set_auto_scale(False)

    for dname, the_dim in in_cube.dimensions.iteritems():

        out_cube.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)

    for v_name, varin in in_cube.variables.iteritems():

        # TODO: Change datatype and fill value in CoReSyFDataCubeMasking
        outVar = out_cube.createVariable(v_name, np.float32, varin.dimensions, fill_value=-999)

        # TODO: Check if need in CoReSyFDataCubeMasking
        outVar.set_auto_maskandscale(False)

        # TODO: Remove in CoReSyFDataCubeMasking
        #outVar.setncatts({k: varin.getncattr(k) for k in varin.ncattrs()})

        outVar[:] = varin[:]

    masking.masking_cube(out_cube,mask, dim='date')

    print out_cube.variables["analysed_sst"]
    # print out_cube.variables["analysed_sst"][0,79:139,46:82]

    in_cube.close()
    out_cube.close()

    #print sst_arry.__str__
    # print sst_arry
    # print np.ma.is_masked(in_cube.variables["analysed_sst"][0, :, :])
    # print in_cube.variables["mask"][0, 54, 24]

    # mask = masking.aggregate_mask(in_cube, ["1",], dim="date", mask_var="mask")
    # print mask[54, 24]



    # masking.masking_cube(out_cube, mask)




    #with Dataset("test_data\cube_masked_all.nc", 'r') as root:
        #print root
        # sst = root.variables['analysed_sst'][0,:,:]
        # mask = root.variables['mask'][0,:,:]
        #data = root.variables["analysed_sst"][0, :, :]
        #mask = root.variables["mask"][0, :, :]
        #show_data(data)
        #show_data(mask)


if __name__ == '__main__':
    main()
