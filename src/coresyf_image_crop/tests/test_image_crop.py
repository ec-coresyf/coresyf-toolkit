from unittest import TestCase
import os
import shutil
from ..coresyf_image_crop import get_shapefile_polygon_extent, \
    get_shapefile_crs, read_zip_shapefile

TEMP_PATH = "temp_path"


class TestImageCrop(TestCase):

    def setUp(self):
        self.data_source = read_zip_shapefile('test_data/grid_EPSG_3763.zip', 
                                              TEMP_PATH)

    def tearDown(self):
        if os.path.isdir(TEMP_PATH):
            shutil.rmtree(TEMP_PATH)

    def test_get_shapefile_polygon_extent(self):
        data_source = read_zip_shapefile('test_data/grid_EPSG_3763.shx.zip')
        get_shapefile_polygon_extent(data_source)
        print ("Ok")

    def test_get_shapefile_crs(self):
        data_source = read_zip_shapefile('test_data/grid_EPSG_3763.shx.zip')
        espg_code = get_shapefile_crs(data_source)
        self.assertEqual(espg_code, 3763)
        
