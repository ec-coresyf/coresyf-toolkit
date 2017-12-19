#!/bin/bash

#computation time
startglobal=$(date +%s.%N)
#

echo "---------------------------------------------------------------"
echo "	SAR image Processing and bathymetry estimation	"
echo "---------------------------------------------------------------"
echo ""
echo ""



#***********************
# 1) Tiling
#***********************
python SAR_Tiling.py -a Config_Image.ini -i Aveiro.tif -b bathymetry.npz -p contrast slant -r 4326 32629 -d 2000 -w 9 -s 0.5 -T 16.6 -v

##*****************************************
## 2) Spectra estimate (parallel)
##*****************************************

fun1 () {
	local filename=$1
	fname=$(echo $filename| cut -d'/' -f 4)
	python SAR_Spectrum.py -i $fname -a Config_Spectrum.ini -c 290 -m 'Radial' -p 5 -d 100 -v
}
##for filename in subset0*.out; do fun1 "$filename" & done 
for filename in sub*.out; do fun1 "$filename" & done 
wait


##*****************************************************************
## 3) Point Subdivision (Deep/shallow water vs computation points)
##*****************************************************************
python SAR_GridPoints_Subdivision.py -a Config_Inversion.ini -l 0 -T 16.6 -m direct -w linear -v


##*****************************************
## 4) Depth Inversion (parallel)
##*****************************************
### Reference points (to be added later)
## global grid points

fun2 () {
	local filename=$1
	fname=$(echo $filename| cut -d'/' -f 4)
	python SAR_Inversion.py -i $fname -v
}

if [ -f ComputationPoints0.out ]
##if [ -f Output/TEMP/Inversion/Computation0.out ]
then
	for filename in Computation*.out; do fun2 "$filename" & done
	wait
fi

##*****************************************
## 5) Post-Processing
##*****************************************
##merge all information for post-processing
python SAR_Postprocessing.py


