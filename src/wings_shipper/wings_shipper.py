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
    shipper.parse_manifest()


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
        self.read_manifest()

    def read_manifest(self):
        """Reads the manifest file and loads it into a dict"""
        self.manifest = json.load(open(self.manifest_path))

    def parse_manifest(self):
        """Converts the manifest file into valid parameters to be uploaded to
        wings."""
        # A component's ID should not have spaces in the name.
        component_id = self.manifest['name'].replace(' ', '')
        component_type_id = '{}{}'.format(component_id, 'Type')

        self.create_component_type(component_type_id)

    def create_component_type(self, component_type_id):
        """Attempts to retrieve a component type. If it doesn't exist in wings,
        it creates a new one"""
        self.data_manager.new_data_type('MyType')
        self.component_manager.add_component_type(component_type_id)

    def create_component(self, component_type_id):
        """Attempts to retrieve a component. If it doesn't exist in wings,
        it creates a new one"""
        pass

    def create_data_type(self, data_type):
        """Attempts to retrieve a data type. If it doesn't exist in wings,
        it creates a new one"""
        pass

    def ship_wings_tool(self):
        """Ships the tool to wings, adding it as a new component"""
        pass


if __name__ == '__main__':
    deploy_application()
