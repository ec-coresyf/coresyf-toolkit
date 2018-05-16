from unittest import TestCase
from osgeo import ogr, osr
from ..coresyf_image_crop import get_shapefile_polygon_extent, \
    get_shapefile_crs, read_shapefile, apply_buffer_to_polygon

TEMP_PATH = "temp_path"


class TestImageCrop(TestCase):

    def setUp(self):
        self.data_source = read_shapefile('test_data/grid_EPSG_3763')
        self.polygon_extent_wkt = "POLYGON ((" + \
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
        self.assertEqual(extent_polygon.ExportToWkt(), self.polygon_extent_wkt)

    def test_get_shapefile_crs(self):
        epsg_code = get_shapefile_crs(self.data_source)
        self.assertEqual(epsg_code, self.epsg_code)

    def test_apply_buffer_to_polygon(self):
        buffer_4326_units = 0.022207
        buffer_3763_units = 2000
        crs_buffer = 4326
        crs_polygon = 3763
        polygon_extent = ogr.CreateGeometryFromWkt(self.polygon_extent_wkt)
        osr_polygon = osr.SpatialReference()
        osr_polygon.ImportFromEPSG(crs_polygon)
        polygon_extent.AssignSpatialReference(osr_polygon)

        polygon_with_buffer = apply_buffer_to_polygon(polygon_extent,
                                                      buffer_4326_units,
                                                      crs_polygon,
                                                      crs_buffer)

        expected_polygon = polygon_extent.Buffer(buffer_3763_units, 0)

        for n in range(4):
            self.assertAlmostEqual(polygon_with_buffer.GetEnvelope()[n],
                                   expected_polygon.GetEnvelope()[n],
                                   delta=500)
