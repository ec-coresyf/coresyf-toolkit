import sys
import os

import shutil

import zipfile

import logging

from manifest import get_manifest
from argument_parser import CoReSyFArgumentParser

TMP_DIR = os.path.abspath("tmp")


class NoOutputFile(Exception):

    def __init__(self, file):
        super(NoOutputFile, self).__init__()
        self.file = file


class EmptyOutputFile(Exception):

    def __init__(self, file):
        super(EmptyOutputFile, self).__init__()
        self.file = file


class CoReSyFTool(object):

    MANIFEST_FILE_NAME = 'manifest.json'

    def __init__(self, run_script_file_name):
        self.context_directory = self._get_context_directory(
            run_script_file_name)
        self.manifest_file_name = os.path.join(
            self.context_directory, self.MANIFEST_FILE_NAME)
        self.manifest = get_manifest(self.manifest_file_name)
        self.arg_parser = CoReSyFArgumentParser(self.manifest)
        self.operation = self.manifest.get('operation', {})
        self._validate_operation(self.operation)

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
        self.logger.info('Cleaning temporary data.')
        self._clean_tmp_()

    def _check_outputs(self):
        for out_arg in self.arg_parser.outputs:
            output = self.bindings[out_arg]
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
                file_name = arguments[argname]
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

    def run(self, bindings):
        pass
