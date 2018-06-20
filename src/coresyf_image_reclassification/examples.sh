LandUseLandCover_LANDSAT7_LULC_2013_Sep_04.tif="http://example.org"
LandUseLandCover_LANDSAT7_LULC_2014_Sep_07.tif="http://example.org"
#PASSING EXECUTION
#Example of a passing execution
./run --Ssource test_data/LandUseLandCover_LANDSAT7_LULC_2013_Sep_04.tif --Sclass test_data/reclass.txt --Ttarget myoutput1.tif
#PASSING EXECUTION2
#Example of a passing execution using a different input image.
./run --Ssource test_data/LandUseLandCover_LANDSAT7_LULC_2014_Sep_07.tif --Sclass test_data/reclass.txt --Ttarget myoutput2.tif