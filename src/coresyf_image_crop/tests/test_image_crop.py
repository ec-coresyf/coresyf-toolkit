from unittest import TestCase
import os
import shutil
from osgeo import ogr, gdal
from ..coresyf_image_crop import get_shapefile_polygon_extent, \
    get_shapefile_crs, read_shapefile, apply_buffer_to_polygon, \
    get_raster_crs

TEMP_PATH = "temp_path"


class TestImageCrop(TestCase):

    def setUp(self):
        self.data_source = read_shapefile('test_data/grid_EPSG_3763')
        self.extent_polygon_wkt = "POLYGON ((" + \
            "-61575.57812574980926 103754.81329901740537 0," \
            "-54172.937265817548905 103754.81329901740537 0," \
            "-54172.937265817548905 107225.478697661776096 0," \
            "-61575.57812574980926 107225.478697661776096 0,"\
            "-61575.57812574980926 103754.81329901740537 0))"

        self.epsg_code = 3763
        self.test_image = 'test_data/Aveiro_resampled.tif'
        self.test_image_4236 = "test_data/Aveiro_resampled_4326.tif"

    def tearDown(self):
        pass

    def test_get_shapefile_polygon_extent(self):
        extent_polygon = get_shapefile_polygon_extent(self.data_source)
        self.assertTrue(extent_polygon.IsValid())
        self.assertEqual(extent_polygon.ExportToWkt(), self.extent_polygon_wkt)

    def test_get_shapefile_crs(self):
        epsg_code = get_shapefile_crs(self.data_source)
        self.assertEqual(epsg_code, self.epsg_code)

    def test_apply_buffer_to_polygon(self):
        buffer_crs = get_raster_crs(gdal.Open(self.test_image_4236))
        polygon_extent = get_shapefile_polygon_extent(self.data_source)
        buffer_4326 = 0.022207
        buffer_3763 = 2000
        polygon_crs = get_shapefile_crs(self.data_source)

        polygon_with_buffer = apply_buffer_to_polygon(buffer_4326, polygon_extent,
                                                      buffer_crs, polygon_crs)

        expected_polygon = ogr.CreateGeometryFromWkt(self.extent_polygon_wkt)
        expected_polygon = expected_polygon.Buffer(buffer_3763, 0)

        for n in range(4):
            self.assertAlmostEqual(polygon_with_buffer.GetEnvelope()[n],
                                   expected_polygon.GetEnvelope()[n], delta=500)
