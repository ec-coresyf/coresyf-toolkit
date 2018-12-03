#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Utility functions / classes for image intercalibration tool

    Provisional Means Class / library from Mort Canty CRCPython
"""
import numpy as np
from numpy.ctypeslib import ndpointer
import argparse
import platform
import ctypes
import os.path

if platform.system() == 'Windows':
    lib = ctypes.cdll.LoadLibrary('prov_means.dll')
elif platform.system() == 'Linux':
    lib = ctypes.cdll.LoadLibrary('libprov_means.so')
elif platform.system() == 'Darwin':
    lib = ctypes.cdll.LoadLibrary('libprov_means.dylib')
provmeans = lib.provmeans
provmeans.restype = None
c_double_p = ctypes.POINTER(ctypes.c_double)
provmeans.argtypes = [ndpointer(np.float64),
                      ndpointer(np.float64),
                      ctypes.c_int,
                      ctypes.c_int,
                      c_double_p,
                      ndpointer(np.float64),
                      ndpointer(np.float64)]

#===============================#
# Command Line Argument Parsing #
#===============================#

def create_parser():
    parser = argparse.ArgumentParser(prog='intercal',
                                     description='Relative radiometric normalization routine')
    parser.add_argument('-w', '--workdir',
                        default=os.path.dirname(__file__),
                        help="Path to working directory, default "+os.path.dirname(__file__),
                        metavar='DIR', type=lambda x: is_valid_dir(parser, x))
    parser.add_argument('-r', '--reffile',
                        help="Filename of reference raster image",
                        metavar='FILE', type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-i', '--infile',
                        help="Filename of the raster image to be corrected",
                        metavar='FILE', type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-s', '--shp',
                        help="Filename of shapefile defining PIFs",
                        metavar='FILE', type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-b', '--bands',)
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Provide debugging information")
    parser.add_argument('-t', '--type', default='irmad', type=str,
                        choices=['irmad', 'match', 'pif'],
                        help="Type of calibration - '[irmad]','match','pif'")
    return parser


def is_valid_dir(parser, path):
    # helper function to check if directory exists
    if not os.path.isdir(path):
        parser.error('The directory {} does not exist!'.format(path))
    else:
        return path


def is_valid_file(parser, filename):
    # helper function to check if file exists
    if not os.path.isfile(filename):
        parser.error('The file {} does not exist!'.format(filename))
    else:
        return filename


def sanity_check(opts):
    return True

#=============================#
# Provisional Means Algorithm #
#=============================#

class Cpm(object):
    '''Provisional means algorithm'''
    def __init__(self,N):
        self.mn = np.zeros(N)
        self.cov = np.zeros((N,N))
        self.sw = 0.0000001
         
    def update(self,Xs,Ws=None):
        n,N = np.shape(Xs)       
        if Ws is None:
            Ws = np.ones(n)
        sw = ctypes.c_double(self.sw)        
        mn = self.mn
        cov = self.cov
        provmeans(Xs,Ws,N,n,ctypes.byref(sw),mn,cov)
        self.sw = sw.value
        self.mn = mn
        self.cov = cov
          
    def covariance(self):
        c = np.mat(self.cov/(self.sw-1.0))
        d = np.diag(np.diag(c))
        return c + c.T - d
    
    def means(self):
        return self.mn 