#!/usr/bin/env python
#==============================================================================
#                         <wingsUtils.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (Wings utils)
# Language  : Python (v.2.7)
#------------------------------------------------------------------------------
# Scope : (see the following docstring)
# Usage : python snapFileSelector.py
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
This module contains functions and other utilities that can be used to check 
and prepare input and output data to be Wings compliant.

It will be used to automatically prepare data to be run by the Co-ReSyf tools.
The following cases were taken into account:
- the input and/or output files are compressed files (.zip only);
- the input and/or output extensions are not provided.   


------------------------------------------------------------------------------
@info
Adapted from: no references 


@version: v.1.0
@author: RCCC

'''

__version__ = '1.0'


''' SYSTEM MODULES '''
import sys
import os
import zipfile
import shutil


''' IMPORTANT PARAMETERS '''
TEMP_PATH_IN = os.path.abspath("temp_input") + "/"
TEMP_PATH_OUT = os.path.abspath("temp_output") + "/"



#============================================#
# Funtions for preparing INPUT/OUTPUT data   #
#============================================#

def prepareInputData(input_path, extension="", temp_path=TEMP_PATH_IN):
    '''
    Prepare input data and return the input path to be ingested by Co-ReSyf tools.
    @param[in] input_path -> input file path that was passed as a tool argument (Type: String)
    @param[in] extension -> file extension. If empty the first file found within the zip file will be returned (Type: String)
    @param[in] temp_path -> temporary path to be used for extracting all input contents (Type: String)
    @return    input_path -> input path of the file to be ingested by the tool (Type: String)
               wasUnZipped -> flag indicating if input data was successfully extracted (Type: bool)
    '''
    input_path = os.path.abspath(input_path)
    wasUnZipped = False
    
    if zipfile.is_zipfile(input_path):   # input is a zipped file
        myzip = zipfile.ZipFile(input_path, 'r')
        if not myzip.infolist():
            raise ("Input Zip file '%s' is empty!" % input_path)
        myzip.extractall( temp_path )
        myzip.close()

        input_list = [os.path.join(temp_path, x) for x in os.listdir(temp_path) if x.endswith(extension)] # input file 
        if input_list: 
            input_path = input_list[0]
            wasUnZipped = True
    
    return input_path, wasUnZipped


def prepareOutputData(output_path, temp_path=TEMP_PATH_OUT):
    '''
    Prepare output data and return the output path to be ingested by Co-ReSyf tools.
    @param[in] output_path -> output file path that was passed as a tool argument (Type: String)
    @param[in] temp_path -> temporary path to be used for storing all output files (Type: String)
    @return    output_path -> output path of the file to be ingested by the tool (Type: String)
               output_zip -> path of the compressed file that will contain all output data (Type: String)
    '''
    output_path = os.path.abspath(output_path)
    output_zip = None
    extension = os.path.splitext( output_path )[1]
    if not extension or extension == ".zip": 
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        output_zip = output_path
        output_path = os.path.join(temp_path, os.path.basename(output_path)) # temporary path is used as output path for running the tool
    return output_path, output_zip


#=================#
# Compress data   #
#=================#
def compressData(dataFolder, filepath_zip):
    myzip = zipfile.ZipFile(filepath_zip, "w" )
    
    for file in os.listdir(dataFolder):
        file_path = os.path.abspath( os.path.join(dataFolder, file) )
        myzip.write( file_path, 
                     arcname=os.path.basename(file_path), 
                     compress_type=zipfile.ZIP_DEFLATED   )    
    myzip.close()
    shutil.rmtree(dataFolder)

def clearTempData( datafolder ):
    if os.path.isfile(datafolder):
        datafolder = os.path.dirname(datafolder)
        shutil.rmtree( datafolder )        


if __name__ == '__main__':
    pass


