# Description of SAR_Tiling processing steps: 

* Retrieves input parameters [at "SAR_Tiling.py" line 27]
  * Gets EPSG_in and ESPG_out from input image and grid, respectively [at "CSAR_ImageProcessing.py" line 101]

* Reads SAR image [at "SAR_Tiling.py" line 49]
  * Performs slant range correction (at "CSAR_ImageProcessing.py" line 169)
  * DOES NOT run "scale image", only if ScaleFactor is not equal to 1, which is hardcoded to be always =1 (at "CSAR_ImageProcessing.py" line 173)
  * Projects Image to EPSG_out (grid projection) using gdalwarp (at "CSAR_ImageProcessing.py" line 192).
  * Gets Bbox coordinates and pixel resolution from projected image (at "CSAR_ImageProcessing.py" line 207).
  * Stretch image contrast: image histogram equalization (at "CSAR_ImageProcessing.py" line 223).
  * DOES NOT create land mask and set all land regions on image equal to 0 (at "CSAR_ImageProcessing.py" line 230), only if LandMaskFlag is true (whihc is hardcoded to be always false).

* Reads Grid points [at "SAR_Tiling.py" line 72]
  * Finds image pixel that corresponds to the grid point
  * stores list of image pixels or points.

* Calculates the subset dimensions [at "SAR_Tiling.py" line 88]:
  * Dimension in pixels is calculated using input parameter "dimension" (default=2000), in meters, and input image resolution.[at CSAR_Subsets.py line 30]
* Calculates the FFT boxes to estimate spectrum at a given grid point [at "SAR_Tiling.py" line 120]
* Creates files with grid point subsets data [at "SAR_Tiling.py" line 123]
