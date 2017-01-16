 =============================
|   CORESYF TOOLKIT v.0.1     |
 =============================
Command line image processing tools, developped for the first version of the 
Co-ReSyf platform.

coresyf_toolkit
         ├── src         -> contains the scripts of all tools
         └── examples    -> folder where the example data files are stored


 -----------------------------
|      PYTHON VERSIONS        |
 -----------------------------
CORESYF TOOLKIT works with Python 2.6-2.7


 -----------------------------
|        INSTALLATION         |
 -----------------------------
TBC


 -----------------------------
|            USAGE            |
 -----------------------------
TBC


 -----------------------------
|      TOOLS DESCRITPION      |
 -----------------------------
These tools (coming from the requirements assessed for the different Research
Applications) will be deployable in the cloud back-end through either calls from
the Workflow Manager or the Developer’s Sandbox. 

--> Radiometric Correction: an image pre-processing module to perform
radiometric correction of both optical and SAR imagery.

--> Optimal Interpolation: an image processing module to support the
implementation of optimal interpolation methods to obtain gridded maps from
point measurements.

--> Image crop: an image processing module to support the possibility of cropping
an image for a specific AOI.

--> Image mask: an image processing module to support the masking of raster
imagery using either other raster imagery r vector files (e.g. , shapefiles)

--> SAR Speckle filtering: an image pre-processing module for SAR imagery to
remove the speckle effect.

--> Image statistics: an image processing module to support the calculation of
general image values statistics.

--> Geo-referencing: an image processing module to support the geo-referencing
of optical and SAR satellite imagery

--> Error metrics: an image processing module to support the calculation of
different error metrics

--> Vector creation and edition: an image processing module to support the
creation and edition of different vector file formats

--> Layer stack creation: an image processing module to support the ability to stack
images into one multi-layer file sorted in the order in which they are inserted by
the user or by any other user specific parameter (e.g. time)


 -----------------------------
|       CHANGE LOG            |
 -----------------------------
* V0.1: January 16, 2017: first release:
   -> ADDED: Image Crop, Image Mask, Image Splitting, Image Stacking and Points-to-
     -Grid tools.




