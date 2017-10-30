#!/usr/bin/env python
#==============================================================================
#                         <coresyf_image_crop.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Image Crop)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line raster cropping tool for GDAL supported files
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - IMAGE CROP
It uses the GDAL raster utility program "gdal_warp.py" to crop an image for a 
specific region of interest.
It allows cropping a raster based on any polygon shapefile. The extent of the
cropped raster is defined according with the bounding box or limits of the
polygon.

@example:
The geospatial images are usually very large with multidimensional arrays,
which impair the performance of geo-processing tasks. In order to reduce the
amount of processing time, the images are usually cropped to a specific area
of interest.  

Example 1 - Crop image using a polygon shapefile (or a .zip file):
./coresyf_image_crop.py -r etopo_raster.tif -c crop_limits.shp 
                        -o cropped_image.tif 

Example 2 - Crop image using a csv. file containing a polygon in WKT:
./coresyf_image_crop.py -r etopo_raster.tif -c crop_polygon_wkt.csv 
                        -o cropped_imageWKT.tif 

Example 3 - Crop image using WKT expression:
./coresyf_image_crop.py -r etopo_raster.tif 
                        --c_wkt "POLYGON ((-18.18 33.49,-15.39 33.79,-15.30 32.09,-18.11 32.06,-18.18 33.49))" 
                        -o cropped_imageWKT.tif


@attention: 
    @todo
    - Is projection checking performed???
    - Explore other limitations...


@version: v.1.0
@author:

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE = ( '\n'
          'coresyf_image_crop.py [-r <InputRaster>] [-c <Cropfile>]\n'
          '                      [--c_limits="<LonMin> <LatMin> <LonMax> <LatMax>"]\n'
          '                      [--c_wkt="<polygon_in_WKT>"]\n'
          "                      [-o <OutputRaster>] [--o_format=<OutputFileFormat>]"
          "\n")
#"[--o_type=<DataType>]" 

#DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']


''' SYSTEM MODULES '''
from optparse import OptionParser
import sys, os
import subprocess
import csv
from osgeo import ogr

''' PROGRAM MODULES '''
import wingsUtils


def main():
    parser = OptionParser(usage   = USAGE, 
                          version = VERSION)

    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-r', 
                      dest="input_raster", metavar=' ',
                      help="input raster file (GDAL supported file)", )
    parser.add_option('-c', 
                      dest="crop_file", metavar=' ',
                      help="input polygon shapefile or CSV defining crop limits",)
    parser.add_option('--c_limits', 
                      dest="crop_limits", metavar=' ',
                      help="list of values defining georeferenced crop limits",)
    parser.add_option('--c_wkt', 
                      dest="crop_wkt", metavar=' ',
                      help="text containing the crop polygon defined in WKT format",)
    parser.add_option('-o', 
                      dest="output_raster", metavar=' ',
                      help=("output raster file cropped to the extent of the "
                            "shapefile (default: 'cropped_image.tif')"),
                      default="cropped_image.tif")
    parser.add_option('--o_format', 
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'GTiff')",
                      default="GTiff" )    

    #==============================#
    #   Check mandatory options    #
    #==============================#
    (opts, args) = parser.parse_args()
    
    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.input_raster:
        print("No input raster provided. Nothing to do!")
        print(USAGE)
        return
    if opts.crop_wkt == '':
        # No crop, rename input file to be available to wings
        os.rename(opts.input_raster, opts.output_raster)
        print("Empty WKT provided. Output raster not cropped!")
        return

    if not opts.crop_file and not opts.crop_limits and not opts.crop_wkt:
        print("No input polygon or crop limits provided. Nothing to do!")
        print(USAGE)
        return

    #================================#
    #        Check crop input        #
    #================================#
    if opts.crop_file:
        try:
            opts.crop_file, wasUnZipped = wingsUtils.prepareInputData(opts.crop_file, ".shp")
        except Exception as msg:
            print(str(msg))
            print(USAGE)
            return
    
    if opts.crop_limits:
        try:
            crop_limits = [float(i) for i in opts.crop_limits.split(' ')]
            LonMin, LatMin, LonMax, LatMax = crop_limits
            
            if LonMin > 180 or LonMin < -180: 
                print("LonMin value out of range [-180, 180]!")
                raise Exception
            if LonMax > 180 or LonMax < -180:
                print("LonMax value out of range [-180, 180]!")
                raise Exception
            if LatMin > 90 or LatMin < -90:
                print("LatMin value out of range [-90, 90]!")
                raise Exception
            if LatMax > 90 or LatMax < -90:
                print("LatMax value out of range [-90, 90]!")
                raise Exception
            if LatMax < LatMin: 
                print("LatMax is higher than LatMin!")
                raise Exception
            if LonMax < LonMin:
                print("LonMax is higher than LonMin!")    
                raise Exception      
        except Exception:
            print("Incorrect crop limits!")
            print('Example: --c_limits="-100 -60 100 60"')
            print(USAGE)
            return
    
    if opts.crop_wkt:
        # Create a geometry from WKT expression
        try:
            geo = ogr.CreateGeometryFromWkt(opts.crop_wkt)
            if not geo: # Case no exceptions are raised (Most likely)
                raise Exception
        except Exception as message:
            print ('WKT Expression Error. Check syntax')
            print ('Example: --c_wkt="POLYGON ((-18.18 33.49,-15.39 33.79,-15.39 33.79))"')
            return
        
        # Create a temporary CSV file with WKT expression
        opts.crop_wkt = os.path.abspath("temp_crop_polygon.csv")
        csv_file = open(opts.crop_wkt, 'wt')
        try:
            writer = csv.writer(csv_file)
            writer.writerow( ("id", "WKT") )
            writer.writerow( ("0", geo.ExportToWkt()) )
        except Exception as message:
            print ('Error: Unable to create temporary file with WKT expression.')
            return
        finally:
            csv_file.close()

    #================================#
    # Building gdalwarp command line #
    #================================#
    gdal_exe = 'gdalwarp '
    
    raster_opts = ''
    if opts.crop_file:
        raster_opts = '-cutline %s -cl %s -crop_to_cutline ' % (opts.crop_file, 
                                                                os.path.basename(opts.crop_file).split('.')[0])
    elif opts.crop_limits:
        raster_opts = '-te %s' % opts.crop_limits
    else:
        raster_opts = '-cutline %s -crop_to_cutline ' % (opts.crop_wkt) 

    output_opts = '%s %s -of %s ' % (opts.input_raster,
                                     opts.output_raster,
                                     opts.output_format) 
    
    gdalwarp_command = gdal_exe + raster_opts + output_opts
    
    #===========================#
    # Run gdalwarp command line #
    #===========================#
    #print ('\n' + gdalwarp_command)
    #print("\nRunning using Python version %s.%s.%s..." % sys.version_info[:3])
    try:
        process = subprocess.Popen( gdalwarp_command,
                                    shell  = True,
                                    stdin  = subprocess.PIPE,
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE )
        # Reads the output and waits for the process to exit before returning
        stdout, stderr = process.communicate()
        if process.returncode:
            raise Exception (stderr.decode())
        else:
            print (stdout.decode())
            print (stderr.decode()) # stderr may include warning messages
    except Exception as message:
        print( "ERROR: " + str(message) )
        sys.exit(process.returncode)
    finally:
        # Delete temporary files
        if opts.crop_file and wasUnZipped:
            wingsUtils.clearTempData( opts.crop_file )
        if opts.crop_wkt and os.path.exists(opts.crop_wkt):
            os.remove(opts.crop_wkt)


if __name__ == '__main__':
    main()