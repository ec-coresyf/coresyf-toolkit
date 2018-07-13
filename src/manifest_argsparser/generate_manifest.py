#!/usr/bin/python2
import re
import glob
import os
import json
import click
from pathlib import Path
import logging
from argparse import ArgumentParser
ARG_ADDITION_REGEX = re.compile(r'.*parser.add_argument\(.*\)')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_argparser_in_file(filename):
    with open(filename) as source_file:
        source = source_file.read()
        matches = re.findall(ARG_ADDITION_REGEX, source)
        return matches

def write_manifest(manifest, tool_dir, tool_name):
    manifest_json = json.dumps(manifest, indent=4)
    manifest_file_name = tool_name + '.manifest.json'
    manifest_file_path = Path(tool_dir) / manifest_file_name
    with open(str(manifest_file_path), 'w') as manifest_file:
        manifest_file.write(manifest_json)

def create_argument_parser(filename):
    parser = ArgumentParser()
    logger.info('Parsing...')
    for line in parse_argparser_in_file(filename):
        logger.info('Parsing %s.', line)
        exec(line.strip())
    return parser


@click.command()
@click.option('--runfile')
@click.option('--tool_dir')
def create_manifest(runfile, tool_dir=None):
    if tool_dir is None:
        tool_dir = Path(runfile).parent
    name = Path(runfile).resolve().parent.name
    argparser = create_argument_parser(runfile)
    click.echo('Parsed arguments:')
    for prefix, _help in argparser.get_arguments_list():
        click.echo('{}: {}'.format(prefix, _help))
    input_options = raw_input('Which options are inputs? Write their prefixes separeted by space.\n')
    output_options = raw_input('Which options are outputs? Write their prefixes separated by space.\n')
    argparser.set_inputs(input_options.split())
    argparser.set_outputs(output_options.split())
    manifest = argparser.manifest()
    write_manifest(manifest, tool_dir, name)

if __name__ == '__main__':
    create_manifest()
