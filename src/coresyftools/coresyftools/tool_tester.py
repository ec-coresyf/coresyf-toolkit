import sys
import os
import logging
import subprocess
import requests
import json
import glob
from urlparse import urlparse
from os.path import exists, getsize
from argument_parser import CoReSyFArgumentParser
from manifest import get_manifest, find_manifest_files

DOWNLOAD_TIMEOUT = 30
SCHIHUB_DOMAIN = 'https://scihub.copernicus.eu'

class InvalidInputSource(Exception):
    
    def __init__(self, source_url):
        self.source_url = source_url

class InvalidCommandException(Exception):
    pass


class ExampleTitleMissingException(Exception):
    pass


class ExampleDescriptionMissingException(Exception):
    pass


class ToolExampleCommand(object):

    def __init__(self, manifest, title, description, command):
        self.title = title
        self.description = description
        self.command = command
        self.manifest = manifest
        self._parse_arguments()

    def _parse_arguments(self):
        self.arg_parser = CoReSyFArgumentParser(self.manifest)
        args = self.command[1:]
        self.arg_parser.parse_arguments(args)
        self.outputs = [self.arg_parser.bindings[arg] for arg in
                        self.arg_parser.outputs]

    def run(self):
        proc = subprocess.Popen(self.command, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return (proc.returncode, stdout, stderr)

    def __str__(self):
        return ' '.join(self.command)

class ToolTester(object):

    def __init__(self, tool_dir, scihub_credentials):
        self.logger = logging.getLogger()
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.setLevel(logging.DEBUG)
        self.tool_dir = tool_dir
        self.scihub_credentials = scihub_credentials
        self.cwd = os.getcwd()
        examples_file = 'examples.sh'
        self.manifest_file_name = find_manifest_files(tool_dir)[0]
        self.manifest = get_manifest(self.manifest_file_name)
        self._load_examples_file(examples_file)
        self.errors = []
        self.log = {}
        self.configurations = {}

    def _load_examples_file(self, file_name):
        cwd = self.change_to_tool_dir()
        try:
            with open(file_name) as examples_file:
                self.input_mappings = {}
                self.example_commands = []
                title = None
                description = ''
                line_number = 0
                for line in examples_file:
                    self.logger.debug('Read line %s.', line)
                    if not line.strip():
                        continue
                    if self._is_comment(line):
                        if not title:
                            title = self._extract_comment_content(line)
                        else:
                            description += self._extract_comment_content(line)
                    elif self._is_input_mapping(line):
                        file_name, url = self._extract_input_mapping(line)
                        self.logger.debug('Read input mapping %s to %s.',
                                          file_name, url)
                        self.input_mappings[file_name] = url
                    else:
                        self._load_example(line_number, title, description,
                                           line)
                        title = None
                        description = ''
                    line_number += 1
        finally:
            os.chdir(cwd)

    def _extract_input_mapping(self, line):
        file_name, url_str = self._without_newline_separator(line).split('=')
        self._ensures_is_from_schihub(url_str)
        url = self._unquote_str(url_str)
        return (file_name, url)

    def _is_input_mapping(self, line):
        return '=' in line

    def _ensures_is_from_schihub(self, url):
        if url.startswith(SCHIHUB_DOMAIN):
            raise InvalidInputSource(url)

    def _unquote_str(self, _str):
        return _str[1:-1]

    def _without_newline_separator(self, line):
        return line[:-1]

    def _extract_comment_content(self, comment_line):
        # remember the comments start with a '#' character and end with a
        # new line separator
        return comment_line[1:-1]

    def _load_example(self, line_number, title, description, line):
        if not title:
            raise ExampleTitleMissingException(line_number)
        if not description:
            raise ExampleDescriptionMissingException(line_number)
        self.example_commands.append(
            ToolExampleCommand(self.manifest, title, description,
                               line.split()))

    def _is_comment(self, line):
        return line.startswith('#')

    def _byte_to_str(self, _bytes):
        return _bytes.decode('utf-8')[1:-1]

    def _output_errors(self, command):
        for output in command.outputs:
            self.logger.debug('Checking for output %s', output)
            if not exists(output):
                return NoOutputFile(output)
            if not getsize(output) > 0:
                return EmptyOutputFile(output)

    def change_to_tool_dir(self):
        self.cwd = os.getcwd()
        os.chdir(self.tool_dir)
        return self.cwd

    def _test_case(self, command):
        returncode, stdout, stderror = command.run()
        self.log[command] = stdout
        if returncode:
            self.errors.append(NonZeroReturnCode(returncode,
                                self._byte_to_str(stderror)))
        elif stderror:
            self.errors.append(NonEmptyStderr(stderror))
        else:
            output_error = self._output_errors(command)
            if output_error:
                self.errors.append(output_error)

    def _log_command_details(self, command):
        self.logger.info(command.title)
        self.logger.info(command.description)
        self.logger.info('Running %s', str(command))

    def test(self):
        self._download_inputs()
        """Test the tool with the provided invokation command examples."""
        cwd = self.change_to_tool_dir()
        for command in self.example_commands:
            self._log_command_details(command)
            self._test_case(command)
        os.chdir(cwd)

    def _download_inputs(self):
        for file_name, url in self.input_mappings.items():
            if not os.path.exists(file_name):
                self.logger.info('Downloading "%s" from "%s".', file_name, url)
                self._download_input(os.path.join(self.cwd, file_name), url,
                                     self.scihub_credentials)

    def _download_input(self, file_name, url, credentials):
        response = requests.get(url, auth=credentials, stream=True,
                                timeout=DOWNLOAD_TIMEOUT)
        with open(file_name, "a+") as input_file:
            for chunk in response.iter_content(chunk_size=1024):
                input_file.write(chunk)

class TestFailure(Exception):
    pass


class NonZeroReturnCode(TestFailure):

    def __init__(self, returncode, stderror):
        self.returncode = returncode
        self.stderr = stderror

    def __str__(self):
        return '({}, {})'.format(self.returncode, self.stderr)


class NonEmptyStderr(TestFailure):

    def __init__(self, stderror):
        self.message = stderror

    def __str__(self):
        return self.message


class NoOutputFile(TestFailure):

    def __init__(self, file):
        self.file = file


class EmptyOutputFile(TestFailure):

    def __init__(self, file):
        self.file = file