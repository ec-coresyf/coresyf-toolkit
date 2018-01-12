"""A command line utility to deploy a wings application"""
import click
import json
from wings_api.components import ManageComponents
from wings_api.data import ManageData


@click.command()
@click.option('--ipath', help='Path to the manifest file')
@click.option('--wurl', help='WINGS Instance URL')
@click.option('--wuser', help='Username for wings domain')
@click.option('--wpass', help='Password for username')
def deploy_application(ipath, wurl, wuser, wpass):
    """The wrapper function to deploy the wings app"""
    click.echo('Deploying application to wings. Reading from %s' % ipath)
    shipper = WingsShipper(wurl, wuser, wpass, ipath)
    print(shipper.manifest)


class WingsShipper(object):
    """A class to read manifest files and create appropriate wings components"""
    def __init__(self, wings_url, wings_user, wings_pass, manifest_path):
        """Initiates shipper class and instantiates manage data and components.

        :param str wings_url: url for the wings instance to use
        :param str wings_user: username of user where component 
        shall be added
        :param str wings_pass: password to login the user
        """
        self.data_manager = ManageData(wings_url, wings_user, wings_pass)
        self.component_manager = ManageComponents(wings_url, wings_user, wings_pass)
        self.manifest_path = manifest_path
        self.read_manifest()

    def read_manifest(self):
        """Reads the manifest file and loads it into a dict"""
        self.manifest = json.load(open(self.manifest_path))
    
    def parse_manifest(self):
        """Converts the manifest file into valid parameters to be uploaded to
        wings."""
        pass

    def get_or_create_data_type(self, data_type):
        """Attempts to retrieve a data type. If it doesn't exist in wings,
        it creates a new one"""
        pass
    
    def get_or_create_component_type(self, component_type):
        """Attempts to retrieve a component type. If it doesn't exist in wings,
        it creates a new one"""
        pass
    
    def ship_wings_tool(self):
        """Ships the tool to wings, adding it as a new component"""
        pass


if __name__ == '__main__':
    deploy_application()