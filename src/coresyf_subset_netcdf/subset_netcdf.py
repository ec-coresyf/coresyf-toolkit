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

import os
import subprocess

from pathlib2 import Path
from shapely import wkt

import pprint


def get_inputs(source, pattern="*.nc"):
    return sorted(source.glob(pattern))


def wkt2bounds(wkt_str):
    geom = wkt.loads(wkt_str)
    return " ".join(map(str, geom.bounds))


def build_command(source,
                  target_folder,
                  band,
                  bounds,
                  bounds_srs="EPSG:4326",
                  target_format='HFA'):

    """
    Returns shell command to clip source file using
    gdalwarp.

    Inputs
    ------
    source: PurePath
        Source file path

    target_folder: PurePath
        Target folder path

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
    # source file
    source_str = str(source)

    # target file
    extentions = {
        'HFA': ".img"
    }
    extention = extentions[target_format]
    target_name = "{}_{}{}".format(source.stem, band, extention)
    target_file = Path(target_folder / target_name)
    target_str = str(target_file)

    command = (
        'gdalwarp '
        '-t_srs {0} '
        '-te {1} '
        '-of {2} '
        '-overwrite '
        'NETCDF:"{4}":{3} '
        '-co COMPRESS=YES '
        '"{5}"').format(
            bounds_srs,
            bounds,
            target_format,
            band,
            source_str,
            target_str)

    return command


if __name__ == '__main__':
    print "run"

    source_folder = Path("C:/Users/hmrcgen/Projects/coresyf/data/C_origin_cube/2011_global_NetCDF")

    target_folder = Path("C:/Users/hmrcgen/Projects/coresyf/data/tmp/2011")

    clip_polygon = "POLYGON ((-64 66.7, -6 66.7, -6 33, -64 33, -64 66.7, -64 66.7))"

    inputs = get_inputs(source_folder)

    parameters = {
        'source': "",
        'target_folder': target_folder,
        "bounds": wkt2bounds(clip_polygon),
        "band": "",
    }

    bands = ["analysed_sst", "mask"]

    for input in inputs:
        parameters["source"] = input

        for band in bands:
            parameters["band"] = band
            command = build_command(**parameters)
            print command

            output = subprocess.check_call(
                command,
                stderr=subprocess.STDOUT,
                shell=True,
                universal_newlines=True
            )
