#!/usr/bin/python2.7
# -*- coding: utf-8 -*-


import numpy as np
import matplotlib.pyplot as plt
import cv2
import CSAR
import gdal
from scipy.interpolate import griddata
import matplotlib.colors as colors
from datetime import datetime
import argparse
import tarfile
import os, re
import ConfigParser


########## Input arguments
parser = argparse.ArgumentParser(description='Co-ReSyF: Sar Bathymetry Research Application')
parser.add_argument('-i', '--input', help='Input file (tar.gz) with .npz files for FFT determination', required=True)
parser.add_argument('-o', '--output', help='Output text file', required=True)
parser.add_argument("-g", "--graphics", help="Show matplotlib plots while running the application", action="store_true")
parser.add_argument("-t", help="Period of the swell in deep waters, in seconds (s). Default=12s", default=12., type=float, required=False)
parser.add_argument("-v","--verbose", help="increase output verbosity",action="store_true")
parser.add_argument('-a', '--param', help='Parameters file (.ini file)', required=True)
args = parser.parse_args()

########### @TODO
# Reading ini file with parameters
ConfigF = ConfigParser.ConfigParser()
ConfigF.read(args.param)

resStr = ConfigF.get("Run", "res")
resList = resStr.split(',')
res = [float(elem) for elem in resList]

print res
#res= [6.39, 6.39]

Tmax=args.t
fileout = args.output
npz_tar_file = args.input

#################################################################
### TO DO - Read EMODNET to define Tmax

#Tmax=12.## Swell com periodo de 15 segundos
Lmax=(9.8*(Tmax*Tmax))/(2*np.pi)
W2_deep=(2.*np.pi/(Tmax))*(2.*np.pi/(Tmax))
print "LMAX" , Lmax


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

# npz_tar_file = "../FFT_img_outputs20170609T145631_FFT_7.tar.gz"
npz_tar_file_basename = os.path.basename (npz_tar_file)
RunId = re.search(r'\d{8}T\d{6}', npz_tar_file_basename).group()
PointId = re.findall(r"FFT_(\d+)", npz_tar_file_basename)[0]

DepthOut = fileout  #+ 'Depth_' + str(RunId) + '_' + PointId + '.txt'
FDepthOut = open(DepthOut,"w")

# Saving fileoutTXT in current working directory (temporary file)
curdir = os.getcwd()
fileoutTXT = curdir + '/' + str(RunId) + "_FFT_" + PointId + ".txt"
fout = open(fileoutTXT,"w")

tar = tarfile.open(npz_tar_file)

j=0
for member in tar.getmembers(): #for j in xrange(9):
	f=tar.extractfile(member)
	BoxFile = np.load(f)

	if args.verbose:
		print "FFT_" + RunId + "_" + str(j+1)

	FFTid = PointId + "." + str(j+1)
	#npzOut=fileoutTXT[:-4]+"."+str(j+1)+".npz"
	
	### In each virtual machine the sub-images are loaded again for the FFT function
	#BoxFile = np.load(npzOut)

	################    FFT Boxes    
	CDO,DIR,mag,deltaX,deltaY,p2_plot,Kscale,RMask,CDO_array=CSAR.FFT_SAR(BoxFile['imgs'],BoxFile['lons'],BoxFile['lats'],fout,FFTid,Lmax,res=res,Tmax=Tmax)
	################    FFT Plots    
	CSAR.PlotSARFFT(BoxFile['imgs'],BoxFile['lons'],BoxFile['lats'],CDO,DIR,mag,deltaX,deltaY,p2_plot,Kscale,RMask,CDO_array,FFTid,CDOMax=Lmax,dir=fileout)
	j+=1
fout.close()
tar.close()

################    Depth inversion    
CdoDirData=np.loadtxt(fileoutTXT)
CDO_mean=np.nanmean(CdoDirData[:,3])
DIR_mean=np.nanmean(CdoDirData[:,4])
Depth=CSAR.SAR_LinearDepth(CDO_mean,W2_deep,Lmax)
FDepthOut.write(" %s   %s   %s   %s   %s   %s   " % (PointId, CdoDirData[0,1],CdoDirData[0,2],CDO_mean,DIR_mean,Depth)+"\n")
FDepthOut.close()





'''
########################### NEXT SCRIPT ############################

###########################################
########  Final DTM plot ################## 
CSAR.Plot_DTM(RunId,fileout,graphics=Graphics)

if args.verbose:
    print "\n\n SAR Bathymetry DONE!!!"
'''