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

from gpt import call_gpt

from coresyf_tool_base import CoReSyF_Tool

CONFIG = {
    'name': 'CoReSyF calibration',
    'description': 'CoReSyF calibration tool',
    'arguments': [
        {
            'identifier': 'Ssource',
            'name': 'source',
            'description': "Sets source to <filepath>",
            'type': 'data',
            'required': True
        },
        {
            'identifier': 'PexternalAuxFile',
            'name': 'external auxiliary file',
            'description': "The antenna elevation pattern gain auxiliary data file.",
            'type': 'data'
        },
        {
            'identifier': 'PauxFile',
            'name': 'auxiliary file',
            'type': 'parameter',
            'parameterType': 'string',
            'description': "Value must be one of 'Latest Auxiliary File', 'Product Auxiliary File'",
            'options': ['Latest Auxiliary File', 'Product Auxiliary File', 'External Auxiliary File'],
        },
        {
            'identifier': 'PcreateBetaBand',
            'name': 'create beta band',
            'type': 'parameter',
            'parameterType': 'boolean',
            'description': "Create beta0 virtual band."
        },
        {
            'identifier': 'PcreateGammaBand',
            'name': 'create gamma band',
            'type': 'parameter',
            'parameterType': 'boolean',
            'description': "Create gamma0 virtual band."
        },
        {
            'identifier': 'PoutputBetaBand',
            'name': 'output beta band',
            'type': 'parameter',
            'parameterType': 'boolean',
            'description': "Output beta0 band."
        },
        {
            'identifier': 'PoutputGammaBand',
            'name': 'output gamma band',
            'type': 'parameter',
            'parameterType': 'boolean',
            'description': "Output gamma0 band."
        },
        {
            'identifier': 'PoutputImageInComplex',
            'name': 'output image in complex',
            'type': 'parameter',
            'parameterType': 'boolean',
            'description': 'Output image in complex.'
        },
        {
            'identifier': 'PoutputImageScaleInDb',
            'name': 'output image scale in db',
            'type': 'parameter',
            'parameterType': 'boolean',
            'description': "Output image scale."
        },
        {
            'identifier': 'PoutputSigmaBand',
            'name': 'output sigma band',
            'type': 'parameter',
            'parameterType': 'boolean',
            'description': "Output sigma0 band."
        },
        {
            'identifier': 'PsourceBands',
            'name': 'source bands',
            'type': 'parameter',
            'description': "The list of source bands.",
            'parameterType': 'string',
        },
        {
            'identifier': 'Ttarget',
            'name': 'target',
            'description': "Sets the target to <filepath>",
            'type': 'output'
        }
    ]
}


class CoReSyFCalibration(CoReSyF_Tool):
    '''CoReSyF Calibration tool'''

    def run(self, bindings):
        source = bindings.pop('Ssource')
        target = bindings.pop('Ttarget')
        call_gpt('Calibration', source, target, bindings)


if __name__ == '__main__':
    TOOL = CoReSyFCalibration(CONFIG)
    TOOL.execute()
