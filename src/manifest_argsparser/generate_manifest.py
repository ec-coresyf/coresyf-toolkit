#!/usr/bin/python2
import re
import glob
import os
import click
from pathlib import Path
from argparse import ArgumentParser
ARG_ADDITION_REGEX = re.compile(r'\s*parser.add_argument\(.*\)\n')

def parse_argparser_in_file(filename):
    with open(filename) as source_file:
        source = source_file.read()
        matches = re.findall(ARG_ADDITION_REGEX, source)
        return matches

def create_argument_parser(filename):
    parser = ArgumentParser()
    for line in parse_argparser_in_file(filename):
        exec(line.strip())
    return parser


@click.command()
@click.option('--runfile')
@click.option('--tool_dir')
def create_manifest(runfile, tool_dir=None):
    if tool_dir is None:
        tool_dir = Path(runfile).parent
    name = Path(runfile).parent.name
    create_argument_parser(runfile).generate_manifest(tool_dir, name)

if __name__ == '__main__':
    create_manifest()
