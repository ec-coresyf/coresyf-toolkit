#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
===============================================================================
Co-ReSyF Research Application - SAR_Bathymetry
===============================================================================
 Authors: Alberto Azevedo and Francisco Sancho
 Date: June/2016
 Last update: March/2017
 
 Usage: ./SAR_Bathymetry_CoReSyF_V8.py <image input file> 
 
 For help: ./SAR_Bathymetry_CoReSyF_V8.py -h
===============================================================================
"""

import os,sys
wdir=os.getcwd()
paths=[wdir[:-6]+"bin"]
for i in paths:
	sys.path.append(i)

import numpy as np
import matplotlib.pyplot as plt
import cv2
import CSAR
import gdal
from scipy.interpolate import griddata
import matplotlib.colors as colors
from datetime import datetime
import argparse

def restricted_float(x):
    x = float(x)
    if x < 0.1 or x > 0.5:
        raise argparse.ArgumentTypeError("%r not in range [0.1, 0.5]"%(x,))
    return x

########## Input arguments 
parser = argparse.ArgumentParser(description='Co-ReSyF: Sar Bathymetry Research Application')
parser.add_argument('-i','--input', help='Input image',required=False)
parser.add_argument('-p','--polygon', help='Bathymetric AOI - Polygon coords list file',required=False)
parser.add_argument("-g", "--graphics", help="Show matplotlib plots while running the application",action="store_true")
parser.add_argument("-l", "--landmask", help="Apply Landmask",action="store_true")
parser.add_argument("-r", "--resDx", help="Resolution of the final bathymetric grid, in meters (m). Default=500m.", default=500., type=float,required=False)
parser.add_argument("-t", help="Period of the swell in deep waters, in seconds (s). Default=12s", default=12., type=float,required=False)
parser.add_argument("-s", help="FFT box shift parameter. Possible values between (0.1-0.5). Default=0.5.",default=0.5, type=restricted_float,required=False)
parser.add_argument("-v","--verbose", help="increase output verbosity",action="store_true")
args = parser.parse_args()
 

RunId=datetime.now().strftime('%Y%m%dT%H%M%S')
#RunId=datetime.now().strftime('%Y%m%dT%H%M')
PathOut="/home/riaa/Desktop/RA_SAR_Bathymetry/output/SAR_BathyOut_"+str(RunId)+"/"
#newpath = r'./'+PathOut
if not os.path.exists(PathOut):
	os.makedirs(PathOut)

Params=[ "\n#########################################################################################\n",
		 "\nCo-ReSyF: Sar Bathymetry Research Application\n",
		 "#########################################################################################\n",
		 "RunId : %s" % RunId +"\n",
		 "Input file: %s" % args.input +"\n",
		 "Polygon file: %s" % args.polygon +"\n",
		 "Graphics: %s" % args.graphics +"\n",
		 "Grid resolution: %s" % args.resDx+"\n",
		 "Period of the swell: %s" % args.t+"\n",
		 "FFT box shift parameter: %s" % args.s+"\n",
		 "Landmask: %s" % args.landmask+"\n",
		 "Verbosity: %s" % args.verbose+"\n",
		 "\n\n"]
paramsFile=PathOut+"Params_"+str(RunId)+".txt"
parOut=open(paramsFile,"w")
parOut.writelines(Params)
parOut.close()

if args.verbose:
	for i in Params:
		print i[:-1]

filein=args.input
Graphics=args.graphics
GridDx=args.resDx
Tmax=args.t
shift=args.s


# @TODO DELETE THIS AND CHANGE "-p" parameter required to false
filein= '/home/riaa/Desktop/RA_SAR_Bathymetry/input/Images/K5_20140919184413_000000_05912_D_WD02_HH_WTC_B_L1D/K5_Sesimbra_zoom.tif'
args.polygon= '/home/riaa/Desktop/RA_SAR_Bathymetry/input/Images/K5_20140919184413_000000_05912_D_WD02_HH_WTC_B_L1D/P_K5_Sesimbra_zoom.txt'
args.verbose=True
Tmax=13
GridDx=500


#### Hardcoded flags...
SFactor=1./1.
Slant_Flag=False
EPSG="WGS84"
#######################


#################################################################
#################################################################
### TO DO - Read EMODNET to define Tmax

#Tmax=12.## Swell com periodo de 15 segundos
Lmax=(9.8*(Tmax*Tmax))/(2*np.pi)
W2_deep=(2.*np.pi/(Tmax))*(2.*np.pi/(Tmax))
print "LMAX" , Lmax
#################################################################
#################################################################
#################################################################
#################################################################


if args.verbose:
	print "\n\nReading Image..."
img,mask,res, LMaskFile=CSAR.ReadSARImg(filein,ScaleFactor=np.float(SFactor),C_Stretch=True,SlantCorr=Slant_Flag,EPSG_flag=EPSG,Land=args.landmask, path=PathOut)

if args.verbose:
	print "\n\nReading Image... DONE!!!"

lon,lat=CSAR.GetLonLat(LMaskFile)

###
### Offset = # of pixels for half of 1 km FFT box. 
### Therefore, the Offset varies with image resolution. 
offset=CSAR.GetBoxDim(res[0])
if args.verbose:
	print "\nOffset (pixels,m):  (  %s  ;  %s  ) " % (offset,offset*res[0]) +"\n"

############################################################
###### Grid definition 
############################################################
############################################################
Pts=CSAR.SetGrid(LMaskFile,res,GridDeltaX = GridDx)
LonVec,LatVec=lon[0,:],lat[:,0]
Pontos=[]
for i in Pts:
	valx, lon_index=CSAR.find_nearest(LonVec,i[0])
	valy, lat_index=CSAR.find_nearest(LatVec,i[1])
	Pontos.append([lon_index,lat_index])
Pontos = np.array(Pontos)

if args.polygon==None:
	Polygon=CSAR.SetPolygon(LMaskFile,offset,PtsNum=10)
	np.savetxt("Polygon.txt",Polygon)
	os.system("cp -f Polygon.txt "+PathOut+".")
	for i in Polygon:
		print i
else:
	os.system("cp -f "+args.polygon+" "+PathOut+".")
	Polygon=np.loadtxt(args.polygon)
	print Polygon	

cnt=Polygon.reshape((-1,1,2)).astype(np.float32)

Pts2Keep=[]
for m,k in enumerate(Pts):
	Result=cv2.pointPolygonTest(cnt, (k[0],k[1]), False)
	if Result!=-1.0:
		Pts2Keep.append(m)
Pontos=Pontos[Pts2Keep]
#print Pontos_Final.shape


plt.figure()
plt.imshow(img,cmap="gray")
plt.scatter(Pontos[:,0],Pontos[:,1],3,marker='o',color='r')
plt.savefig(PathOut+"Grid.png", dpi=300)
if Graphics:
	plt.show()

if args.verbose:
	print "\n\n"
	print Pontos.shape
	print Pontos
	print "\n\n"


############################################################
############################################################
##########  FFT determination and plot  ####################
############################################################
directory=PathOut+"FFT_img_outputs/"
if not os.path.exists(directory):
	os.makedirs(directory)

if args.verbose:
		print "Creating the FFT image subsets for each grid point... "
for n,i in enumerate(Pontos):
	imgs,lons,lats=CSAR.GetFFTBoxes(i,img,lon,lat,offset,shift)
	for m,j in enumerate(imgs):
		FFTid=str(n+1)+"."+str(m+1)
		npzOut=directory+str(RunId)+"_FFT_"+FFTid+".npz"
		#print npzOut
		np.savez(npzOut, lons=lons[m], lats=lats[m], imgs=imgs[m])
		print len(lons[m])
if args.verbose:
		print "The FFT .npz files were successfully created !!! "



######### END HERE =============================================
# @TODO  Create here xml with metada for WINGS



######### START NEW SCRIPT HERE =============================================
# @TODO 

#################################################################
### Each npz file should be stored in a different virtual machine
#################################################################
#################################################################

###
### Assuming that the disk storage of the virtual machines is shared between machines, 
### a Depth_{RunId}.txt file is created to store the CdoDir averages from the 9 FFT Boxes made for each Bathymetry Grid Point.
### 
### If the storage is not shared, then the Depth inversion must be performed with all FileoutTXT Files gathered in a single machine
### 
###
DepthOut=directory+'Depth_'+str(RunId)+'.txt'
FDepthOut=open(DepthOut,"w")
for n,i in enumerate(Pontos):           #### @TODO TO BE parallelized. Processed only for each existing FFT_.npz files. REMOVE For cycle
	fileoutTXT= directory+str(RunId)+"_FFT_"+str(n+1)+".txt"
	fout=open(fileoutTXT,"w")
	for j in xrange(9):
		FFTid=str(n+1)+"."+str(j+1)
		if args.verbose:
			print "FFT ::",FFTid
		npzOut=fileoutTXT[:-4]+"."+str(j+1)+".npz"
		
		### In each virtual machine the sub-images are loaded again for the FFT function
		BoxFile = np.load(npzOut)

		################    FFT Boxes    
		CDO,DIR,mag,deltaX,deltaY,p2_plot,Kscale,RMask,CDO_array=CSAR.FFT_SAR(BoxFile['imgs'],BoxFile['lons'],BoxFile['lats'],fout,FFTid,Lmax,res=res,Tmax=Tmax)
		################    FFT Plots    
		CSAR.PlotSARFFT(BoxFile['imgs'],BoxFile['lons'],BoxFile['lats'],CDO,DIR,mag,deltaX,deltaY,p2_plot,Kscale,RMask,CDO_array,FFTid,CDOMax=Lmax,dir=directory)
	fout.close()

	################    Depth inversion    
	CdoDirData=np.loadtxt(fileoutTXT)
	CDO_mean=np.nanmean(CdoDirData[:,3])
	DIR_mean=np.nanmean(CdoDirData[:,4])
	Depth=CSAR.SAR_LinearDepth(CDO_mean,W2_deep,Lmax)
	FDepthOut.write(" %s   %s   %s   %s   %s   %s   " % (n+1,CdoDirData[0,1],CdoDirData[0,2],CDO_mean,DIR_mean,Depth)+"\n")
FDepthOut.close()


###########################################
########  Final DTM plot ################## 
CSAR.Plot_DTM(RunId,directory,graphics=Graphics)

if args.verbose:
	print "\n\n SAR Bathymetry DONE!!!"

