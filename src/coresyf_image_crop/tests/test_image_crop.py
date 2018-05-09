from unittest import TestCase
import shutil
from ..coresyf_image_crop import get_shapefile_polygon_extent, \
    get_shapefile_crs, read_zip_shapefile

class TestImageCrop(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_shapefile_polygon_extent(self):
        data_source = read_zip_shapefile('test_data/grid_EPSG_3763.shx.zip')
        get_shapefile_polygon_extent(data_source)
        print ("Ok")
        shutil.rmtree('temp_input')

    def test_get_shapefile_crs(self):
        data_source = read_zip_shapefile('test_data/grid_EPSG_3763.shx.zip')
        espg_code = get_shapefile_crs(data_source)
        self.assertEqual(espg_code, 3763)
        shutil.rmtree('temp_input')
