
# CORESYF TOOLKIT v.0.1

## Introduction

Command line image processing tools, developped for the first version of the 
Co-ReSyf platform.

    coresyf_toolkit
    ├── src         -> contains the scripts of all tools
    └── examples    -> folder where the example data files are stored


## Python Versions
CORESYF TOOLKIT works with Python 2.6-2.7


## Installation
No need to install anything. Just run docker (see usage for examples).

## Usage
### Build image (mandatory)
If the image is not yet built, run the command: 

`docker-compose build`.

This will create an image with the tag `repo.coresyf.eu/toolkit:latest`.

### Test all tools (not implemented yet)
This will find all `tests.py` scripts with unittest module and test the tools:

`docker-compose run test`.

### Test tool by tool
To test `docker-compose up <tool_name>`. Tool name can be one of the following:
* **calibration**: coresyf_calibration
* **crop**: coresyf_image_crop
* **mask**: coresyf_image_mask
* **spliting**: coresyf_image_splitting
* **stacking**: coresyf_image_stacking
* **isodata**: coresyf_isodata_classification
* **pt2grid**: coresyf_pointsToGrid
* **polygon2polyline**: coresyf_PolygonToPolyline
* **polyline2raster**: coresyf_PolylineToRaster
* **randraster**: coresyf_randRasterGen
* **raster2polygon**: coresyf_RasterToPolygon
* **sarfile**: coresyf_sar_fileSelector
* **speckle**: coresyf_speckle_fileter
* **vector**: coresyf_vector_creator

**NOTE**: Image crop is the only tool implemented, and it is not working (needs solving).

### Manual testing

It's possible to test the tools without running any of the predefined commands and options. To do so, invoke the tool with the following command: 

`docker container run repo.coresyf.eu/toolkit <tool_script>.py`

### Where is the data?
The Dockerfile/docker-compose files are configured to place scripts and examples inside the docker container in the following directories:
* **src**: `/opt/toolkit/src`
* **examples**: `/opt/toolkit/examples`

Note that, while source code is mounted as a volume _and_ copied inside the container, the examples folder is solely mounted as a volume.
Also, be aware that the default woking dir of the container is `/opt/toolkit/src`, so there is no need to specify a path to the python script.

### Adding requirements
To add a new python package requirement, simply add it to the `requirements.txt` file and rebuild the image.

## Tools description
These tools (coming from the requirements assessed for the different Research
Applications) will be deployable in the cloud back-end through either calls from
the Workflow Manager or the Developer’s Sandbox. 

* **Radiometric Correction**: an image pre-processing module to perform
radiometric correction of both optical and SAR imagery.

* **Optimal Interpolation**: an image processing module to support the
implementation of optimal interpolation methods to obtain gridded maps from
point measurements.

* **Image crop**: an image processing module to support the possibility of cropping
an image for a specific AOI.

* **Image mask**: an image processing module to support the masking of raster
imagery using either other raster imagery r vector files (e.g. , shapefiles)

* **SAR Speckle filtering**: an image pre-processing module for SAR imagery to
remove the speckle effect.

* **Image statistics**: an image processing module to support the calculation of
general image values statistics.

* **Geo-referencing**: an image processing module to support the geo-referencing
of optical and SAR satellite imagery

* **Error metrics**: an image processing module to support the calculation of
different error metrics

* **Vector creation and edition**: an image processing module to support the
creation and edition of different vector file formats

* **Layer stack creation**: an image processing module to support the ability to stack
images into one multi-layer file sorted in the order in which they are inserted by
the user or by any other user specific parameter (e.g. time)

## Tools Usage
### **Radiometric Correction**
It uses the command line based Graph Processing Tool (GPT) to perform radiometric
calibration of mission products. The input must be the whole product (use either
the 'manifest.safe' or the whole product in a zip file as input).

#### Examples

##### Calibrate a Sentinel product S1A
`./coresyf_calibration.py --Ssource S1A_EW_GRDM_1SDH_20171001T060648_20171001T060753_018615_01F62E_EE7F.zip --Ttarget myfile` 

### **Optimal Interpolation**
TBD

### **Image crop**
TBD

### **Image mask**
TBD

### **SAR Speckle filtering**
TBD

### **Image statistics**
TBD

### **Geo-referencing**
TBD

### **Error metrics**
TBD

### **Vector creation and edition**
TBD

### **Layer stack creation**
TBD
## CHANGE LOG
* V0.2: December 14, 2017: Dockerization
   * Dockerized toolkit
   * Improved readme
* V0.1: January 16, 2017: first release:
   * ADDED: Image Crop, Image Mask, Image Splitting, Image Stacking and Points-to-Grid tools.




