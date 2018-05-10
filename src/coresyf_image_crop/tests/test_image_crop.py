from unittest import TestCase
import os
import shutil
from osgeo import ogr
from ..coresyf_image_crop import get_shapefile_polygon_extent, \
    get_shapefile_crs, read_zip_shapefile, crop_raster

TEMP_PATH = "temp_path"


class TestImageCrop(TestCase):

    def setUp(self):
        self.data_source = read_zip_shapefile('test_data/grid_EPSG_3763.zip',
                                              TEMP_PATH)
        self.extent_polygon_wkt = "POLYGON ((" + \
            "-61575.57812574980926 103754.81329901740537 0," \
            "-54172.937265817548905 103754.81329901740537 0," \
            "-54172.937265817548905 107225.478697661776096 0," \
            "-61575.57812574980926 107225.478697661776096 0,"\
            "-61575.57812574980926 103754.81329901740537 0))"
        
        self.epsg_code = 3763

    def tearDown(self):
        if os.path.isdir(TEMP_PATH):
            shutil.rmtree(TEMP_PATH)

    def test_get_shapefile_polygon_extent(self):
        extent_polygon = get_shapefile_polygon_extent(self.data_source)
        self.assertTrue(extent_polygon.IsValid())
        self.assertEqual(extent_polygon.ExportToWkt(), self.extent_polygon_wkt)

    def test_get_shapefile_crs(self):
        epsg_code = get_shapefile_crs(self.data_source)
        self.assertEqual(epsg_code, self.epsg_code)

    def test_crop_raster(self):
        test_image = 'test_data/Aveiro_resampled.tif'
        output_image = os.path.join(TEMP_PATH, 'output')
        polygon_ext = ogr.CreateGeometryFromWkt(self.extent_polygon_wkt)
        polygon_ext = polygon_ext.Buffer(2000, 0)
        crop_raster(test_image, output_image, polygon_ext, self.epsg_code)
        self.assertNotEqual(os.path.getsize(output_image), 0)
        self.assertLess(os.path.getsize(output_image),
                        os.path.getsize(test_image))
