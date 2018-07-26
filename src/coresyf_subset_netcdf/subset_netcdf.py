# # GDAL Approche
#
# ## ToDo:
#
# - build target path from source and variable
# - select variables to clip
# - research if date is in netCDF attributes after clliping
# - plot cliped target file
# - fix south oriantation
# - fix values should by in kelvin (apply scale and offset)
# - loop over all input files in folder
# - research how many decimal places the SST values are

import glob
import os
import subprocess

from pathlib2 import Path
from shapely import wkt

def get_inputs(source, pattern="*.nc"):
    path = os.path.join(
        source_folder,
        pattern
    )
    return glob.glob(path)


def wkt2bounds(wkt_str):
    geom = wkt.loads(wkt_str)
    return " ".join(map(str, geom.bounds))


def build_command(source,
                  target,
                  band,
                  bounds,
                  bounds_srs="EPSG:4326",
                  target_format='HFA'):

    """
    Returns shell command to clip source file using
    gdalwarp.

    Inputs
    ------
    source: string
        Source file path

    target: string
        Target file path

    band: string
        Name of band to clip

    bounds_srs: string
        SRS in which to interpret the bounds coordinates:

    bounds: string
        Extents of output file to be created

    region: string
        Polygon to clip by defined as WKT

    target_format: string
        Output format
    """

    command = (
        'gdalwarp '
        '-t_srs {0} '
        '-te {1} '
        '-of {2} '
        'NETCDF:"{4}":{3} '
        '-co COMPRESS=YES '
        '{5}').format(
            bounds_srs,
            bounds,
            target_format,
            band,
            source,
            target)

    return command


if __name__ == '__main__':
    print "run"



    # source_folder = os.path.join(
    #     "..",
    #     "data",
    #     "C_origin_cube",
    #     "2011_global_NetCDF"
    # )
    #
    # target_folder = os.path.join(
    #     "..",
    #     "data",
    #     "tmp"
    # )
    #
    # clip_polygon = "POLYGON ((-64 66.7, -6 66.7, -6 33, -64 33, -64 66.7, -64 66.7))"
    #
    # inputs = get_inputs(source_folder)
    # source = inputs[0]
    # name = os.path.basename(source)
    #
    # parameters = {
    #     'source': source,
    #     'target': os.path.join(target_folder, name),
    #     "bounds": wkt2bounds(clip_polygon),
    #     "band": "analysed_sst",
    # }
    #
    # command = build_command(**parameters)
    # print command
    # # output = subprocess.check_call(
    # #              command,
    # #              stderr=subprocess.STDOUT,
    # #              shell=True,
    # #              universal_newlines=True
    # # )
