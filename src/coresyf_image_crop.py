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

Example 1 - Crop image using a polygon shapefile:
./coresyf_image_crop.py -r etopo_raster.tif -c crop_limits.shp 
                        -o cropped_image.tif 


@attention: 
    @todo
    - Is projection checking performed???
    - Explore other limitations...


@version: v.1.0
@author: RCCC

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( '\n'
            'coresyf_image_crop.py [-r <InputRaster>] [-c <CropShapefile>]\n'
            '                      [--c_limits="<LonMin> <LatMin> <LonMax> <LatMax>"]\n'
            "                      [-o <OutputRaster>] [--o_format=<OutputFileFormat>]"
 #           "[--o_type=<DataType>]" 
            "\n")

#DefaultTypesLookup = ['Byte','UInt16','Int16','UInt32','Int32','Float32','Float64']


''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
import subprocess


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
                      dest="crop_shape", metavar=' ',
                      help="input polygon shapefile defining crop limits",)
    parser.add_option('--c_limits', 
                      dest="crop_limits", metavar=' ',
                      help="list of values defining georeferenced crop limits",)
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
    if not opts.crop_shape and not opts.crop_limits:
        print("No input polygon shapefile or crop limits provided. Nothing to do!")
        print(USAGE)
        return    
    #================================#
    #        Check crop limits       #
    #================================#
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
        except:
            print("Incorrect crop limits!")
            print('Example: --c_limits="-100 -60 100 60"')
            print(USAGE)
            return
    
    #================================#
    # Building gdalwarp command line #
    #================================#
    gdal_exe    = 'gdalwarp '
    
    raster_opts = ''
    if opts.crop_shape:
        raster_opts = '-cutline %s -cl %s -crop_to_cutline ' % (opts.crop_shape, 
                                                                opts.crop_shape.split('.')[0])
    else:
        raster_opts = '-te %s' % opts.crop_limits
    
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
                                    stderr = subprocess.PIPE, )
        # Reads the output and waits for the process to exit before returning
        stdout, stderr = process.communicate()   
        print (stdout) 
        print('I am runnin')
        print(stderr)
        
        
        if stderr:      raise Exception (stderr)  # or  if process.returncode:
    except Exception, message:
        
        print( str(message) )
        
        sys.exit(process.returncode)
    

if __name__ == '__main__':
    main()