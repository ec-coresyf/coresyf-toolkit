import unittest
from ..components import ManageComponents
from ..data import ManageData
import json


class ApplicationsTestCase(unittest.TestCase):
    '''
        Application API test case
    '''
    # pylint: disable=too-many-instance-attributes
    # We don't care about this when testing.

    def setUp(self):
        self.component_instance = ManageComponents(
            'http://wings:8080/wings', 'admin', 'blank')
        self.component_instance.login('ptp2ta')

    def test_can_get_type_id(self):
        """Tests if it is possible to retrieve the correct component id in three scenarios:

            1. Passing no parameter, in which case a fixed type must be returned;
            2. Passing a non-url parameter, in which case an ontology type is returned;
            3. Passing a url parameter, in which case the value is considered valid and returned
        """
        self.assertEqual(self.component_instance.get_type_id(),
                         'http://www.wings-workflows.org/ontology/component.owl#Component')
        self.assertEqual(self.component_instance.get_type_id('Dummy'),
                         'http://wings:8080/wings/export/users/admin/blank/components/ontology.owl#Dummy')
        self.assertEqual(
            self.component_instance.get_type_id(
                'http://www.wings-workflows.org/ontology/component.owl#Dummy'),
            'http://www.wings-workflows.org/ontology/component.owl#Dummy')

    def test_can_get_component_id(self):
        """Tests if it is possible to retrieve the correct component id in three scenarios:

            1. Passing no parameter, in which case a fixed type must be returned;
            2. Passing a non-url parameter, in which case an ontology type is returned;
            3. Passing a url parameter, in which case the value is considered valid and returned
        """
        self.assertEqual(self.component_instance.get_component_id('garbage'),
                         'http://wings:8080/wings/export/users/admin/blank/components/library.owl#garbage')
        self.assertEqual(
            self.component_instance.get_component_id(
                'http://wings:8080/wings/export/users/admin/blank/components/library.owl#garbage'),
            'http://wings:8080/wings/export/users/admin/blank/components/library.owl#garbage')

    def test_can_get_parent_class(self):
        """Tests if, given a parent identifier, it is possible to retrieve it's type/class"""
        self.assertEqual(
            self.component_instance.get_component_class('garbage'),
            'http://wings:8080/wings/export/users/admin/blank/components/library.owl#garbageClass')
        self.assertEqual(
            self.component_instance.get_component_class(
                'http://wings:8080/wings/export/users/admin/blank/components/library.owl#garbage'),
            'http://wings:8080/wings/export/users/admin/blank/components/library.owl#garbageClass')

    def test_can_get_component(self):
        """Tests if it is possible to retrieve a component from wings

        NOTE: we should be testing adding a component and retrieving it
        to see if the response is different than None. However, we have tests
        below that use this method with components in WINGS.
        """
        self.assertEqual(self.component_instance.get_component(
            'dummycomponent'), None)

    def test_can_add_component_type(self):
        """Tests if it is possible to add a new component type to wings"""
        component_params = {
            'parent_cid': '',
            'parent_type': 'http://www.wings-workflows.org/ontology/component.owl#Component',
            'cid': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#testComponentType',
            'load_concrete': 'false'
        }
        # We check if the build payload equals what is expected
        component_payload = self.component_instance.add_component_type(
            'testComponentType')
        self.assertEqual(component_payload, component_params)

        # We check if everything was added to the database
        self.assertEqual(self.component_instance.get_component(
            'http://wings:8080/wings/export/users/admin/blank/components/library.owl#testComponentType')['id'],
            component_params['cid'])

    def test_can_add_component(self):
        """Tests if it is possible to add a new component to wings.

            It differs from test above because it has a different parent
        """
        # We need to add a new component type since we cannot rely on previous
        # tests to carry out subsequent ones
        self.component_instance.add_component_type('testComponentType2')
        component_params = {
            'parent_cid': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#testComponentType2',
            'parent_type': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#testComponentType2Class',
            'cid': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#testComponent',
            'load_concrete': 'true'
        }
        component_payload = self.component_instance.add_component(
            'testComponentType2',
            'testComponent'
        )
        self.assertEqual(component_payload, component_params)

        # We try retrieving a component without the full ID to verify it makes
        # the proper conversion
        self.assertEqual(self.component_instance.get_component('testComponent')['id'],
                         component_params['cid'])

    def test_get_invalid_component_raises_exception(self):
        """Tests if trying to retrieve a component with invalid parameters (ontology-wise) raises
        an attribute error.
        """
        self.component_instance.add_component(
            'falseComponent',
            'testComponentError'
        )
        with self.assertRaises(AttributeError):
            self.component_instance.get_component('testComponentError')

    def test_can_add_component_parameters(self):
        """Tests if it is possible to add parameters to a component"""
        # We need to create a data type
        data_instance = ManageData(
            'http://wings:8080/wings', 'admin', 'blank')
        data_instance.login('ptp2ta')
        data_instance.new_data_type('Raster')

        # We need to create the components first
        self.component_instance.add_component_type('parameterComponentType')
        self.component_instance.add_component(
            'parameterComponentType', 'parameterComponent')

        inputs_dict = [
            {
                'role': 'Input1',
                'type': 'Raster',
                'prefix': '-i1',
                'dimensionality': 0,
            }, {
                'role': 'Input2',
                'type': 'Raster',
                'prefix': '-i2',
                'dimensionality': 1,
            }
        ]

        parameters_dict = [
            {
                'role': 'param1',
                'type': 'string',
                'prefix': '-p1',
                'paramDefaultValue': 'one',
            }, {
                'role': 'param2',
                'type': 'int',
                'prefix': '-p2',
                'paramDefaultValue': 1,
            }
        ]

        outputs_dict = [
            {
                'role': 'output1',
                'type': 'Raster',
                'prefix': '-o1',
                'dimensionality': 1,
            }, {
                'role': 'output2',
                'type': 'Raster',
                'prefix': '-o2',
                'dimensionality': 0,
            }
        ]

        expected_payload = {
            'component_json': json.dumps({
                'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent',
                'type': 2,
                'inputs': [
                    {
                        'role': 'Input1',
                        'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                        'prefix': '-i1',
                        'dimensionality': 0,
                        'isParam': False
                    }, {
                        'role': 'Input2',
                        'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                        'prefix': '-i2',
                        'dimensionality': 1,
                        'isParam': False
                    }, {
                        'role': 'param1',
                        'type': 'http://www.w3.org/2001/XMLSchema#string',
                        'prefix': '-p1',
                        'paramDefaultValue': 'one',
                        'isParam': True
                    }, {
                        'role': 'param2',
                        'type': 'http://www.w3.org/2001/XMLSchema#int',
                        'prefix': '-p2',
                        'paramDefaultValue': 1,
                        'isParam': True
                    }
                ],
                'outputs': [
                    {
                        'role': 'output1',
                        'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                        'prefix': '-o1',
                        'dimensionality': 1,
                        'isParam': False
                    }, {
                        'role': 'output2',
                        'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                        'prefix': '-o2',
                        'dimensionality': 0,
                        'isParam': False
                    }
                ],
                'rulesText': '',
                'requirement': {
                    'softwareIds': [],
                    'memoryGB': '0',
                    'storageGB': '0',
                    'needs64bit': False
                }
            }),
            'load_concrete': True
        }
        rules = ''

        # We check that the parameters are being passed correctly to WINGS
        self.assertDictEqual(expected_payload, self.component_instance.add_component_parameters(
            'parameterComponent', inputs_dict, parameters_dict, outputs_dict, rules
        ))

        payload_response = {
            'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent',
            'type': 2,
            'inputs': [
                {
                    'role': 'Input1',
                    'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                    'prefix': '-i1',
                    'dimensionality': 0,
                    'isParam': False,
                    'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent_Input1'
                }, {
                    'role': 'Input2',
                    'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                    'prefix': '-i2',
                    'dimensionality': 1,
                    'isParam': False,
                    'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent_Input2'
                }, {
                    'role': 'param1',
                    'type': 'http://www.w3.org/2001/XMLSchema#string',
                    'prefix': '-p1',
                    'paramDefaultValue': 'one',
                    'isParam': True,
                    'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent_param1'
                }, {
                    'role': 'param2',
                    'type': 'http://www.w3.org/2001/XMLSchema#int',
                    'prefix': '-p2',
                    'paramDefaultValue': 1,
                    'isParam': True,
                    'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent_param2'
                }
            ],
            'outputs': [
                {
                    'role': 'output1',
                    'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                    'prefix': '-o1',
                    'dimensionality': 1,
                    'isParam': False,
                    'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent_output1'
                }, {
                    'role': 'output2',
                    'type': 'http://wings:8080/wings/export/users/admin/blank/data/ontology.owl#Raster',
                    'prefix': '-o2',
                    'dimensionality': 0,
                    'isParam': False,
                    'id': 'http://wings:8080/wings/export/users/admin/blank/components/library.owl#parameterComponent_output2'
                }
            ],
            'rules': [],
            'inheritedRules': [],
            'requirement': {
                'softwareIds': [],
                'memoryGB': 0,
                'storageGB': 0,
                'needs64bit': False
            }
        }

        # We check that the request to get the component has everything correctly defined
        self.assertDictEqual(self.component_instance.get_component(
            'parameterComponent'), payload_response)

    def tearDown(self):
        pass
