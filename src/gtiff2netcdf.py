
#!/usr/bin/env python
#==============================================================================
#                         <gtiff2netcdf.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (GeoTiff to netCDF conversor)
# Language  : Python (v.2.7)
#------------------------------------------------------------------------------
# Scope : (see the following docstring)
# Usage : python gtiff2netcdf.py
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module includes a function to convert GeoTiff into netCDF files (NetCDF with
CF conventions).

It will be used to convert the application outputs, in GeoTiff, into netCDF format
 in order to make easy the ingestion by Geoserver and layers/bands publication.   
The min and max values of each band are also computed and included in the returned
object.

------------------------------------------------------------------------------
@info
Adapted from: 
https://gis.stackexchange.com/questions/70458/convert-timeseries-stack-of-gtiff-raster-to-single-netcdf

GDAL/OGR Cookbook documentation:
https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
------------------------------------------------------------------------------
@version: v.1.0
@author: STeam
------------------------------------------------------------------------------

@change:
1.0
- First release of the tool.

'''


import os
import datetime
from osgeo import gdal

import numpy as np
import netCDF4


def convert_geotiff_into_netcdf(gtiff_src, output_netcdf):

    #=========================#
    #    Read GeoTiff file    #
    #=========================#
    src_ds = gdal.Open(gtiff_src, gdal.GA_ReadOnly)
    n_bands = src_ds.RasterCount 
    bands_id_list = [i for i in range(1, n_bands+1)]

    nlon = src_ds.RasterXSize
    nlat = src_ds.RasterYSize
    geotransform = src_ds.GetGeoTransform()
    origin_lon = geotransform[0]
    origin_lat = geotransform[3]
    pix_size_lon = geotransform[1]
    pix_size_lat = geotransform[5]

    lon = np.arange(nlon)*pix_size_lon + origin_lon
    lat = np.arange(nlat)*pix_size_lat + origin_lat

    #=========================#
    #   Create NetCDF file    #
    #=========================#
    nco = netCDF4.Dataset(output_netcdf, 'w', format='NETCDF4')

    ## Creating netCDF info ##
    nco.Conventions = 'CF-1.6, ACDD-1.3'
    #nco.standard_name_vocabulary = 'CF Standard Name Table v29'
    #nco.creator_name = ''
    #nco.creator_url = ''
    #nco.institution = ''
    #nco.title = ''
    #nco.summary = ''
    #nco.source = ''
    timestamp = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%dT%H:%M:%S')
    nco.date_created = timestamp
    nco.history = timestamp + ' - netCDF file creation\n'

    # Grid
    nco.cdm_data_type = 'Grid'    
    nco.geospatial_lat_min = str(np.min(lat))
    nco.geospatial_lat_max = str(np.max(lat))
    nco.geospatial_lat_units = 'degrees_north'
    nco.geospatial_lon_min = str(np.min(lon))
    nco.geospatial_lon_max = str(np.max(lon))
    nco.geospatial_lon_units = 'degrees_east'

    # Time coverage   
    #nco.time_coverage_start = datetime.datetime.strftime(ti1[0], '%Y-%m-%dT%H:%M:%S')
    #nco.time_coverage_end = datetime.datetime.strftime(ti1[-1], '%Y-%m-%dT%H:%M:%S')
    #dt = ti1[-1] - ti1[0]
    #nco.time_coverage_duration = 'P' + str(dt.days) + 'D'
    #dt = ti1[1] - ti1[0]
    #nco.time_coverage_resolution = 'P' + str(dt.seconds / 60 / 60) + 'H'

    ## Dimensions ##
    # chunking is optional, but can improve access a lot: 
    # (see: http://www.unidata.ucar.edu/blogs/developer/entry/chunking_data_choosing_shapes)
    # chunk_lon=16
    # chunk_lat=16
    # chunk_time=12
    nco.createDimension('lon', nlon)
    nco.createDimension('lat', nlat)
    nco.createDimension('time', 1)

    # Time
    timeo = nco.createVariable('time', 'f4', ('time'), zlib=True, complevel=4)
    timeo.standard_name = 'time'
    timeo.long_name = 'time'
    timeo.units = 'hours since 1970-01-01 00:00:00'
    timeo.calendar = 'gregorian'
    timeo[:] = np.nan # netCDF4.date2num(datetime.datetime.now(), units=timeo.units, calendar=timeo.calendar)

    # Lat
    lato = nco.createVariable('lat', 'f4', ('lat'), fill_value=-9999, zlib=True, complevel=4)
    lato.standard_name = 'latitude'
    lato.long_name = 'Latitude'
    lato.units = 'degrees_north'
    lato[:] = lat

    # Lon
    lono = nco.createVariable('lon', 'f4', ('lon'), fill_value=-9999, zlib=True, complevel=4)
    lono.standard_name = 'longitude'
    lono.long_name = 'Longitude'
    lono.units = 'degrees_east'
    lono[:] = lon

    # create container variable for CRS: lon/lat WGS84 datum
    crso = nco.createVariable('crs','i4')
    crso.long_name = 'Lon/Lat Coords in WGS84'
    crso.grid_mapping_name='latitude_longitude'
    crso.longitude_of_prime_meridian = 0.0
    crso.semi_major_axis = 6378137.0
    crso.inverse_flattening = 298.257223563

    ## Create variables for each band ####
    for i in bands_id_list:
        srcband = src_ds.GetRasterBand(i)
        band_array = srcband.ReadAsArray() #.astype(numpy.float)
        band_name = os.path.basename ( os.path.splitext(gtiff_src)[0] ) + '_band_' + str(i)

        print ('Writing band ' + band_name + ' into netCDF file....')
        print (np.nanmin(band_array))
        print (np.nanmean(band_array)) # numpy.median(zoneraster), numpy.std(zoneraster), numpy.var(zoneraster)
        print ( srcband.GetMetadata() )
        
        varo = nco.createVariable(band_name, 'f4',  ('time', 'lat', 'lon'),
                                fill_value=-9999, zlib=True, complevel=6,)
                                #chunksizes=[chunk_time,chunk_lat,chunk_lon])
        varo.standard_name = band_name
        varo.long_name = band_name
        varo.units = ''
        varo.grid_mapping = 'crs'
        varo.valid_min = np.nanmean(band_array) - 2*np.nanstd(band_array) #np.nanmin(band_array)
        varo.valid_max = np.nanmean(band_array) + 2*np.nanstd(band_array) #np.nanmax(band_array)
        #varo.scale_factor = 0.01
        #varo.add_offset = 0.00
        #varo.set_auto_maskandscale(False)
        varo[:] = band_array

    nco.close()



if __name__ == '__main__':
    ### EXAMPLE/TEST 1 ####
    gtiff = 'myoutput.tif'
    netcdf = 'myoutput_new.nc'

    convert_geotiff_into_netcdf(gtiff, netcdf)



#########################################
#           OLD METHOD                  #
#########################################
'''
def convert_geotiff_into_netcdf(gtiff_src, output_netcdf):
    # Open existing dataset
    src_ds = gdal.Open(gtiff_src)
    # Open output format driver, see gdal_translate --formats for list
    tmp_format = "GTiff"
    driver = gdal.GetDriverByName(tmp_format)
    # Output to new format
    dst_ds = driver.CreateCopy(gtiff_src + '.tiff', src_ds, 0)
    # Properly close the datasets to flush to disk
    dst_ds = None
    src_ds = None

    # Open existing dataset
    src_ds = gdal.Open(gtiff_src + '.tiff')

    # Open output format driver, see gdal_translate --formats for list
    target_format = "netCDF"
    driver = gdal.GetDriverByName(target_format)

    # Output to new format
    dst_ds = driver.CreateCopy(output_netcdf + '.nc', src_ds, 0)

    # Properly close the datasets to flush to disk
    dst_ds = None
    src_ds = None

    # Remove intermediate file
    os.remove(gtiff_src + '.tiff')


gtiff_src = '/home/rccc/Downloads/z_OnGPT/myoutput.tif'
output_netcdf = '/home/rccc/Downloads/z_OnGPT/myoutput_old_methods'

convert_geotiff_into_netcdf(gtiff_src, output_netcdf)
'''