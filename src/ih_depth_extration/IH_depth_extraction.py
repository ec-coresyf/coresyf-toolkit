'''
RAY TRACING ALGORITHM

Bathymetry derivation using SAR images.
The image is divided into tracks, each track contains the depth at each
position, retrieved from SAR image, using FFT (averaged over a squared 
sub-image centered at each position) and depth computed 
from mean wavelength, based on the dispersion relation.

Starting positions (x0,y0) are defined according to the domain size and
size of each averaging box.
The next position is defined by displacement of dm on the wave direction of the
previous box.

Finally, for each position the depth is calculated based on the dispersion
relation:
        h = atanh(sg/km)/km
Where km is the mean wave number and sg = s^2/g
(s = frequency, g = gravitational acceleration)

INPUTS:
        Image (lon,lat,sigma0)
        Starting depth (hi)
        Box size for each tracking point in m, (Dxi, Dyi) 
		Bathymetry file (reference: GEBCO)
		Maximum Points for each track (default: 300)
		Displacement between tracking positions (default: 100)
		Stopping depth (hstop)

OUTPUTS:
        positions of each tracking point (lonp,latp)
        depth of each tracking point (hp)

------------------------------------------------------------------------------------ 
Python Requirements: numpy
Modules: IH_SAR
------------------------------------------------------------------------------------
version: v.6 (Jun2018)
------------------------------------------------------------------------------------
Created: Nov2016, Luisa Lamas luisa.lamas@hidrografico.pt
Updated: Mar2017, Jose Paulo paulo.pinto@hidrografico.pt (v.3)
Updated: Jun2018, Luisa Lamas (v.6 - to implement on Co-ReSyF platform)
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
'''
import numpy

#-# specific modules
import IH_SAR

# -------------------------------------------------------------------------------- 

#---------------------------------------------------------------------------------
# 1.
# Get SAR Image Data
# FROM PLATFORM: 
# needs: lon(vector), lat(vector), sigma(matrix[lat,lon]) 

# 2.
# Input params: initial depth(hi), Box size (in m) for tracking (Dxi,Dyi)
# maximum tracking points (pts), displacement between tracks (dm) and 
# limit shallow water depth (hstop) 
args = IH_SAR.input_params()

Dxi = args.Dxi
Dyi = args.Dyi
dm = args.dm
hi = args.hi 
hstop = args.hstop
pts = args.pts

# input bathymetry file
bat_file = args.bat_file

# name for the final file (.nc)
outfilename = args.outfilename

#---------------------------------------------------------------------------------
# 3.
# Get Reference Bathymetry
href = IH_SAR.get_bat(bat_file,lon,lat)

#---------------------------------------------------------------------------------
# 4.
# Define initial positions based on initial depth and mean direction to shore
[loni,lati,mdir] = IH_SAR.get_initial(lon,lat,Dxi,Dyi,href,hi)

#---------------------------------------------------------------------------------
# 5.
# Convert lon, lat to meters (distance from 0,0) 
[lonm,latm] = IH_SAR.deg2meters(lon,lat)

#---------------------------------------------------------------------------------
# 6.
# Ray Tracing Algorithm
# --------------------------------------------------------------------------------
# number of tracks
tracks = len(loni)

# VARIABLES
# depth and corresponding positions along track
lonp = numpy.zeros((tracks,pts))
lonp[:] = numpy.NaN
latp = numpy.zeros((tracks,pts))
latp[:] = numpy.NaN
hp = numpy.zeros((tracks,pts))
hp[:] = numpy.NaN   

# START TRACKING
for it in range(tracks):

    lon0 = loni[it]
    lat0 = lati[it]
    mdir0 = mdir[it]

    # initial tracking positions and depth
	n = 0
    lonp[it,n] = lon0
    latp[it,n] = lat0
    hp[it,n] = hi
    
	# find nearest point
    i = numpy.argmin([abs(lat0-las) for las in lat])
    j = numpy.argmin([abs(lon0-los) for los in lon])
    
    h0 = hi
    
    while href[i,j]>=hstop:
                    
        x0 = lonm[j]    
        y0 = latm[i]
        
        # check if box is inside domain
        if (y0-Dyi/2. <= min(latm) or y0+Dyi/2. >= max(latm) or
            x0-Dxi/2. <= min(lonm) or x0+Dxi/2. >= max(lonm)):
            break
        else: # Retrieve wave parameters
            [dx,dy,sig_box] = IH_SAR.get_subimage(x0,y0,lonm,latm,sigma,Dxi,Dyi)
            
            if numpy.isnan(sig_box).all(): # Bad FFT
                break
            else:
                if lat[0]>lat[1]: #descending or ascending orbit
                    sig_box = numpy.flipud(sig_box)
                
                [tp,km] = IH_SAR.wave_params(dx,dy,sig_box,mdir0,sflag)

                if numpy.isnan(numpy.sum([tp,km])): # no retrieved values
                    break  #to next track   
                else:

                    if n==0: # Mean Frequency for first box considering k = 2pi/2D (sg^2/g)
                       sg = km*numpy.tanh(km*h0)
                       h = h0
                    else:

                        # compute depth from sg of previous box 
                        if sg < km:
                            h = numpy.arctanh(sg/km)/km # depth 
                        else:
                            h = h0
##
                        #do not allow more than 30% error from reference depth
                        if numpy.abs(h-href[i,j]) > 0.3*href[i,j]:
                            h = href[i,j]
                        else:
                            h = h
                    
                        sg = km*numpy.tanh(km*h)
 
                    # DISPLACEMENT
                    
                    x = x0+dm*numpy.cos(tp*numpy.pi/180.) # next box x position
                    y = y0+dm*numpy.sin(tp*numpy.pi/180.) # next box x position
					
					# find nearest
                    i = numpy.argmin([abs(y-las) for las in latm])
                    j = numpy.argmin([abs(x-los) for los in lonm])
                            
                    x0 = x
                    y0 = y

                    hp[it,n] = h
                    latp[it,n] = lat[i]
                    lonp[it,n] = lon[j]

                    h0 = h

                    n = n+1
                    if n == pts:
                        break # END TRACK

#---------------------------------------------------------------------------------
# 7.
# Save Final Bathymetry 
#
IH_SAR.bathymetry_save(outfilename,lonp,latp,hp)

#-#  DONE
