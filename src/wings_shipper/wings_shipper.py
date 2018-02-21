"""A command line utility to deploy a wings application"""
from os.path import exists, join
from os import makedirs, getcwd
from shutil import rmtree
import click
import json
import zipfile
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
        wings_parameters = json.load(open('wings_config.json'))
        wurl = wings_parameters['url']
        wdomain = wings_parameters['domain']
        wuser = wings_parameters['user']
        wpass = wings_parameters['password']
    
    # try:
    shipper = WingsShipper(wurl, wdomain, wuser, wpass, ipath)
    click_log('{}: {}'.format(
        shipper.manifest['name'], shipper.manifest['description']), 'INFO')
    click_log('Type: {}'.format(shipper.manifest['type']), 'INFO')
    click_log('{} inputs'.format(len(shipper.manifest['inputs'])), 'INFO')
    click_log('{} parameters'.format(len(shipper.manifest['parameters'])), 'INFO')
    click_log('{} outputs'.format(len(shipper.manifest['outputs'])), 'INFO')
    click_log('RUNNING SHIPPER...', 'INFO')

    # except Exception as e:
    #     click_log(str(e), 'ERROR')
    #     return
    try:
        shipper.ship_wings_tool()
        click_log('Application shipped!', 'SUCCESS')
        
    except Exception as e:
        click_log(str(e), 'ERROR')
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
        raise AttributeError('Wings parameters undefined and config file does not exist')

def is_wings_parameters_defined(wurl, wdomain, wuser, wpass):
    return (wurl and wdomain and wuser and wpass)
    
def click_log(message, error_type):
    color = 'blue'
    bold = False
    if error_type == 'ERROR':
        color = 'red'
        bold = True
    elif error_type == 'SUCCESS':
        color = 'green'
        bold = True

    click.echo(click.style('[%s] %s' % (error_type, message), fg=color, bold=bold))

class WingsShipper(object):
    """A class to read manifest files and create appropriate wings components"""

    def __init__(self, wings_url, wings_domain, wings_user,
                 wings_pass, tool_zip_path):
        """Initiates shipper class and instantiates manage data and components.

        :param str wings_url: url for the wings instance to use
        :param str wings_domain: the wings domain to use
        :param str wings_user: username of user where component
        shall be added
        :param str wings_pass: password to login the user
        """
        self.temp_dir = join(getcwd(), 'tmp')
        self.data_manager = ManageData(wings_url, wings_user, wings_domain)
        self.component_manager = ManageComponents(
            wings_url, wings_user, wings_domain)
        self.data_manager.login(wings_pass)
        self.component_manager.login(wings_pass)
        self.tool_zip_path = tool_zip_path
        self.manifest_path = None
        self.manifest = {}
        self.unzip_tool()
        self.read_manifest()

    def unzip_tool(self):
        self.make_target_dir()
        zip_reference = zipfile.ZipFile(self.tool_zip_path, 'r')
        target_folder = zip_reference.namelist()[0]

        zip_reference.extractall(self.temp_dir)
        zip_reference.close()
        self.manifest_path = join(self.temp_dir, target_folder, 'manifest.json')

    def make_target_dir(self):
        if not exists(self.temp_dir):
            makedirs(self.temp_dir)

    def read_manifest(self):
        """Reads the manifest file and loads it into a dict"""
        self.manifest = json.load(open(join(self.manifest_path)))

    def ship_wings_tool(self):
        """Ships the tool to wings, adding it as a new component"""
        self.create_component_type()
        self.create_component()
        inputs_list = self.parse_data_argument(self.manifest['inputs'])
        params_list = self.parse_parameter_argument(
            self.manifest['parameters'])
        outputs_list = self.parse_data_argument(self.manifest['outputs'])
        self.add_component_properties(inputs_list, params_list, outputs_list)
        self.component_manager.upload_component(self.tool_zip_path)
        self.component_manager.set_component_location(self.get_component_id())

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
                'dimensionality': self.get_dimensionality_value(_data)
            })
        return data_list

    @staticmethod
    def get_dimensionality_value(data_argument):
        """Check if the data argument has a collection parameter set to true.
        This means that the dimensionality will be 1 (we don't use dimensionalities
        greater than that)"""
        if data_argument.get('collection'):
            return 1
        return 0

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

    def cleanup_temp_dir(self):
        rmtree(self.temp_dir)


if __name__ == '__main__':
    deploy_application()
