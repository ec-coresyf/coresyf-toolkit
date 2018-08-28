"""A command line utility to deploy a domain"""
from os.path import exists, join
from xml.dom import minidom

import click

from wings_api.domain import ManageDomain
from wings_shipper import deploy_application

CORESYFTOOLS_TARGET_DIR = '../coresyftools/target/'


@click.command()
@click.option('--wurl', help='WINGS Instance URL')
@click.option('--idomain', help='Path to the zipped domain file')
@click.option('--ilist_tools', help='Path to the file with the list of tools')
@click.option('--iusers', help='Path to the XML file with the list of users')
def deploy_domain_to_users(wurl, idomain, ilist_tools, iusers):
    """The wrapper function to deploy the domain to wings users"""
    try:
        validate_inputs(wurl, idomain, ilist_tools, iusers)
    except Exception as e:
        click_log(str(e), 'ERROR')
        return

    list_users_credentials = read_users_credentials(iusers)
    list_tools = read_list_tools(ilist_tools)

    for user_dict in list_users_credentials:
        username = user_dict['username']
        password = user_dict['password']
        try:
            domain_name = deploy_domain(username, password, idomain)
            click_log('Domain "{}" deployed for user "{}"!'.format(domain_name, username), 'SUCCESS')
        except Exception as e:
            click_log(str(e), 'ERROR')

        for tool in list_tools:
            try:
                deploy_application(tool, wurl, domain_name, username, password)
            except Exception as e:
                click_log(str(e), 'ERROR')


def validate_inputs(wurl, idomain, ilist_tools, iusers):
    if not exists(idomain):
        raise ValueError('Input path with zipped domain file does not exist')
    if not (wurl and idomain and ilist_tools and iusers):
        raise AttributeError('All parameters must be defined.')


def read_users_credentials(xml_users):
    list_user_credentials = []
    mydoc = minidom.parse(xml_users)
    users_elements = mydoc.getElementsByTagName('user')

    for elem in users_elements:
        list_user_credentials.append({
            'username': elem.attributes['username'].value,
            'password': elem.attributes['password'].value,
            })
    return list_user_credentials


def read_list_tools(txt_tools):
    list_tools = []
    lines = [line.rstrip('\n') for line in open(txt_tools)]
    for i in range(0, len(lines)):
        tool_zip_filename = lines[i].strip() + '.zip'
        list_tools.append(join(CORESYFTOOLS_TARGET_DIR, tool_zip_filename))
    return list_tools


def deploy_domain(user, password, domain_zip_filepath):
    domain = ManageDomain('https://wings.coresyf.eu/wings', user)
    domain.login(password)

    response = domain.import_domain(domain_zip_filepath)
    domain_name = response['name']
    domain.select_default_domain(domain_name)
    return domain_name


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


if __name__ == '__main__':
    deploy_domain_to_users()
