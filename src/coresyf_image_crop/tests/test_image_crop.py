from unittest import TestCase
from ..coresyf_image_crop import get_shapefile_polygon_extent, read_zip_shapefile


class TestImageCrop(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_shapefile_polygon_extent(self):
        data_source = read_zip_shapefile('/home/rccc/Downloads/Crop_Tool_DESIGN/grid_EPSG_3763.zip')
        get_shapefile_polygon_extent(data_source)
        print ("Ok")
        pass
