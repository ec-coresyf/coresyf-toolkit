import sys
import os
import logging
import subprocess
from coresyf_tool_base import CoReSyFArgParser, get_manifest


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
        self.arg_parser = CoReSyFArgParser(self.manifest)
        self.arg_parser.parse_arguments(self.command[1:])
        self.outputs = self.arg_parser.outputs

    def run(self):
        proc = subprocess.Popen(self.command, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return (proc.returncode, stdout, stderr)

    def __str__(self):
        return ' '.join(self.command)


def normalize_variable_name(name):
    return name


class ToolTester(object):

    def __init__(self, tool_dir):
        os.chdir(tool_dir)
        examples_file = 'examples.sh'
        self.manifest_file_name = 'manifest.json'
        self.manifest = get_manifest(self.manifest_file_name)
        self._load_examples_file(examples_file)
        self.logger = logging.getLogger()
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.setLevel(logging.DEBUG)

    def _load_examples_file(self, file_name):
        with open(file_name) as examples_file:
            self.example_commands = []
            title = None
            description = ''
            ln = 0
            for line in examples_file:
                if not line.strip():
                    continue
                if self._is_comment(line):
                    if not title:
                        title = line[1:-1]
                    else:
                        description += line[1:-1]
                elif self._is_valid_command(line):
                    if not title:
                        raise ExampleTitleMissingException(ln)
                    if not description:
                        raise ExampleDescriptionMissingException(ln)
                    self.example_commands.append(
                        ToolExampleCommand(self.manifest, title, description,
                                           line.split()))
                    title = None
                    description = ''
                else:
                    raise InvalidCommandException(line)
                ln += 1

    def _is_comment(self, line):
        return line.startswith('#')

    def _is_valid_command(self, command):
        return True

    def _byte_to_str(self, _bytes):
        return _bytes.decode('utf-8')[1:-1]

    def test(self):
        self.errors = [] 
        self.log = {}
        for command in self.example_commands:
            self.logger.info('################################################################################')
            self.logger.info(command.title)
            self.logger.info(command.description)
            self.logger.info('Running %s', str(command))
            returncode, stdout, stderror = command.run()
            self.log[command] = stdout
            if returncode:
                self.errors.append(NonZeroReturnCode(returncode,
                                   self._byte_to_str(stderror)))
            elif stderror:
                self.errors.append(NonEmptyStderr(self._byte_to_str(stderror)))


class TestFailure():
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
