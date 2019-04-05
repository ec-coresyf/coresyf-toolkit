# Unit tests
# Runs unit tests in tests/ and reports result
pytest -v

# Runs IR-MAD Releative Radiometric Normalization
# using tests/data/reference.img as reference image
# using tests/data/target.img as target image
# using all 4 bands in both images
# corrected image written as demo/cal_target.tif
# pseudo invariant features as demo/pif_reference.tif
# statistics written into intercal.log
# all output files overwritten if commanbd re-run
./intercal.py -w demo -r tests/data/reference.img -i tests/data/target.img -b 1 2 3 4
