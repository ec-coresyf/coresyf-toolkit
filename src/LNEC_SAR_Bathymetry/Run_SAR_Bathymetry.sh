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
SAR_Tiling/run -a Config_Image.ini -i test_data/Aveiro_20170131T183449_20170131T183514_004096_007148_CDB9_Sigma0_VV_processed.tif -b test_data/grid_EPSG_3763.zip -p contrast slant -d 2000 -w 9 -s 0.5 -T 16.6 -v

##*****************************************
## 2) Spectra estimate (parallel)
##*****************************************

fun1 () {
	local filename=$1
	fname=$(echo $filename| cut -d'/' -f 4)
	SAR_Spectrum/run -i $fname -a Config_Spectrum.ini -c 290 -m 'Radial' -p 5 -d 100 -v
}
##for filename in subset0*.out; do fun1 "$filename" & done 
for filename in sub*.out; do fun1 "$filename" & done
wait


##*****************************************************************
## 3) Point Subdivision (Deep/shallow water vs computation points)
##*****************************************************************
fun3 () {
	local filename=$1
	fname=$(echo $filename| cut -d'/' -f 4)
	SAR_GridPoints_Subdivision/run -i $fname -a Config_Inversion.ini -l 0 -T 16.6 -m direct -w linear -o ${fname}.sub  -v
}
for filename in Spectrum*.out; do fun3 "$filename" & done
wait


##*****************************************
## 4) Depth Inversion (parallel)
##*****************************************
### Reference points (to be added later)
## global grid points

fun2 () {
	local filename=$1
	fname=$(echo $filename| cut -d'/' -f 4)
	SAR_Inversion/run -i $fname -o ${fname}.inv -v
}

#if [ -f ComputationPoints0.out ]
##if [ -f Output/TEMP/Inversion/Computation0.out ]
#then
for filename in Spectrum*.sub; do fun2 "$filename" & done
wait
#fi

##*****************************************
## 5) Post-Processing
##*****************************************
##merge all information for post-processing
dirlist=`ls Spectrum*.inv`
SAR_Postprocessing/run -i $dirlist -o final_data.txt -v


