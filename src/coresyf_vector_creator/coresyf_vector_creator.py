#!/usr/bin/python2
from coresyftools.tool import CoReSyFTool
import csv
import os

from osgeo import ogr, osr

''' PROGRAM MODULES '''
from wingsUtils import prepareOutputData, compressData


class CoresyfVectorCreator(CoReSyFTool):

    def createVector(self, data_file, output_vector, format_name='ESRI Shapefile',
                     crs_data=4326, crs_vector=4326):
        '''
        It opens the text file with the features and points coordinates and
        creates a vector file (shapefile) with all points and respective data.
        :param str data_file: path of the text file.
        :param str output_vector: path of the output vector file.
        :param str format_name: output vector format
        :param str crs_data: coordinate reference system of the input data
        :param str crs_vector: coordinate reference system of the output vector
                               data.
        '''
        # set up the shapefile driver
        driver = ogr.GetDriverByName(format_name)
        # Remove output shapefile if it already exists
        if os.path.exists(output_vector):
            driver.DeleteDataSource(output_vector)
        # create the data source
        dst_datasource = driver.CreateDataSource(output_vector)
        # Create layer with the spatial reference defined by 'crs_vector'
        in_srs = osr.SpatialReference()
        in_srs.ImportFromEPSG(int(crs_data))
        out_srs = osr.SpatialReference()
        out_srs.ImportFromEPSG(int(crs_vector))
        transform_crs = osr.CoordinateTransformation(in_srs, out_srs)

        layer_name = os.path.splitext(os.path.basename(output_vector))[0]
        dst_layer = dst_datasource.CreateLayer(layer_name, srs=out_srs,
                                               geom_type=ogr.wkbPoint)
        # Read data from data file
        data = csv.DictReader(open(data_file, 'rb'), delimiter=',',
                              quoting=csv.QUOTE_NONE)

        # Add a new fields
        for field in data.fieldnames:
            new_field = ogr.FieldDefn(field, ogr.OFTReal)
            dst_layer.CreateField(new_field)
            new_field = None

        # Add features and attributes to the shapefile
        for row in data:
            feature = ogr.Feature(dst_layer.GetLayerDefn())
            for field in data.fieldnames:
                feature.SetField(field, row[field])
            # create the geometry from WKT
            wkt = 'POINT(%f %f)' % (float(row['Longitude']),
                                    float(row['Latitude']))
            point = ogr.CreateGeometryFromWkt(wkt)
            point.Transform(transform_crs)
            feature.SetGeometry(point)
            dst_layer.CreateFeature(feature)
            feature = None
        dst_datasource = None

    def run(self, bindings):
        data_file = bindings['Ssource']
        output_format = bindings['o_format']
        input_crs = bindings['in_crs']
        output_crs = bindings['o_crs']
        output_vector = bindings['Ttarget']

        # Check output&input extensions (required for Wings)
        output_vector, output_vector_zip = prepareOutputData(output_vector)

        self.createVector(data_file, output_vector, output_format,
                          input_crs, output_crs)

        # Compress output files into zip file (required for Wings)
        if output_vector and output_vector_zip:
            compressData(output_vector, output_vector_zip)
