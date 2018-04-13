import re
import glob
import os
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


#for pyfile in glob.glob('Toolbox/*.py'):
#    create_argument_parser(pyfile).generate_manifest(os.path.splitext(os.path.basename(pyfile))[0])

for pyfile in glob.glob('../SAR_*/run'):
    name = Path(pyfile).parent.name
    create_argument_parser(pyfile).generate_manifest(name)