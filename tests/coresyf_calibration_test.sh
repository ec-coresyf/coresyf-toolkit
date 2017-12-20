#/bin/bash 

source `dirname $0`/helpers.sh

#INFILE=$1

if [ -z "$INFILE" ]; then
	echo 'An input file should be passed as parameter'
	exit 1
fi


if [ ! -f $INFILE ]; then
	echo 'Input file not found'
	exit 1
fi

export _JAVA_OPTIONS="-Xmx4g"

#Nominal cases:

src/coresyf_calibration.py --Ssource $INFILE.SAFE  --Ttarget out
test -f out
check "target specified"
rm -f out

src/coresyf_calibration.py --Ssource $INFILE.SAFE --Ttarget out --PauxFile 'Latest Auxiliary File' --PcreateBetaBand true --PcreateGammaBand true --PoutputBetaBand true --PoutputGammaBand true --PoutputImageInComplex true --PoutputImageScaleInDb true --PoutputSigmaBand true
test -f out
check "all parameters"
rm -f out

#Error cases:
src/coresyf_calibration.py --Ssource $INFILE.SAFE --Ttarget out --PauxFile 'Latest Auxiliary File' --PcreateBetaBand true --PcreateGammaBand true --PoutputBetaBand true --PoutputGammaBand true --PoutputImageInComplex true --PoutputImageScaleInDb true --PoutputSigmaBand true --PsourceBands 'HH'
test $? -ne 0
check "invalid band"
rm -f out

src/coresyf_calibration.py --Ssource $INFILE.SAFE
test $? -ne 0
check "target missing"
rm -f target.dim.tif


src/coresyf_calibration.py
test $? -ne 0
check "source missing"


src/coresyf_calibration.py --Ssource "prod.tif" 
test $? -ne 0
check "missing file"

src/coresyf_calibration.py --Ssource $INFILE.SAFE --PauxFile 'prodxpto'
test $? -ne 0
check "source missing"
