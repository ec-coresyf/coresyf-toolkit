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

import argparse
import os
import subprocess

from pathlib2 import Path
from shapely import wkt
from shapely.geometry.polygon import Polygon
from shapely.errors import WKTReadingError

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

# CLI


class valid_polygon(argparse.Action):
    """Polygon validation
    Check if polygon input follow the WKT standard format and is of type POLYGON.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_polygon = values
        try:
            geom = wkt.loads(prospective_polygon)
        except WKTReadingError:
            raise argparse.ArgumentTypeError(
                "polygon: {0} WKT definition is unvalid!".format(prospective_polygon)
            )
        if not isinstance(geom, Polygon):
            raise argparse.ArgumentTypeError(
                "polygon: Is is not a Polygon!"
            )
        else:
            setattr(namespace, self.dest, prospective_polygon)


class valid_bbox(argparse.Action):
    """Bounding Box validation
    Check if bbox input follow the standard format:
    bbox = min Longitude , min Latitude , max Longitude , max Latitude
    """
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_bbox = values
        min_Lon = prospective_bbox[0]
        min_Lat = prospective_bbox[1]
        max_Lon = prospective_bbox[2]
        max_Lat = prospective_bbox[3]

        if not (min_Lon < max_Lon) and not (min_Lat < max_Lat):
            raise argparse.ArgumentTypeError(
                "bbox:{0} is not a valid bounding box!".format(prospective_bbox)
            )
        else:
            setattr(namespace, self.dest, prospective_bbox)


class readable_dir(argparse.Action):
    """Check if folder is existing and readable."""
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="subset_netcdf",
        description="""
        This tool subset NetCDF files by a list of variables.
        Optinal those subset can also by cliped by an area
        defined as BBOX or Well-known text (WKT) POLYGON.""",
        epilog="""Examples:

        subset_netcdf -b mask, analysed_sst -p "POLYGON ((-64 66.7, -6 66.7, -6 33, -64 33, -64 66.7, -64 66.7))" NetCDF_folder/ target_folder/

        subset_netcdf -b analysed_sst -c -64 33 -6 67 NetCDF_folder/ target_folder/

        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-b',
        '--bands',
        nargs='+',
        help='List of band names to subset.',
        required=True)

    parser.add_argument(
        '-c',
        '--bbox',
        nargs=4,
        action=valid_bbox,
        help="Area to subset as Bounding Box.",
        metavar=('xmin', 'ymin', 'xmax', 'ymax'))

    parser.add_argument(
        '-p',
        '--polygon',
        action=valid_polygon,
        help="Area to subset defined as polygon in WKT.",
        metavar='WKT POLYGON')

    parser.add_argument(
        'source',
        action=readable_dir,
        help='Folder to read NetCDF files from.')

    parser.add_argument(
        'target',
        action=readable_dir,
        help='Folder to write subset files in.')

    args = parser.parse_args()

    source_folder = Path(args.source)

    target_folder = Path(args.target)

    if args.polygon:
        bounds = wkt2bounds(args.polygon)
    else:
        bounds = args.bbox
