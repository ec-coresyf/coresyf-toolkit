import logging
import os
import shutil
import string
import sys
import zipfile

from argument_parser import CoReSyFArgumentParser
from manifest import get_manifest
from sarge import Capture, run, shell_format

TMP_DIR = os.path.abspath('tmp')

class MissingCommandPlaceholderForOption(Exception):

    def __init__(self, option_identifier):
        super(MissingCommandPlaceholderForOption, self).__init__(
            'Identifier {} was defined, but not used in the command template.'
            .format(option_identifier)
        )
        self.option_identifier = option_identifier

class UnexpectedCommandPlaceholder(Exception):

    def __init__(self, placeholder):
        super(UnexpectedCommandPlaceholder, self).__init__(
            '''Found {} in command template. However it is not a defined input,
            output or parameter identifier.'''.format(placeholder))
        self.placeholder = placeholder


class NoOutputFile(Exception):

    def __init__(self, file):
        super(NoOutputFile, self).__init__()
        self.file = file


class EmptyOutputFile(Exception):

    def __init__(self, file):
        super(EmptyOutputFile, self).__init__()
        self.file = file


MANIFEST_FILE_NAME = 'manifest.json'

class CoReSyFTool(object):

    def __init__(self, run_script_file_name, manifest_file_name=MANIFEST_FILE_NAME):
        self.context_directory = self._get_context_directory(
            run_script_file_name)
        self.manifest_file_name = os.path.join(
            self.context_directory, manifest_file_name)
        self.manifest = get_manifest(self.manifest_file_name)
        self.arg_parser = CoReSyFArgumentParser(self.manifest)
        if 'command' in self.manifest:
            self._validate_command(self.manifest['command'])
        self.operation = self.manifest.get('operation', {})
        self._validate_operation(self.operation)

    def _validate_command(self, command):
        placeholders = self._extract_command_placeholders(command)
        for placeholder in placeholders:
            if placeholder not in self.arg_parser.identifiers:
                raise UnexpectedCommandPlaceholder(placeholder)
        for identifier in self.arg_parser.identifiers:
            if identifier not in placeholders:
                raise MissingCommandPlaceholderForOption(identifier)

    def _extract_command_placeholders(self, command_template):
        formatter = string.Formatter()
        return set([field_name for
                    literal_text, field_name, format_spec, conversion in
                    formatter.parse(command_template)])

    # Manifests 'operation' field is intended for specifying behavior aspects
    # for CoReSyFTool specializations (i.e. subclasses).
    # For example, GPTCoReSyFTool use it for specifying the GPT operation or
    # if a GPT graph is to be used.
    # This method, which is called during __init__, is supposed to be
    # overridden by subclasses, in order to extend manifest validation
    # according to operation logics of specializations.
    def _validate_operation(self, operation_dict):
        return (True, [])

    def _parse_args(self, args=None):
        self.arg_parser.parse_arguments(args)
        self.bindings = self.arg_parser.bindings
        self.logger = logging.getLogger(CoReSyFTool.__name__)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.logger.setLevel(logging.DEBUG)

    def _get_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.INFO)
        return logger

    def _get_context_directory(self, run_script_file_name):
        return os.path.dirname(
            os.path.abspath(run_script_file_name))
        
    def get_temporary_directory(self):
        os.mkdir(TMP_DIR)
        return TMP_DIR

    def execute(self, args=None):
        self._parse_args(args)
        self.logger.info('Executing.')
        self.logger.debug('Bindings: %s', str(self.bindings))
        self.logger.info('Preparing inputs.')
        self._prepare_inputs_(self.bindings)
        self.logger.info('Running.')
        self.run(self.bindings)
        self._check_outputs()
        self.prepare_outputs()
        self.logger.info('Cleaning temporary data.')
        self._clean_tmp_()

    def _check_outputs(self):
        for out_arg in self.arg_parser.outputs:
            outputs = self.bindings[out_arg]
            if not hasattr(outputs, '__iter__'):
                outputs = [outputs]
            for output in outputs:
                if not os.path.exists(output):
                    raise NoOutputFile(output)
                elif not os.path.getsize(output) > 0:
                    raise EmptyOutputFile(output)

    def _unzip_file_(self, file_name):
        extracted_files = None
        self.logger.debug('Trying to unzip %s.', file_name)
        if zipfile.is_zipfile(file_name):
            self.logger.info('Extracting %s .', file_name)
            archive = zipfile.ZipFile(file_name, 'r')
            if not archive.infolist():
                self.arg_parser.arg_parser.error(
                    "Input zip file '{}' is empty.".format(file_name))
            archive.extractall(TMP_DIR)
            archive.close()
            extracted_files = [os.path.join(TMP_DIR, f)
                               for f in os.listdir(TMP_DIR)]
        return extracted_files

    def _prepare_inputs_(self, arguments):
        for argname in self.arg_parser.inputs:
            if argname in arguments and arguments[argname]:
                files = arguments[argname]
                if not hasattr(files, '__iter__'):
                    files = [files]
                for file_name in files:
                    if not os.path.exists(file_name):
                        self.arg_parser.arg_parser.error(
                            "{} does not exists.".format(file_name))
                    else:
                        extracted_files = self._unzip_file_(file_name)
                        if extracted_files:
                            self.bindings[argname] = extracted_files[0]

    def _clean_tmp_(self):
        if os.path.isdir(TMP_DIR):
            shutil.rmtree(TMP_DIR)

    def _run_command(self, command_template):
        self.logger.debug('Command: %s', str(command_template))
        self.invoke_shell_command(command_template, **self.bindings)

    def run(self, bindings):
        self.logger.info('Running command...')
        if 'command' in self.manifest:
            self._run_command(self.manifest['command'])

    def invoke_shell_command(self, fmt, **kwargs):
        cmd_str = shell_format(fmt, **kwargs)
        stdout_capture = Capture()
        stderr_capture = Capture()
        pipeline = run(cmd_str, stdout=stdout_capture, stderr=stderr_capture)
        return (pipeline, stdout_capture, stderr_capture)

    def prepare_outputs(self):
        """
        Method that checks if the tools' outputs are in a directory.
        If yes, it calls another method to compress. If not, it does nothing.
        """
        for out_arg in self.arg_parser.outputs:
            outputs = self.bindings[out_arg]
            if not hasattr(outputs, '__iter__'):
                outputs = [outputs]
            for output in outputs:
                if os.path.isdir(output):
                    self.write_to_zipfile(output)

    def write_to_zipfile(self, directory):
        """
        Creates a ZipFile with the files in 'directory'.
        """
        path = os.path.abspath(directory)
        # we need to change the name of the output directory to avoid conflicts
        # with the zip archive name without the '.zip' extension
        output_path = path + '_'
        os.rename(path, output_path)
        files_list = os.listdir(output_path)
        with zipfile.ZipFile(path, 'w') as archive:
            for file_ in files_list:
                archive.write(os.path.join(output_path, file_), file_)
            archive.close()


