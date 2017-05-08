#!/usr/bin/env python
#==============================================================================
#                         <coresyf_isodata_classification.py>
#==============================================================================
# Project   : Co-ReSyF
# Company   : Deimos Engenharia
# Component : Co-ReSyF Tools (ISOdata classification algorithm)
# Language  : Python (v.2.6)
#------------------------------------------------------------------------------
# Scope : Command line ISOdata classification for GDAL supported files
# Usage : (see the following docstring)
#==============================================================================
# $LastChangedRevision:  $:
# $LastChangedBy:  $:
# $LastChangedDate:  $:
#==============================================================================

'''
@summary: 
This module runs the following Co-ReSyF tool:
 - ISODATA CLASSIFICATION
It uses the pyradar module isodata_classification to classificate a raster
into a defined number of classes.

@example:

Example 1 - Classify a GTiff image "example" and store the output in another GTiff:
python coresyf_isodata_classification.py -r ../examples/ISOdata_classification/example.TIF -o classified_example.tif


@attention: 
    @todo
    - Is projection checking performed???
    - Explore other limitations...


@version: v.1.0
@author: RIAA

@change:
1.0
- First release of the tool. 
'''

VERSION = '1.0'
USAGE   = ( '\n'
            'coresyf_isodata_classification.py [-r <InputRaster>]' 
            '[-c_threshold <ConvergenceThreshold>]'
            "[-i <IterationNumber>] [-k <InitialClusters>] [-s <StdThreshold>]"
            "[-p <PairClusters>] [-m <MinPixels>] [-c <MergeDist>]"
            "[-o <OutputRaster>] [--o_format=<OutputFileFormat>]"
            "\n")



''' SYSTEM MODULES '''
from optparse import OptionParser
import sys
import subprocess
from scipy.cluster.vq import vq     
#from pyradar.classifiers.isodata import isodata_classification
#from pyradar.core.equalizers import equalization_using_histogram
#from pyradar.core.sar import create_dataset_from_path
#from scipy import misc
import os
#import Image
import numpy as np
from osgeo import gdal
def gdal_create_image(target_file, width, height, bands, img_format, values, geotrans, proj):
    """create an gdal compatible image from a 3D matrix, where 1th dimension represents the
    bands, 2th the rows, and the 3th the lines of the image"""
    driver = gdal.GetDriverByName(img_format)
    if not driver:
        raise Exception('No gdal driver was found for %s.' % img_format)
    dataset = driver.Create(target_file, width, height, bands, gdal.GDT_Float32)
    dataset.GetRasterBand(1).WriteArray(values)
    dataset.SetGeoTransform(geotrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    return dataset
def initial_clusters(img_flat, k, method="linspace"):
    """
    Define initial clusters centers as startup.
    By default, the method is "linspace". Other method available is "random".
    """
    methods_availables = ["linspace", "random"]

    assert method in methods_availables, "ERROR: method %s is no valid." \
                                         "Methods availables %s" \
                                         % (method, methods_availables)
    if method == "linspace":
        max, min = img_flat.max(), img_flat.min()
        centers = np.linspace(min, max, k)
    '''elif method == "random":
        start, end = 0, img_flat.size
        indices = np.random.randint(start, end, k)
        centers = img_flat.take(indices)'''

    return centers

def discard_clusters(img_class_flat, centers, clusters_list, THETA_M):
    """
    Discard clusters with fewer than THETA_M.
    """
    k = centers.shape[0]
    to_delete = np.array([])

    assert centers.size == clusters_list.size, \
        "ERROR: discard_cluster() centers and clusters_list size are different"

    for cluster in xrange(0, k):
        indices = np.where(img_class_flat == clusters_list[cluster])[0]
        total_per_cluster = indices.size
        if total_per_cluster <= THETA_M:
            to_delete = np.append(to_delete, cluster)

    if to_delete.size:
        new_centers = np.delete(centers, to_delete)
        new_clusters_list = np.delete(clusters_list, to_delete)
    else:
        new_centers = centers
        new_clusters_list = clusters_list

    new_centers, new_clusters_list = sort_arrays_by_first(new_centers,
                                                          new_clusters_list)

#        shape_bef = centers.shape[0]
#        shape_aft = new_centers.shape[0]
#        print "Isodata(info): Discarded %s clusters." % (shape_bef - shape_aft)

#        if to_delete.size:
#            print "Clusters discarded %s" % to_delete

    assert new_centers.size == new_clusters_list.size, \
        "ERROR: discard_cluster() centers and clusters_list size are different"

    return new_centers, new_clusters_list

def sort_arrays_by_first(centers, clusters_list):
    """
    Sort the array 'centers' and the with indices of the sorted centers
    order the array 'clusters_list'.
    Example: centers=[22, 33, 0, 11] and cluster_list=[7,6,5,4]
    returns  (array([ 0, 11, 22, 33]), array([5, 4, 7, 6]))
    """
    assert centers.size == clusters_list.size, \
    "ERROR: sort_arrays_by_first centers and clusters_list size are not equal"

    indices = np.argsort(centers)

    sorted_centers = centers[indices]
    sorted_clusters_list = clusters_list[indices]

    return sorted_centers, sorted_clusters_list

def update_clusters(img_flat, img_class_flat, centers, clusters_list):
    """ Update clusters. """
    k = centers.shape[0]
    new_centers = np.array([])
    new_clusters_list = np.array([])

    assert centers.size == clusters_list.size, \
        "ERROR: update_clusters() centers and clusters_list size are different"

    for cluster in xrange(0, k):
        indices = np.where(img_class_flat == clusters_list[cluster])[0]
        #get whole cluster
        cluster_values = img_flat[indices]
        #sum and count the values
        sum_per_cluster = cluster_values.sum()
        total_per_cluster = (cluster_values.size) + 1
        #compute the new center of the cluster
        new_cluster = sum_per_cluster / total_per_cluster

        new_centers = np.append(new_centers, new_cluster)
        new_clusters_list = np.append(new_clusters_list, cluster)

    new_centers, new_clusters_list = sort_arrays_by_first(new_centers,
                                                          new_clusters_list)

    assert new_centers.size == new_clusters_list.size, \
        "ERROR: update_clusters() centers and clusters_list size are different"

    return new_centers, new_clusters_list

def split_clusters(img_flat, img_class_flat, centers, clusters_list, THETA_S, THETA_M):
    """
    Split clusters to form new clusters.
    """
    assert centers.size == clusters_list.size, \
        "ERROR: split() centers and clusters_list size are different"

    delta = 10
    k = centers.size
    count_per_cluster = np.zeros(k)
    stddev = np.array([])

    avg_dists_to_clusters = compute_avg_distance(img_flat, img_class_flat,
                                                 centers, clusters_list)
    d = compute_overall_distance(img_class_flat, avg_dists_to_clusters,
                                 clusters_list)

    # compute all the standard deviation of the clusters
    for cluster in xrange(0, k):
        indices = np.where(img_class_flat == clusters_list[cluster])[0]
        count_per_cluster[cluster] = indices.size
        value = ((img_flat[indices] - centers[cluster]) ** 2).sum()
        value /= count_per_cluster[cluster]
        value = np.sqrt(value)
        stddev = np.append(stddev, value)

    cluster = stddev.argmax()
    max_stddev = stddev[cluster]
    max_clusters_list = int(clusters_list.max())

    if max_stddev > THETA_S:
        if avg_dists_to_clusters[cluster] >= d:
            if count_per_cluster[cluster] > (2.0 * THETA_M):
                old_cluster = centers[cluster]
                new_cluster_1 = old_cluster + delta
                new_cluster_2 = old_cluster - delta

                centers = np.delete(centers, cluster)
                clusters_list = np.delete(clusters_list, cluster)

                centers = np.append(centers, [new_cluster_1, new_cluster_2])
                clusters_list = np.append(clusters_list, [max_clusters_list,
                                          (max_clusters_list + 1)])

                centers, clusters_list = sort_arrays_by_first(centers,
                                                              clusters_list)

                assert centers.size == clusters_list.size, \
                   "ERROR: split() centers and clusters_list size are different"

    return centers, clusters_list

def compute_avg_distance(img_flat, img_class_flat, centers, clusters_list):
    """
    Computes all the average distances to the center in each cluster.
    """
    k = centers.size
    avg_dists_to_clusters = np.array([])

    for cluster in xrange(0, k):
        indices = np.where(img_class_flat == clusters_list[cluster])[0]

        total_per_cluster = indices.size + 1
        sum_per_cluster = (np.abs(img_flat[indices] - centers[cluster])).sum()

        dj = (sum_per_cluster / float(total_per_cluster))

        avg_dists_to_clusters = np.append(avg_dists_to_clusters, dj)

    return avg_dists_to_clusters

def compute_overall_distance(img_class_flat, avg_dists_to_clusters,
                             clusters_list):
    """
    Computes the overall distance of the samples from their respective cluster
    centers.
    """
    k = avg_dists_to_clusters.size
    total = img_class_flat.size
    count_per_cluster = np.zeros(k)

    for cluster in xrange(0, k):
        indices = np.where(img_class_flat == clusters_list[cluster])[0]
        count_per_cluster[cluster] = indices.size

    d = ((count_per_cluster / total) * avg_dists_to_clusters).sum()

    return d

def merge_clusters(img_class_flat, centers, clusters_list, P, THETA_C):
    """
    Merge by pair of clusters in 'below_threshold' to form new clusters.
    """
    pair_dists = compute_pairwise_distances(centers)

    first_p_elements = pair_dists[:P]

    below_threshold = [(c1, c2) for d, (c1, c2) in first_p_elements
                                if d < THETA_C]

    if below_threshold:
        k = centers.size
        count_per_cluster = np.zeros(k)
        to_add = np.array([])  # new clusters to add
        to_delete = np.array([])  # clusters to delete

        for cluster in xrange(0, k):
            result = np.where(img_class_flat == clusters_list[cluster])
            indices = result[0]
            count_per_cluster[cluster] = indices.size

        for c1, c2 in below_threshold:
            c1_count = float(count_per_cluster[c1]) + 1
            c2_count = float(count_per_cluster[c2])
            factor = 1.0 / (c1_count + c2_count)
            weight_c1 = c1_count * centers[c1]
            weight_c2 = c2_count * centers[c2]

            value = round(factor * (weight_c1 + weight_c2))

            to_add = np.append(to_add, value)
            to_delete = np.append(to_delete, [c1, c2])

        #delete old clusters and their indices from the availables array
        centers = np.delete(centers, to_delete)
        clusters_list = np.delete(clusters_list, to_delete)

        #generate new indices for the new clusters
        #starting from the max index 'to_add.size' times
        start = int(clusters_list.max())
        end = to_add.size + start

        centers = np.append(centers, to_add)
        clusters_list = np.append(clusters_list, xrange(start, end))

        centers, clusters_list = sort_arrays_by_first(centers, clusters_list)

    return centers, clusters_list

def compute_pairwise_distances(centers):
    """
    Compute the pairwise distances 'pair_dists', between every two clusters
    centers and returns them sorted.
    Returns:
           - a list with tuples, where every tuple has in it's first coord the
             distance between to clusters, and in the second coord has a tuple,
             with the numbers of the clusters measured.
             Output example:
                [(d1,(cluster_1,cluster_2)),
                 (d2,(cluster_3,cluster_4)),
                 ...
                 (dn, (cluster_n,cluster_n+1))]
    """
    pair_dists = []
    size = centers.size

    for i in xrange(0, size):
        for j in xrange(0, size):
            if i > j:
                d = np.abs(centers[i] - centers[j])
                pair_dists.append((d, (i, j)))

    #return it sorted on the first elem
    return sorted(pair_dists)

def quit_low_change_in_clusters(centers, last_centers, iter, THETA_O):
    """Stop algorithm by low change in the clusters values between each
    iteration.
    :returns: True if should stop, otherwise False.
    """
    quit = False
    if centers.shape == last_centers.shape:
        thresholds = np.abs((centers - last_centers) / (last_centers + 1))

        if np.all(thresholds <= THETA_O):  # percent of change in [0:1]
            quit = True
#            print "Isodata(info): Stopped by low threshold at the centers."
#            print "Iteration step: %s" % iter

    return quit

def isodata_classification(img, parameters):
    """
    Classify a numpy 'img' using Isodata algorithm.
    Parameters: a dictionary with the following keys.
            - img: an input numpy array that contains the image to classify.
            - parameters: a dictionary with the initial values.
              If 'parameters' are not specified, the algorithm uses the default
              ones.
                  + number of clusters desired.
                    K = 15
                  + max number of iterations.
                    I = 100
                  + max number of pairs of clusters which can be ,erged.
                    P = 2
                  + threshold value for min number in each cluster.
                    THETA_M = 10
                  + threshold value for standard deviation (for split).
                    THETA_S = 0.1
                  + threshold value for pairwise distances (for merge).
                    THETA_C = 2
                  + threshold change in the clusters between each iter.
                    THETA_O = 0.01
        Note: if some(or all) parameters are nos providen, default values
              will be used.
    Returns:
            - img_class: a numpy array with the classification.
    """
    k = parameters["K"]
    P = parameters["P"]
    THETA_C = parameters["THETA_C"]
    no_data_value=parameters["no_data_value"]
    N, M = img.shape  # for reshaping at the end
    img_flat = img.flatten()
    img_flat = img_flat.tolist()
    idx = [i for i, x in enumerate(img_flat) if x != no_data_value]
    minus = np.ones(len(img_flat), dtype=np.int)*(-1)
    img_flat=np.asarray(img_flat)
    img_flat_aux = img_flat[idx]


    #img_flat = np.asarray(img_flat_aux)
    img_flat = img_flat_aux

    clusters_list = np.arange(k)  # number of clusters availables
    print "Isodata(info): Starting algorithm with %s classes" % k
    centers = initial_clusters(img_flat, k, "linspace")

    for iter in xrange(0, parameters["I"]):
#        print "Isodata(info): Iteration:%s Num Clusters:%s" % (iter, k)
        last_centers = centers.copy()
        # assing each of the samples to the closest cluster center
        img_class_flat, dists = vq(img_flat, centers)

        centers, clusters_list = discard_clusters(img_class_flat,
                                                  centers, clusters_list, parameters["THETA_M"])
        centers, clusters_list = update_clusters(img_flat,
                                                 img_class_flat,
                                                 centers, clusters_list)
        k = centers.size

        if k <= (parameters["K"] / 2.0):  # too few clusters => split clusters
            centers, clusters_list = split_clusters(img_flat, img_class_flat,
                                                    centers, clusters_list, parameters["THETA_M"], parameters["THETA_S"])

        elif k > (parameters["K"] * 2.0):  # too many clusters => merge clusters
            centers, clusters_list = merge_clusters(img_class_flat, centers,
                                                    clusters_list, P, THETA_C)
        else:  # nor split or merge are needed
            pass

        k = centers.size
###############################################################################
        if quit_low_change_in_clusters(centers, last_centers, iter, parameters["THETA_O"]):
            break

#        take_snapshot(img_class_flat.reshape(N, M), iteration_step=iter)
###############################################################################
    print "Isodata(info): Finished with %s classes" % k
    print "Isodata(info): Number of Iterations: %s" % (iter + 1)
    
    img_class_flat_aux = img_class_flat.tolist() 
    minus[idx]=img_class_flat_aux
    img_class_flat = np.asarray(minus)
    return img_class_flat.reshape(N, M)

def main():
    parser = OptionParser(usage   = USAGE, 
                          version = VERSION)
    
    #==============================#
    # Define command line options  #
    #==============================#
    parser.add_option('-r', 
                      dest="input_raster", metavar=' ',
                      help="input raster file (GDAL supported file)", )
    parser.add_option('-o', 
                      dest="output_raster_classified", metavar=' ',
                      help=("output raster file classified using ISODATA "
                            "algorithm (default: 'classified_image.tif')"),
                      default="classified_image.tif")
    parser.add_option('--o_format', 
                      dest="output_format", metavar=' ',
                      help="GDAL format for output file (default: 'GTiff')",
                      default="GTiff" )
    parser.add_option('--c_threshold', 
                      dest="convergence_threshold", metavar=' ',
                      help="Threshold of the change allowed in the clusters between each iteration (default: 0.01)",
                      default=0.01 )
    parser.add_option('-i', 
                      dest="iteration_number", metavar=' ',
                      help="Maximum number of iterations (default: 100)",
                      default=100 )
    parser.add_option('-k', 
                      dest="initial_clusters", metavar=' ',
                      help="Number of initial clusters (default: 15)",
                      default=15 )
    parser.add_option('-s', 
                      dest="std_threshold", metavar=' ',
                      help="Threshold value for standard deviation, to split the clusters (default: 0.1)",
                      default=0.1 )
    parser.add_option('-p', 
                      dest="pair_clusters", metavar=' ',
                      help="Maximum number of pairs of clusters which can be merged (default: 2)",
                      default=2 )
    parser.add_option('-m', 
                      dest="min_pixels", metavar=' ',
                      help="Minimum number of pixels in each cluster (default: 10)",
                      default=10 )
    parser.add_option('-c', 
                      dest="merge_dist", metavar=' ',
                      help="Maximum distance between clusters before merging (default: 2)",
                      default=2 )
    parser.add_option('--no_data_value', 
                      dest="no_data_value", metavar=' ',
                      help="Pixel value excluded from the classification (default: 0)",
                      type=int,
                      default=0 )

    #==============================#
    #   Check mandatory options    #
    #==============================#
    (opts, args) = parser.parse_args()

    if len(sys.argv) == 1:
        print(USAGE)
        return
    if not opts.input_raster:
        print("No input raster provided. Nothing to do!")
        print(USAGE)
        return
    
    params = {"K": opts.initial_clusters, "I" : opts.iteration_number, "P" : opts.pair_clusters, "THETA_M" : opts.min_pixels, "THETA_S" : opts.std_threshold,
          "THETA_C" : opts.merge_dist, "THETA_O" : opts.convergence_threshold, "no_data_value" : opts.no_data_value}


    data = gdal.Open(opts.input_raster)
    width=data.RasterXSize
    height=data.RasterYSize
    geotrans=data.GetGeoTransform()  
    proj=data.GetProjection() 
    dataset = np.array(data.GetRasterBand(1).ReadAsArray())
    target_file=opts.output_raster_classified
    img_format=opts.output_format
    class_image = isodata_classification(dataset, parameters=params)
    #print(np.unique(class_image))
    gdal_create_image(target_file, width, height, 1, img_format, class_image, geotrans, proj)


if __name__ == '__main__':
    main()