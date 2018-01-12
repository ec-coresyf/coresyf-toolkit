"""Contains a class to manage components in wings"""
import re
from .userop import UserOperation
import json


class ManageComponents(UserOperation):
    """A class to manage components in wings"""

    def __init__(self, server, userid, domain):
        super(ManageComponents, self).__init__(server, userid, domain)
        self.dcdom = self.get_export_url() + "components/ontology.owl#"
        self.dclib = self.get_export_url() + "components/library.owl#"
        self.dtypedom = self.get_export_url() + "data/ontology.owl#"

    def get_data_type_id(self, typeid):
        """Returns the type id based on an input id.
        If the input is none, returns a standard type (DataObject)
        If the input is a URL it returns itself

        :param str typeid: the type_id to convert
        :return: a valid WINGS type_id
        :rtype: str
        """
        if typeid is None:
            return 'http://www.wings-workflows.org/ontology/data.owl#DataObject'
        elif not re.match(r"(http:|https:)//", typeid):
            return '{}{}'.format(self.dtypedom, typeid)
        else:
            return typeid

    def get_type_id(self, type_id=None):
        """Returns the type id based on an input id.
        If the input is none, returns a standard type (Component)
        If the input is a URL it returns itself

        :param str type_id: the type_id to convert
        :return: a valid WINGS type_id
        :rtype: str
        """
        if type_id is None:
            return 'http://www.wings-workflows.org/ontology/component.owl#Component'
        elif not re.match(r"(http:|https:)//", type_id):
            return '{}{}'.format(self.dcdom, type_id)
        else:
            return type_id

    def get_component_id(self, component_id):
        """Builds a valid wings component identifier based on a string.
        If the string is already http formatted, returns itself.

        :param str component_id: The id of the component.
        :return: A valid WINGS component id
        :rtype: str
        """
        if not re.match(r'(http:|https:)//', component_id):
            return '{}{}'.format(self.dclib, component_id)
        else:
            return component_id

    def get_component_class(self, component_id):
        """Returns a class for a given component.

        The class corresponds simply to appending the 'Class' word to the 
        component id.

        :param str component_id: the component id to fetch the class
        :return: A valid wings component class
        :rtype: str
        """
        component_id = self.get_component_id(component_id)

        return '{}{}'.format(component_id, 'Class')

    def get_component(self, component_id):
        """Retrieves all available component types

        :param str component_id: the component id retrieve
        :return: The JSON response with the component (None if not found)
        :rtype: dict
        :raises AttributeErrror: if the component is invalid in wings context (code 500)
        """
        payload_data = {'cid': self.get_component_id(component_id)}
        resp = self.session.get(
            '{}components/getComponentJSON'.format(self.get_request_url()),
            params=payload_data)
        if resp.status_code == 500:
            raise AttributeError(
                'Component {} has an invalid attribute (rdf)'.format(component_id))

        return resp.json()

    def add_component_type(self, cid):
        """Adds a component type to WINGS.

        :param str cid: the component id to be added to wings
        :return: The payload sent to WINGS
        :rtype: dict
        """
        payload_params = {
            'parent_cid': '',
            'parent_type': self.get_type_id(),
            'cid': self.get_component_id(cid),
            'load_concrete': 'false'
        }
        self.session.post('{}components/type/addComponent'.format(
            self.get_request_url()), payload_params)
        return payload_params

    def add_component(self, parent_id, cid):
        """Adds a component to wings.

        :param str parent_id: The id of the parent component (component type)
        :param str cid: the component id to be added to wings
        :return: The payload sent to WINGS
        :rtype: dict
        """
        payload_params = {
            'parent_cid': self.get_component_id(parent_id),
            'parent_type': self.get_component_class(parent_id),
            'cid': self.get_component_id(cid),
            'load_concrete': 'true'
        }
        self.session.post(
            '{}components/addComponent'.format(self.get_request_url()), payload_params)
        return payload_params

    def add_component_parameters(self, component_id, inputs, parameters, outputs, rules):
        """Adds parameters to a component in WINGS.abs

        :param str inputs: The list of input data for the component
        :param str parameters: The list of input parameters for the component
        :param str outputs: thi list of output data for the component
        :return: The payload sent to wings
        :rtype: dict
        """
        component_params = {
            'id': self.get_component_id(component_id),
            'type': 2,
            'inputs': [],
            'outputs': [],
            'rulesText': rules,
            'requirement': {
                'softwareIds': [],
                'memoryGB': '0',
                'storageGB': '0',
                'needs64bit': False
            }
        }

        for _input in inputs:
            _input['type'] = self.get_data_type_id(_input['type'])
            _input['isParam'] = False
            component_params['inputs'].append(_input)

        for param in parameters:
            param['type'] = self._get_parameter_schema(param['type'])
            param['isParam'] = True
            component_params['inputs'].append(param)

        for output in outputs:
            output['type'] = self.get_data_type_id(_input['type'])
            output['isParam'] = False
            component_params['outputs'].append(output)

        payload_params = {
            'component_json': json.dumps(component_params),
            'load_concrete': True
        }

        self.session.post(
            '{}components/saveComponentJSON'.format(self.get_request_url()),
            data=payload_params)

        return payload_params

    def _get_parameter_schema(self, parameter_type):
        """Verifies if the parameter type is a valid XML schema type and
        returns the onthology for it.

        :param str parameter_type: The parameter type of the schema
        :return: The onthology for the parameter type
        :rtype: str
        :raises: TypeError if the parameter type is invalid.
        """
        valid_types = ['string', 'boolean', 'int', 'float', 'date']
        if parameter_type not in valid_types:
            raise TypeError('Parameter type invalid; must be one of: {}'.format(
                ' '.join(valid_types)
            ))

        return 'http://www.w3.org/2001/XMLSchema#{}'.format(parameter_type)
