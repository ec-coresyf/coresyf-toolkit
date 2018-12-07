#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Utility functions / classes for image intercalibration tool

    Provisional Means Class / library from Mort Canty CRCPython
"""
import numpy as np
from numpy.ctypeslib import ndpointer
from betaincder import betainc
import math
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
                        help="Path to working directory",
                        default="./",
                        metavar='DIR', type=lambda x: is_valid_dir(parser, x))
    parser.add_argument('-r', '--reffile',
                        help="Filepath of reference raster image",
                        metavar='FILE', type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-i', '--infile',
                        help="Filepath of the raster image to correct",
                        metavar='FILE', type=lambda x: is_valid_file(parser, x))
    parser.add_argument('--fsfile',
                        help="Filepath of the full scene image to correct",
                        metavar='FILE', type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-f', '--format',
                        help="A valid GDAL output file format. Default GeoTiFF",
                        type=str, default="GTiff")
    parser.add_argument('-s', '--shp',
                        help="Filepath of shapefile defining PIFs",
                        metavar='FILE', type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-b', '--bands',
                        help="Bands to be corrected e.g. -b 2 3 4, default band 1",
                        nargs='*', type=int, default=[])
    parser.add_argument('-t', '--type', 
                        help="Type of calibration - '[irmad]','match','pif'",
                        choices=['irmad', 'match', 'pif'],
                        default='irmad', type=str)
    parser.add_argument('-n', '--ncp',
                        help="No change threshold. Default 0.95",
                        type=float, default=0.95)
    parser.add_argument('--debug', default=False, action='store_true',
                        help="Provide debugging information")
    
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

#===========================#
# Generalized eigenproblem #
#===========================#

def geneiv(A,B): 
# solves A*x = lambda*B*x for numpy matrices A and B, 
# returns eigenvectors in columns
    Li = np.linalg.inv(choldc(B))
    C = Li*A*(Li.transpose())
    C = np.asmatrix((C + C.transpose())*0.5,np.float32)
    eivs,V = np.linalg.eig(C)
    return eivs, Li.transpose()*V


def choldc(A):
# Cholesky-Banachiewicz algorithm, 
# A is a numpy matrix
    L = A - A  
    for i in range(len(L)):
        for j in range(i):
            sm = 0.0
            for k in range(j):
                sm += L[i,k]*L[j,k]
            L[i,j] = (A[i,j]-sm)/L[j,j]
        sm = 0.0
        for k in range(i):
            sm += L[i,k]*L[i,k]
        L[i,i] = math.sqrt(A[i,i]-sm)        
    return L

#=================#
# Orthoregression #
#=================#

def orthoregress(x,y): 
    Xm = np.mean(x)
    Ym = np.mean(y) 
    s = np.cov(x,y)
    R = s[0,1]/math.sqrt(s[1,1]*s[0,0])
    lam,vs = np.linalg.eig(s)         
    idx = np.argsort(lam)    
    vs = vs[:,idx]      # increasing order, so
    b = vs[1,1]/vs[0,1] # first pc is second column
    return [b,Ym-b*Xm,R]

#===========================#
# F-test for equal variance #
#===========================#

def fv_test(x0,x1):
# taken from IDL library    
    nx0 = len(x0)
    nx1 = len(x1)
    v0 = np.var(x0)
    v1 = np.var(x1)
    if v0 >v1:
        f = v0/v1
        df0 = nx1-1
        df1 = nx0-1
    else:
        f = v1/v0
        df0 = nx1-1
        df1 = nx0-1
    prob = 2.0*betainc(0.5*df1,0.5*df0,df1/(df1+df0*f))
    if prob >1:
        return (f,2.0-prob)
    else:
        return (f,prob) 