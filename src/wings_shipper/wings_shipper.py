"""A command line utility to deploy a wings application"""
import json
import zipfile
from os import getcwd, makedirs
from os.path import exists, join
from shutil import rmtree

import click

from wings_api.components import ManageComponents
from wings_api.data import ManageData


@click.command()
@click.option('--ipath', help='Path to the tool')
@click.option('--wurl', help='WINGS Instance URL')
@click.option('--wdomain', help='Wings domain to use')
@click.option('--wuser', help='Username for wings domain')
@click.option('--wpass', help='Password for username')
def deploy_application(ipath, wurl, wdomain, wuser, wpass):
    """The wrapper function to deploy the wings app"""
    try:
        validate_inputs(ipath, wurl, wdomain, wuser, wpass)
    except Exception as e:
        click_log(str(e), 'ERROR')
        return

    if not is_wings_parameters_defined(wurl, wdomain, wuser, wpass):
        wings_params = read_wings_config_file()
        wings_params['tool_zip_path'] = ipath
    else:
        wings_params = {
            'url': wurl,
            'domain': wdomain,
            'username': wuser,
            'password': wpass,
            'tool_zip_path': ipath
        }
    try:
        shipper = WingsShipper(**wings_params)
        log_shipper_information(shipper)

    except Exception as e:
        click_log(str(e), 'ERROR')
        shipper.cleanup_temp_dir()
        return

    try:
        shipper.ship_wings_tool()
        click_log('Application shipped!', 'SUCCESS')

    except Exception as e:
        click_log(str(e), 'ERROR')
        shipper.cleanup_temp_dir()
        return

    shipper.cleanup_temp_dir()


def validate_inputs(ipath, wurl, wdomain, wuser, wpass):
    if not exists(ipath):
        raise ValueError('Input path does not exist')
    if (wurl or wdomain or wuser or wpass) and \
            not (wurl and wdomain and wuser and wpass):
        raise AttributeError('All wings parameters must be defined.')
    if not is_wings_parameters_defined(wurl, wdomain, wuser, wpass) and \
            not exists('wings_config.json'):
        raise AttributeError(
            'Wings parameters undefined and config file does not exist')


def is_wings_parameters_defined(wurl, wdomain, wuser, wpass):
    return wurl and wdomain and wuser and wpass


def click_log(message, error_type):
    color = 'blue'
    bold = False
    if error_type == 'ERROR':
        color = 'red'
        bold = True
    elif error_type == 'SUCCESS':
        color = 'green'
        bold = True

    click.echo(click.style('[%s] %s' %
                           (error_type, message), fg=color, bold=bold))


def read_wings_config_file():
    wings_parameters = json.load(open('wings_config.json'))
    return {
        'url': wings_parameters['url'],
        'domain': wings_parameters['domain'],
        'username': wings_parameters['user'],
        'password': wings_parameters['password']
    }


def log_shipper_information(shipper):
    click_log('{}: {}'.format(
        shipper.manifest['name'], shipper.manifest['description']), 'INFO')
    click_log('Type: {}'.format(shipper.manifest['type']), 'INFO')
    click_log('{} inputs'.format(len(shipper.manifest['inputs'])), 'INFO')
    click_log('{} parameters'.format(
        len(shipper.manifest['parameters'])), 'INFO')
    click_log('{} outputs'.format(len(shipper.manifest['outputs'])), 'INFO')
    click_log('RUNNING SHIPPER...', 'INFO')


class WingsShipper(object):
    """A class to read manifest files and create appropriate wings components
    """

    def __init__(self, url, domain, username,
                 password, tool_zip_path):
        """Initiates shipper class and instantiates manage data and components.

        :param str url: url for the wings instance to use
        :param str domain: the wings domain to use
        :param str username: username of user where component
        shall be added
        :param str password: password to login the user
        :param tool_zip_path: path to the zipped file containing the tool
        """
        self.temp_dir = join(getcwd(), 'tmp')
        self.tool_zip_path = tool_zip_path
        self.manifest_path = None
        self.manifest = {}

        self.data_manager = ManageData(url, username, domain)
        self.component_manager = ManageComponents(
            url, username, domain)
        self.data_manager.login(password)
        self.component_manager.login(password)
        self.unzip_tool()
        self.read_manifest()

    def unzip_tool(self):
        """Unzips the tool to ship to wings to the temporary directory"""
        self.make_temporary_dir()
        zip_reference = zipfile.ZipFile(self.tool_zip_path, 'r')
        target_folder = zip_reference.namelist()[0]

        zip_reference.extractall(self.temp_dir)
        zip_reference.close()
        self.set_manifest_path(target_folder)

    def make_temporary_dir(self):
        """Creates a temporary directory to unzip file contents"""
        if not exists(self.temp_dir):
            makedirs(self.temp_dir)

    def set_manifest_path(self, target):
        """Sets the path to the manifest file"""
        self.manifest_path = join(
            self.temp_dir, target, 'manifest.json')

    def read_manifest(self):
        """Reads the manifest file and loads it into a dict"""
        self.manifest = json.load(open(join(self.manifest_path)))

    def ship_wings_tool(self):
        """Ships the tool to wings, adding it as a new component"""
        self.create_component_type()
        self.create_component()
        _inputs, _params, _outputs = self.parse_tool_arguments()

        self.add_component_properties(_inputs, _params, _outputs)
        self.component_manager.upload_component(
            self.get_component_id(), self.tool_zip_path)

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

    def parse_tool_arguments(self):
        """Reads the tool arguments from the manifest file"""
        _inputs = self.parse_data_argument(self.manifest['inputs'])
        _params = self.parse_parameter_argument(
            self.manifest['parameters'])
        _outputs = self.parse_data_argument(self.manifest['outputs'])
        return _inputs, _params, _outputs

    def parse_data_argument(self, raw_data):
        """Parses data arguments contained in the manifest"""
        data_list = []
        for _data in raw_data:
            self.create_data_type(_data['type'])
            data_list.append({
                'role': _data['identifier'],
                'type': _data['type'],
                'prefix': '-{}'.format(_data['identifier']),
                'dimensionality': self.get_dimensionality_value(_data)
            })
        return data_list

    def create_data_type(self, data_type):
        """Attempts to retrieve a data type. If it doesn't exist in wings,
        it creates a new one"""
        self.data_manager.new_data_type(data_type)

    @staticmethod
    def get_dimensionality_value(data_argument):
        """Check if the data argument has a collection parameter set to true.
            This means that the dimensionality will be 1 (we don't use
            dimensionalities greater than that)
        """
        if data_argument.get('collection'):
            return 1
        return 0

    def parse_parameter_argument(self, raw_parameters):
        """Parses parameter arguments contained in the manifest"""
        parameter_list = []
        for _parameter in raw_parameters:
            parameter_value = self.get_parameter_value(_parameter)
            parameter_type = self.get_parameter_type(_parameter)
            parameter_list.append({
                'role': _parameter['identifier'],
                'type': parameter_type,
                'prefix': '-{}'.format(_parameter['identifier']),
                'paramDefaultValue': parameter_value
            })
        return parameter_list

    def get_parameter_value(self, parameter):
        parameter_value = parameter['default']
        if parameter['type'] == 'list':
            parameter_value = str(parameter['default'])
        return parameter_value

    def get_parameter_type(self, parameter):
        parameter_type = parameter['type']
        if parameter_type == 'list':
            parameter_type = 'string'
        return parameter_type

    def add_component_properties(self, inputs, parameters, outputs):
        """Adds the properties of the component to wings"""
        self.component_manager.add_component_parameters(
            self.get_component_id(), inputs, parameters, outputs, '')

    def cleanup_temp_dir(self):
        """Removes the temporary dir and all its contents"""
        rmtree(self.temp_dir)


if __name__ == '__main__':
    deploy_application()
