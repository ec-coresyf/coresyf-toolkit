import os
import re
import json
from .userop import UserOperation


class ManageData(UserOperation):
    """A class to manage data in WINGS"""
    def __init__(self, server, userid, domain):
        super(ManageData, self).__init__(server, userid, domain)
        self.dcdom = self.get_export_url() + "data/ontology.owl#"
        self.dclib = self.get_export_url() + "data/library.owl#"

    def get_type_id(self, typeid):
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
            return self.dcdom + typeid
        else:
            return typeid

    def get_data_id(self, dataid):
        """Builds a valid wings data identifier based on a string.
        If the string is already http formatted, returns itself.

        :param str dataid: The id of the data.
        :return: A valid WINGS data id
        :rtype: str
        """
        if not re.match(r"(http:|https:)//", dataid):
            return self.dclib + dataid
        else:
            return dataid

    def new_data_type(self, dtype, parent=None):
        """Adds a new data type to wings
        
        :param str dtype: the datatype to add
        :param str parent: the datatype parent (supertype)
        """
        parent = self.get_type_id(parent)
        dtype = self.get_type_id(dtype)
        postdata = {'parent_type': parent, 'data_type': dtype}
        self.session.post(self.get_request_url() +
                          'data/newDataType', postdata)

    def add_type_properties(self, dtype, properties):
        """Adds properties to a WINGS data type.

        :param str dtype: the datatype where properties will be added
        :param dict properties: a dictionary with properties to add to the 
        datatype. Must have the following format:
            {
                'property_name_1': 'property_range_1',
                'property_name_2': 'property_range_2'
            }
        """
        xsd = 'http://www.w3.org/2001/XMLSchema#'
        dtype = self.get_type_id(dtype)
        data = {'add': {}, 'del': {}, 'mod': {}}
        for pname in properties:
            pid = self.get_type_id(pname)
            prange = xsd + properties[pname]
            data['add'][pid] = {'prop': pname, 'pid': pid, 'range': prange}
        postdata = {'data_type': dtype, 'props_json': json.dumps(data)}
        self.session.post(self.get_request_url() +
                          'data/saveDataTypeJSON', postdata)

    def add_data_for_type(self, dataid, dtype):
        """Adds a data object for a given type.

        :param str dataid: the id of the data to add
        :param str dtype: the type of data to add (WINGS datatype)
        """
        dtype = self.get_type_id(dtype)
        dataid = self.get_data_id(dataid)
        postdata = {'data_id': dataid, 'data_type': dtype}
        self.session.post(self.get_request_url() +
                          'data/addDataForType', postdata)

    def del_data_type(self, dtype):
        """Removes a data type from WINGS

        :param str dtype: the datatype to be removed
        """
        dtype = self.get_type_id(dtype)
        postdata = {'data_type': json.dumps([dtype]), 'del_children': 'true'}
        self.session.post(self.get_request_url() +
                          'data/delDataTypes', postdata)

    def del_data(self, dataid):
        """Removes a data object from wings

        :param str dataid: The id of the data object to be removed
        """
        dataid = self.get_data_id(dataid)
        postdata = {'data_id': dataid}
        self.session.post(self.get_request_url() + 'data/delData', postdata)

    def get_all_items(self):
        """Retrieves all data items in WINGS.

        :return: All data items in wings
        :rtype: dict
        """
        resp = self.session.get(
            self.get_request_url() + 'data/getDataHierarchyJSON')
        return resp.json()

    def get_data_description(self, dataid):
        """Retrieves information for a WINGS data item

        :param str dataid: the id of the data item to retrieve
        :return: The properties of the data item
        :rtype: dict
        """
        dataid = self.get_data_id(dataid)
        postdata = {'data_id': dataid}
        resp = self.session.post(
            self.get_request_url() + 'data/getDataJSON', postdata)
        return resp.json()

    def get_datatype_description(self, dtype):
        """Retrieves information for a WINGS data type

        :param str dtype: the id of the data type to retrieve
        :return: The properties of the data type
        :rtype: dict
        """
        dtype = self.get_type_id(dtype)
        postdata = {'data_type': dtype}
        resp = self.session.post(
            self.get_request_url() + 'data/getDataTypeJSON', postdata)
        return resp.json()

    def upload_data_for_type(self, filepath, dtype):
        """Uploads a data file for a given data type.

        :param str filepath: the path to the file to be uploaded
        :param str dtype: the datatype to which the file will be uploaded
        :return: the id of the data that was added
        :rtype: str
        """
        dtype = self.get_type_id(dtype)
        fname = os.path.basename(filepath)
        files = {'file': (fname, open(filepath, 'rb'))}
        postdata = {'name': fname, 'type': 'data'}
        response = self.session.post(self.get_request_url() + 'upload',
                                     data=postdata, files=files)
        if response.status_code == 200:
            details = response.json()
            if details['success']:
                dataid = os.path.basename(details['location'])
                dataid = re.sub(r"(^\d.+$)", r"_\1", dataid)
                self.add_data_for_type(dataid, dtype)
                self.set_data_location(dataid, details['location'])
                return dataid

    def save_metadata(self, dataid, metadata):
        """Saves the metadata for a WINGS data item

        :param str dataid: id of the data item to save the metadata
        :param dict metadata: a dict with the metadata to be saved.
        Must have the following format:
            {
                'property_name_1': 'property_value_1',
                'property_name_2': 'property_value_2'
            }
        """
        pvals = []
        for key in metadata:
            if(metadata[key]):
                pvals.append(
                    {'name': self.dcdom + key, 'value': metadata[key]})
        postdata = {'propvals_json': json.dumps(
            pvals), 'data_id': self.get_data_id(dataid)}
        self.session.post(self.get_request_url() +
                          'data/saveDataJSON', postdata)

    def set_data_location(self, dataid, location):
        """Sets the location of a given WINGS data item

        :param str dataid: the id of the data item
        :param str location: the new location path for the data item
        """
        postdata = {'data_id': self.get_data_id(dataid), 'location': location}
        self.session.post(self.get_request_url() +
                          'data/setDataLocation', postdata)
