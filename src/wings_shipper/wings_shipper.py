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
    click.echo(click.style(
        '[INFO] Reading manifest file: %s' % ipath, fg='blue'))

    try:
        shipper = WingsShipper(wurl, wdomain, wuser, wpass, ipath)
        click.echo(click.style(
            '[INFO] %s: %s' % (shipper.manifest['name'],
                            shipper.manifest['description']),
            fg='blue'))
        click.echo(click.style(
            '[INFO] Type: %s' % shipper.manifest['type'], fg='blue'))
        click.echo(click.style(
            '[INFO] %i inputs' % len(shipper.manifest['inputs']), fg='blue'))
        click.echo(click.style(
            '[INFO] %i parameters' % len(shipper.manifest['parameters']), fg='blue'))
        click.echo(click.style(
            '[INFO] %i outputs' % len(shipper.manifest['outputs']), fg='blue'))
        click.echo(click.style(
            '[INFO] RUNNING SHIPPER...', fg='blue', bold=True))
    except Exception as e:
        click.echo(click.style(
            '[ERROR] Application encountered an error initializing: %s' % str(e),
            fg='red', bold=True))
        return
    try:
        shipper.ship_wings_tool()
        click.echo(click.style(
            '[SUCCESS] Application shipped!', fg='green', bold=True
        ))
    except Exception as e:
        click.echo(click.style(
            '[ERROR] Application encountered an error initializing: %s' % str(e),
            fg='red', bold=True))
        return


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

    def ship_wings_tool(self):
        """Ships the tool to wings, adding it as a new component"""
        self.create_component_type()
        self.create_component()
        inputs_list = self.parse_data_argument(self.manifest['inputs'])
        params_list = self.parse_parameter_argument(self.manifest['parameters'])
        outputs_list = self.parse_data_argument(self.manifest['outputs'])
        self.add_component_properties(inputs_list, params_list, outputs_list)

    def read_manifest(self):
        """Reads the manifest file and loads it into a dict"""
        self.manifest = json.load(open(self.manifest_path))

    def create_component_type(self):
        """Attempts to retrieve a component type. If it doesn't exist in wings,
        it creates a new one"""
        self.component_manager.add_component_type(self.manifest['type'])

    def create_component(self):
        """Attempts to retrieve a component. If it doesn't exist in wings,
        it creates a new one"""
        self.component_manager.add_component(self.manifest['type'],
                                             self.get_component_id())

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

    def parse_parameter_argument(self, raw_parameters):
        parameter_list = []
        for _parameter in raw_parameters:
            parameter_list.append({
                'role': _parameter['identifier'],
                'type': _parameter['type'],
                'prefix': '--{}'.format(_parameter['identifier']),
                'paramDefaultValue': _parameter['default']
            })
        return parameter_list

    def create_data_type(self, data_type):
        """Attempts to retrieve a data type. If it doesn't exist in wings,
        it creates a new one"""
        self.data_manager.new_data_type(data_type)

    def add_component_properties(self, inputs, parameters, outputs):
        self.component_manager.add_component_parameters(
            self.get_component_id(), inputs, parameters, outputs, '')


if __name__ == '__main__':
    deploy_application()
