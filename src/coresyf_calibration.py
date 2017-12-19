#!/usr/bin/env python
'''
@summary: 
This module runs the following Co-ReSyF tool:
 - CALIBRATION
 It uses the command line based Graph Processing Tool (GPT) to perform radiometric
callibration of mission products. The input must be the whole product (use either
 the 'manifest.safe' or the whole product in a zip file as input).

@example:

Example 1 - Calibrate a Sentinel product S1A:
./coresyf_calibration.py --Ssource S1A_EW_GRDM_1SDH_20171001T060648_20171001T060753_018615_01F62E_EE7F.zip 
                         --Ttarget myfile

@attention: 
    @todo
    - Add a product file to be used as example in 'examples' directory
    - Develop test script

@version: v.1.0

@change:
1.0
- First release of the tool. 
'''
import os

import json

from gpt import call_gpt

from coresyf_tool_base import CoReSyFTool

TOOL_DEF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coresyf_calibration_tool.json')


class CoReSyFCalibration(CoReSyFTool):
    '''CoReSyF Calibration tool'''

    def run(self, bindings):
        source = bindings.pop('Ssource')
        target = bindings.pop('Ttarget')
        call_gpt('Calibration', source, target, bindings)


if __name__ == '__main__':
    TOOL = CoReSyFCalibration(TOOL_DEF_FILE)
    TOOL.execute()
