from unittest import TestCase
from ..coresyf_image_crop import get_shapefile_polygon_extent


class TestImageCrop(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_shapefile_polygon_extent(self):
        get_shapefile_polygon_extent('/home/rccc/Downloads/Crop_Tool_DESIGN/grid_EPSG_3763.shp')
        print ("Ok")
        pass
