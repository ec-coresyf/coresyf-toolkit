#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" CoReSyF Image Inter-calibration Tool
@summary:
This module runs the following Co-ReSyF tool:
    - IMAGE INTERCALIBRATION
It takes a raster image as reference and a raster image to correct.
Depending on input arguments it performs relative radiative normalisation
of the image to be corrected with the reference image.

@attention:
    - Note that both raster images must have the same dimensions.
"""

import tools.irmad as mad
import tools.image as img
import tools.auxil as aux

def main():

    print "running"
    IrMad = mad.IRMAD('working')

if __name__ == "__main__":
    main()