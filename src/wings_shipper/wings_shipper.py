"""A command line utility to deploy a wings application"""
import click
import json
from wings_api.components import ManageComponents
from wings_api.data import ManageData


@click.command()
@click.option('--ipath', help='Path to the manifest file')
@click.option('--wurl', help='WINGS Instance URL')
@click.option('--wdomain', help='Wings domain to use')
@click.option('--wuser', help='Username for wings domain')
@click.option('--wpass', help='Password for username')
def deploy_application(ipath, wurl, wdomain, wuser, wpass):
    """The wrapper function to deploy the wings app"""
    click.echo('Deploying application to wings. Reading from %s' % ipath)
    shipper = WingsShipper(wurl, wdomain, wuser, wpass, ipath)
    shipper.ship_wings_tool()


class WingsShipper(object):
    """A class to read manifest files and create appropriate wings components"""

    def __init__(self, wings_url, wings_domain, wings_user,
                 wings_pass, manifest_path):
        """Initiates shipper class and instantiates manage data and components.

        :param str wings_url: url for the wings instance to use
        :param str wings_domain: the wings domain to use
        :param str wings_user: username of user where component
        shall be added
        :param str wings_pass: password to login the user
        """
        self.data_manager = ManageData(wings_url, wings_user, wings_domain)
        self.component_manager = ManageComponents(
            wings_url, wings_user, wings_domain)
        self.data_manager.login(wings_pass)
        self.component_manager.login(wings_pass)
        self.manifest_path = manifest_path
        self.manifest = {}

    def ship_wings_tool(self):
        """Ships the tool to wings, adding it as a new component"""
        self.read_manifest()
        self.create_component_type()
        self.create_component()
        inputs_list = self.parse_data_argument(self.manifest['inputs'])
        print(inputs_list)
        # params_list = self.read_parameters()
        outputs_list = self.parse_data_argument(self.manifest['outputs'])
        print(outputs_list)

    def read_manifest(self):
        """Reads the manifest file and loads it into a dict"""
        self.manifest = json.load(open(self.manifest_path))

    def create_component_type(self):
        """Attempts to retrieve a component type. If it doesn't exist in wings,
        it creates a new one"""
        self.component_manager.add_component_type(self.get_component_type_id())

    def create_component(self):
        """Attempts to retrieve a component. If it doesn't exist in wings,
        it creates a new one"""
        self.component_manager.add_component(self.get_component_type_id(),
                                             self.get_component_id())

    def get_component_type_id(self):
        """Returns the component type, which consists of appending
        the keyword 'type' at the end of the component"""
        return '{}Type'.format(self.get_component_id())

    def get_component_id(self):
        """Reads the manifest file and returns the component ID.

        It consists of stripping the name of the component from spaces.
        """
        return self.manifest['name'].replace(' ', '')

    def parse_data_argument(self, raw_data):
        data_list = []
        for _data in raw_data:
            self.create_data_type(_data['type'])
            data_list.append({
                'role': _data['identifier'],
                'type': _data['type'],
                'prefix': '--{}'.format(_data['identifier']),
                'dimensionality': _data['dimensionality']
            })
        return data_list

    def create_data_type(self, data_type):
        """Attempts to retrieve a data type. If it doesn't exist in wings,
        it creates a new one"""
        pass


if __name__ == '__main__':
    deploy_application()
