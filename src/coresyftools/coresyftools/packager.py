#!/usr/bin/python2
from os import listdir
from os.path import join, exists
from zipfile import ZipFile
from tool_tester import ToolTester
from argument_parser import CoReSyFArgumentParser
from manifest import get_manifest, find_manifest_files

import click


class ToolDirectoryNotFoundException(Exception):
    pass


class TargetDirectoryNotFoundException(Exception):
    pass


class MissingRunFileException(Exception):
    pass


class MissingManifestFileException(Exception):
    pass


class MissingExamplesFileException(Exception):
    pass

class MultipleManifestFileException(Exception):
    pass

class ToolErrorsException(Exception):

    def __init__(self, errors):
        self.errors = errors


class Packager():

    def __init__(self, tool_dir, target_dir, scihub_credentials):
        self.tool_dir = tool_dir
        self.target_dir = target_dir
        self.scihub_credentials = scihub_credentials
        self.manifest = None

    def _check_tool_directory_structure(self):
        if not exists(self.tool_dir):
            raise ToolDirectoryNotFoundException()
        if not exists(self.target_dir):
            raise TargetDirectoryNotFoundException()
        if not exists(join(self.tool_dir, 'run')):
            raise MissingRunFileException()
        manifest_files = find_manifest_files(self.tool_dir)
        if not manifest_files:
            raise MissingManifestFileException()
        if len(manifest_files) > 1:
            raise MultipleManifestFileException()
        if not exists(join(self.tool_dir, 'examples.sh')):
            raise MissingExamplesFileException()
    
    def _read_manifest(self):
        manifest_file_name = find_manifest_files(self.tool_dir)[0]
        self.manifest = get_manifest(manifest_file_name)

    def _test(self):
        tester = ToolTester(self.tool_dir, self.scihub_credentials)
        tester.test()
        if tester.errors:
            raise ToolErrorsException(tester.errors)

    def _archive(self):
        files_to_exclude = self._get_input_output_names()
        with ZipFile(join(self.target_dir, self.manifest['name']) + '.zip',
                     'w') as tool_archive:
            for file_ in listdir(self.tool_dir):
                if file_ not in files_to_exclude:
                    tool_archive.write(join(self.tool_dir, file_), file_)
            tool_archive.close()

    def _get_input_output_names(self):
        arg_parser = CoReSyFArgumentParser(self.manifest)
        args = self._get_command()[1:]
        arg_parser.parse_arguments(args)
        inputs = [arg_parser.bindings[argin] for argin in arg_parser.inputs]
        outputs = [arg_parser.bindings[argout] for argout in
                   arg_parser.outputs]
        return inputs + outputs

    def _get_command(self):
        with open(join(self.tool_dir, 'examples.sh')) as examples_file:
            for line in examples_file:
                if line.startswith('./'):
                    command = line.split()
            examples_file.close()
        return command

    def pack_tool(self):
        self._check_tool_directory_structure()
        self._read_manifest()
        self._test()
        self._archive()


@click.command()
@click.option('--tool_dir', type=click.Path(), default='.')
@click.option('--target_dir', type=click.Path(), default='..')
@click.option('--scihub_user')
@click.option('--scihub_pass')
def pack_tool(tool_dir, target_dir, scihub_user, scihub_pass):
    click.echo('Packaging {} to {}..'.format(tool_dir, target_dir))
    try:
        packager = Packager(tool_dir, target_dir, (scihub_user, scihub_pass))
        packager.pack_tool()
    except ToolErrorsException as tool_errors:
        for error in tool_errors.errors:
            click.echo('Packaging error: {}'.format(error), err=True)
    else:
        click.echo('Packaging finished.')

if __name__ == '__main__':
    pack_tool()
