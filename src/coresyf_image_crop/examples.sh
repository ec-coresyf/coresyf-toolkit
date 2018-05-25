Aveiro_resampled.tif="http://example.org"
#PASSING EXECUTION
#Example of a passing execution
./run --Ssource tests/test_data/Aveiro_resampled.tif --Pbuffer 5 --Sgrid tests/test_data/grid_EPSG_3763 --Ttarget myoutput1.tif
#PASSING EXECUTION2
#Example of a passing execution. Here the buffer is provided in meters.
./run --Ssource tests/test_data/Aveiro_resampled.tif --Pbuffer 1000 --PbufferUnits meters --Sgrid tests/test_data/grid_EPSG_3763 --Ttarget myoutput2.tif



