"""A command line utility to deploy a wings application"""
import click
from wings_api.components import ManageComponents


@click.command()
@click.option('--ipath', help='Path to zip file containing application manifest')
def deploy_application(ipath):
    """The wrapper function to deploy the wings app"""
    click.echo('Deploying application to wings. Reading from %s' % ipath)


if __name__ == '__main__':
    deploy_application()
