#/bin/bash 

source ./helpers.sh

cd ..

#gets the test file 
if [ ! -d Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC ]; then
	wget ftp://rsat2:yvr578MM@ftp.mda.ca/Vancouver%20Dataset/Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC.zip 
	unzip Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC.zip
	mv RS2_OK871_PK6633_DK3208_FQ2_20080415_143805_HH_VV_HV_VH_SLC Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC
fi

#Nominal cases:

src/coresyf_calibration.py --Ssource Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC/product.xml
test -f target.dim.tif
check "source file" 
rm -f target.dim.tif

src/coresyf_calibration.py --Ssource Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC/product.xml --Ttarget out
test -f out.tif
check "target specified"
rm -f out.tif

src/coresyf_calibration.py --Ssource Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC/product.xml --Ttarget out --PauxFile 'Latest Auxiliary File' --PcreateBetaBand true --PcreateGammaBand true --PoutputBetaBand true --PoutputGammaBand true --PoutputImageInComplex true --PoutputImageScaleInDb true --PoutputSigmaBand true --PsourceBands 'i_HH,q_HV,i_VH,q_VH' --PselectedPolarisations 'HH,HV'
test -f out.tif
check "all parameters"
rm -f out.tif

#Error cases:
src/coresyf_calibration.py
test $? -ne 0
check "source missing"


src/coresyf_calibration.py --Ssource "prod.tif" 
test $? -ne 0
check "missing file"

src/coresyf_calibration.py --Ssource Vancouver_RS2_FineQuad2_HH_VV_HV_VH_SLC/product.xml --PauxFile 'prodxpto'
test $? -ne 0
check "source missing"
