#-# MODULE IH_SAR
'''
Auxiliary functions to use in the wave tracking algorithm developed by IH.
------------------------------------------------------------------------------------
Python Requirements: os, numpy, scipy, matplotlib, netCDF4
------------------------------------------------------------------------------------
version: v.3  (Jun2018) 
------------------------------------------------------------------------------------
Created: Dez2017, Luisa Lamas luisa.lamas@hidrografico.pt
Updated: Jun2018, Luisa Lamas (v.3 to implement in Co-ReSyF platform)
------------------------------------------------------------------------------------

'''
# PYTHON MODULES
import numpy
import os
import netCDF4
import argparse
import ConfigParser

from math import radians, cos, sin, atan2, sqrt
from scipy.ndimage.filters import gaussian_filter
from scipy.interpolate import griddata
from scipy.integrate import simps
import matplotlib.mlab as mlab

def input_params():
	parser = argparse.ArgumentParser(description='Depth Extraction using Ray-Tracing Algorithm (IH)')
	# input parameters for depth extraction
	parser.add_argument('-i','--hi',help = 'starting depth for the tracking algorithm (meters)',default=100)
	parser.add_argument('-x','--Dxi',help = 'x-dimension of the subscene (meters)',default=1000)
	parser.add_argument('-y','--Dyi',help = 'y-dimension of the subscene (meters)',default=1000)
	parser.add_argument('-s','--hstop',help = 'stopping depth for the tracking algorithm (meters)',default=15)
	parser.add_argument('-p','--pts',help = 'Maximum tracking points for each track (number)',default=300)
	parser.add_argument('-d','--dm',help = 'distance between each track position (meters)',default=100)
	
	parser.add_argument('-b','--bat_file',help = 'initial bathymetry file (netcdf)',default='GEBCO_2014_2D.nc')
	parser.add_argument('-o','--outfilename',help='name for the final bathymetry (netcdf)',default='final_bathymetry.nc')
	
	args = parser.parse_args()
	
	return args

def get_bat(bat_file,lon,lat):
    '''
    function: [href] = get_bat(lon,lat)
    retrieves: bathymetry within the domain (lon,lat)

    INPUT:
		bat_file (GEBCO_2014_2d.nc)
        domain grid (lon,lat)

    OUTPUT:
        bathymetry in meters (href)

    ------------------------------------------------------------------------------------
    Python Requirements: numpy, netCDF4, os, matplotlib
    ------------------------------------------------------------------------------------
    version: v.2  (May2018) 
    ------------------------------------------------------------------------------------
    Created: Oct2017, Luisa Lamas luisa.lamas@hidrografico.pt
	Updated: May2018 (v.2)
    ------------------------------------------------------------------------------------
    '''

    minlat = min(lat)
    maxlat = max(lat)
    minlon = min(lon)
    maxlon = max(lon)

    # BATHYMETRY
    nc = netCDF4.Dataset(bat_file)
    lonb = nc.variables['lon'][:]
    latb = nc.variables['lat'][:]
    z = nc.variables['elevation'][:]
    nc.close()

    # CROPPING BATHYMETRY
    i = [index for index,la in enumerate(latb) if la <= maxlat+0.1 and la >= minlat-0.1]
    j = [index for index,lo in enumerate(lonb) if lo <= maxlon+0.1 and lo >= minlon-0.1]

    lonb = lonb[j]
    latb = latb[i]
    bat = z[i[0]:i[-1]+1,j[0]:j[-1]+1]

    bat[bat>0] = 0
    bat = bat*-1

    xb, yb = numpy.meshgrid(lonb, latb)
    
    # interpolate bathymetry to SAR grid
    href = mlab.griddata(xb.ravel(),yb.ravel(),bat.ravel(),lon,lat,interp='linear')

    return href

def get_initial(lon,lat,Dxi,Dyi,href,hi):
    '''
    Define starting positions for each track (x0,y0) according to the domain size and
    size of each averaging box.
    INPUT: 
        domain grid (lon,lat)
        box dimensions (Dxi, Dyi)
        reference bathymetry (href)
        initial depth (hi)
    
    OUTPUT:
        initial positions along hi (loni,lati)
        mean direction to shore (mean_dir)
				
    ------------------------------------------------------------------------------------
    Python Requirements: numpy

    ------------------------------------------------------------------------------------
    version: v.1  (Oct2017) 
    ------------------------------------------------------------------------------------
    Created: Oct2017, Luisa Lamas luisa.lamas@hidrografico.pt
    ------------------------------------------------------------------------------------
    '''

    dy = distance(lon[0],lon[0],lat[0],lat[-1])
    dx = distance(lon[0],lon[-1],lat[0],lat[0])

    Nlon = len(lon)
    Nlat = len(lat)

    # Grid mesh
    xa, ya = numpy.meshgrid(lon, lat)
    
    baty, batx = numpy.gradient(href)
    i, j = numpy.where(href < hi)
    batxm = numpy.mean(batx[i, j])
    batym = numpy.mean(baty[i, j])
    mean_dir = numpy.arctan2(batym,batxm)*180/numpy.pi + 180

    #---------------------------------------------------------------------------------
    # INITIAL TRACKING POSITIONS
    # Get initial tracking positions from domain size and size of each box (Dxi,Dyi)
    # Positions depend on mean direction to shore
    #---------------------------------------------------------------------------------

    if numpy.logical_or(numpy.logical_and(numpy.greater(mean_dir,45),
                                          numpy.less(mean_dir,135)),
                        numpy.logical_and(numpy.greater(mean_dir,225),
                                          numpy.less(mean_dir,315))):
        loni = numpy.zeros(Nlon)
        lati = numpy.zeros(Nlon)
        mdir = numpy.zeros(Nlon)
        
        for j in range(Nlon):
            i = numpy.abs(href[:,j]-hi).argmin()
            loni[j] = xa[i,j]
            lati[j] = ya[i,j]
            btxi = batx[i,j]
            btyi = baty[i,j]
            mdir[j] = numpy.arctan2(btyi,btxi)*180/numpy.pi + 180

        lsr = int(0.5*Dxi*(Nlon-1)/dx) # distance between points ~ box size
        
    else:
        loni = numpy.zeros(Nlat)
        lati = numpy.zeros(Nlat)
        mdir = numpy.zeros(Nlat) 
        for i in range(Nlat):
            j = numpy.abs(href[i,:]-hi).argmin()
            loni[i] = xa[i,j]
            lati[i] = ya[i,j]
            btxi = batx[i,j]
            btyi = baty[i,j]
            mdir[i] = numpy.arctan2(btyi,btxi)*180/numpy.pi + 180

        lsr = int(0.5*Dyi*(Nlat-1)/dy) # distance between points ~ box size

    # resampling initial offshore segment according to box size (Dxi,Dyi)
    loni = loni[::lsr] 
    lati = lati[::lsr]
    mdir = mdir[::lsr]

    return loni,lati,mdir

def get_subimage(x0,y0,lonm,latm,sigma,Dxi,Dyi):
    '''
    Get data inside a box of Dxi,Dyi dimensions,
    centred at x0,y0 (sub-image).
	
    INPUT: 
        Center position (x0,y0)
        Domain grid (latm,lonm) in meters
        Data (sigma) in (latm,lonm) dimensions
        Box width and height (Dxi,Dyi)
    OUTPUT:
	Grid resolution (dx,dy)
	Data inside the box (sig_box)
	
    ------------------------------------------------------------------------------------
    Python Requirements: numpy

    ------------------------------------------------------------------------------------
    version: v.1  (Nov2017) 
    ------------------------------------------------------------------------------------
    Created: Nov2017, Luisa Lamas luisa.lamas@hidrografico.pt
    ------------------------------------------------------------------------------------
    '''

    # grid resolution
    dx = abs(lonm[1]-lonm[0])   
    dy = abs(latm[1]-latm[0])

    # number of points inside the box
    px = int(Dxi/dx)
    py = int(Dyi/dy)
        
    # find center of the box in the grid (x0,y0)
    cla = numpy.abs(latm-y0).argmin()
    clo = numpy.abs(lonm-x0).argmin()

    # indices of box points ([-N:...:N] where N is half the box size)
    i = numpy.arange(cla-py/2,cla+py/2+1)
    j = numpy.arange(clo-px/2,clo+px/2+1)

    # Sigma inside the box
    sig_box = sigma[i[0]:i[-1]+1,j[0]:j[-1]+1]

    return dx,dy,sig_box

def wave_params(dx,dy,sig_box,mean_dir):
    '''
    returns: Wave parameters from FFT of SAR image

    The function computes the fast fourier transform over a box of Dxi x Dyi dimensions.
    The result is in Sf(k,theta) dimensions.
    The quadrant is chosen based on mean direction from shore retrieved from
    bathymetry gradient.
    The wave parameters are retrieved using the mean spectrum integrated using
    Simpson Rule.
      
    INPUT:
        image resolution (dx,dy)
        sigma from subimage (sig_box)
        mean direction to shore (mean_dir)

    OUTPUT:
        Peak Wave direction (tp)
        Mean Wave number (km)
        
    ------------------------------------------------------------------------------------
    version: v.7  (May2018)
    ------------------------------------------------------------------------------------
    Created: Oct2016, Luisa Lamas luisa.lamas@hidrografico.pt
    Updated: Mar2017, Jose Paulo paulo.pinto@hidrografico.pt (v.2)
    Updated: May2018, Luisa Lamas (v.7)
    ------------------------------------------------------------------------------------
    '''
    
	#-----------------------------------------------------------------------------
    # FAST FOURIER TRANSFORM
    #-----------------------------------------------------------------------------

    # Grid
    rows,cols = sig_box.shape
    sig_box = sig_box - numpy.nanmean(sig_box)

    # Use TAPER algorithm to minimize weight in borders
    sig_hann = taper(sig_box,cols,rows)
    sig = sig_hann - numpy.nanmean(sig_hann) 
        
    # Fast Fourier transform
    S = numpy.fft.fft2(sig)
    S = numpy.fft.fftshift(S)
    S = S*numpy.conjugate(S)

    if numpy.isnan(S).all(): #bad FFT
        tp=km=numpy.NaN
    else:

        # CLEAN SPECTRUM
        # Gaussian smoothing of S (remove some noise)
        Sf = gaussian_filter(numpy.real(S), 0.9)

        #-----------------------------------------------------------------------------
        # WAVE PARAMETERS
        #-----------------------------------------------------------------------------

        # wavenumber grid
        # 2D Grid
        wx,wy = numpy.meshgrid(numpy.arange(0,cols),numpy.arange(0,rows))  
        kx = wx-numpy.max(wx)/2.
        ky = wy-numpy.max(wy)/2.

        kx = 2*numpy.pi*kx/dx/cols
        ky = 2*numpy.pi*ky/dy/rows

        kl = numpy.sqrt(kx**2+ky**2) # norm
        kl[kl==0] = 0.0001

        kxn = kx/kl
        kyn = ky/kl

        # filter spectrum values based on critical wavelength (50-400m)
        F = kx**2 + ky**2
        mask = numpy.logical_and(numpy.less_equal(F,0.03),
                     numpy.greater_equal(F,0.0005))

        Sf = numpy.real(Sf*mask)
            
        # Normalization of Sf
        Sn = Sf/simps(simps(Sf))
        Sn_max = numpy.nanmax(Sn) 

        # Find Quadrant based on mean direction to shore
        # Find peak value --> Sn > 80%
        if mean_dir <= 90 or mean_dir > 270:
            ii, jj = numpy.where(numpy.logical_and(numpy.greater_equal(kx,0),numpy.greater(Sn,Sn_max*0.8)))
            
        else:
            ii, jj = numpy.where(numpy.logical_and(numpy.less_equal(kx,0),numpy.greater(Sn,Sn_max*0.8)))

        # Peak wave direction
        kcos = numpy.nanmean(kxn[ii,jj])
        ksin = numpy.nanmean(kyn[ii,jj])
        tp = numpy.arctan2(ksin,kcos)*180/numpy.pi

        if tp < 0:
            tp = tp + 360
        else:
            tp = tp

        #-----------------------------------------------------------------------------
        # MEAN WAVE PARAMETERS
        # Compute Mean with Spectrum Integration (Simpsons Rule)
        #-----------------------------------------------------------------------------

		km = simps(simps(Sn*kl))/simps(simps(Sn))

    return tp,km

def distance(lon1,lon2,lat1,lat2):
    '''
    distance between two points (lat/lon decimal)
    based on haversine formula:
    formula to calculate the great-circle distance between two points
    [the shortest distance over the earths surface]
    '''

    R = 6371000  # Earths radius in metres
    #convert lat/lon to radians
    latitude1 = radians(lat1)
    latitude2 = radians(lat2)
    dlatitude = radians(lat2-lat1)
    dlongitude = radians(lon2-lon1)

    a = sin(dlatitude/2)**2 + cos(latitude1)*cos(latitude2)*sin(dlongitude/2)**2
    c = 2*atan2(sqrt(a),sqrt(1-a))
    d = R*c

    return d
	
def deg2meters(lon,lat):
    '''
    retrieves grid in distance (meters) from source (lon[0],lat[0])
    '''
    
    Nlat = len(lat)
    Nlon = len(lon)

    # total domain size in meters ----------------------------------------
    DY = distance(lon[0],lon[0],lat[0],lat[-1])
    DX = distance(lon[0],lon[-1],lat[0],lat[0])

    if lat[0] > lat[-1]:
        latm = numpy.arange(DY,0,-DY/Nlat)  #descending orbit
    else:
        latm = numpy.arange(0,DY,DY/Nlat)   #ascending orbit

    if lon[0] > lon[-1]:
        lonm = numpy.arange(DX,0,-DX/Nlon)
    else:        
        lonm = numpy.arange(0,DX,DX/Nlon)

    return lonm,latm
	
def taper(F,M,N):
    '''
    Taper algorithm to reduce weight in borders of
    MxN matrix
    M,N - Matrix dimensions
    F - Matrix with dims (M,N)

    --------------------------------------------
    Python requires numpy
	--------------------------------------------
	--------------------------------------------
    
    '''
    
    dx = numpy.arange(0,M)
    dy = numpy.arange(0,N)
    cx = M/2. # center
    cy = N/2. 
    
    # 2D Grid
    wx,wy = numpy.meshgrid(dx,dy)  #2D box

    # Gaussian function
    Ax = ((wx-cx)**2)/(0.5*M**2)
    Ay = ((wy-cy)**2)/(0.5*N**2)
    hann = numpy.exp(-(Ax+Ay)) # Gaussian window

    Fh = F*hann

    return Fh

def bathymetry_save(outfilename,lonp,latp,hp):
    """
    Save final result as netcdf file
    bathymetry in each tracking point - (lonp,latp,hp)

    ------------------------------------------------------------------------------------
    version: v.2  (May2018) 
    ------------------------------------------------------------------------------------
    Created: Fev2018 Luisa Lamas luisa.lamas@hidrografico.pt
	Updated: May2018 Luisa Lamas (v.2)
    ------------------------------------------------------------------------------------
    ------------------------------------------------------------------------------------
    """
    
    tracks, positions = hp.shape
   
    rootgrp = netCDF4.Dataset(outfilename, 'w', clobber=True)

    # Create dimensions, variables and attributes:
    ncdim_tracks = rootgrp.createDimension('tracks', tracks)
    ncdim_positions = rootgrp.createDimension('positions', positions)

    #DEPTH ALONG TRACK and POSITIONS
    nc_lat = rootgrp.createVariable('lat', 'f4', ('tracks','positions'),fill_value=-9999)
    nc_lat.long_name = 'latitude'
    nc_lat.units = 'degrees_north'
    nc_lat[:] = latp

    nc_lon = rootgrp.createVariable('lon', 'f4', ('tracks','positions'),fill_value=-9999)
    nc_lon.long_name = 'longitude'
    nc_lon.units = 'degrees_east'
    nc_lon[:] = lonp

    # Data
    nc_depth = rootgrp.createVariable('depth', 'f4', ('tracks','positions'),fill_value=-9999)
    nc_depth.long_name = 'depth'
    nc_depth[:] = hp

    rootgrp.close()

    return
