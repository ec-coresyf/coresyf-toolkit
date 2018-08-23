import unittest
from ..domain import ManageDomain


class DomainTestCase(unittest.TestCase):
    '''
        Domain API test case
    '''
    # pylint: disable=too-many-instance-attributes
    # We don't care about this when testing.

    def setUp(self):
        self.user = 'rccc'
        self.password = 'avidacosta'
        self.domain_zip_filepath = 'tests/test_data/test_domain.zip'
        self.domain = ManageDomain('https://wings.coresyf.eu/wings', self.user)
        self.domain.login(self.password)

    def test_can_import_domain(self):
        """Tests if it is possible to import a new domain to wings, using a
        local zip file with domain properties.
        """
        response = self.domain.import_domain(self.domain_zip_filepath)

        expected_response = {
            'engine': 'Local',
            'name': 'test_domain',
            'url': 'http://localhost:8080/wings/export/users/rccc/test_domain',
            'isLegacy': False,
            'directory': '/usr/share/tomcat8/.wings/storage/users/rccc/test_domain',
            'permissions': []
            }

        self.assertDictEqual(response, expected_response)

    def test_can_select_default_domain(self):
        """Tests if it is possible to select a new domain as the default one.
        """
        self.domain.import_domain(self.domain_zip_filepath)
        response = self.domain.select_default_domain('test_domain')
        self.assertEqual(response, 'OK')
        self.assertEqual(self.domain.get_selected_domain(), 'test_domain')

    def tearDown(self):
        pass
