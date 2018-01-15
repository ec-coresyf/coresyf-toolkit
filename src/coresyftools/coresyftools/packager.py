import os
from os import mkdir, rename, listdir
from os.path import join, basename, splitext, exists
from shutil import copy, make_archive


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


class Packager():

    def __init__(self, tool_dir, target_dir):
        self.tool_dir = tool_dir
        self.target_dir = target_dir

    def _check_tool_directory_structure(self):
        if not exists(self.tool_dir):
            raise ToolDirectoryNotFoundException()
        if not exists(self.target_dir):
            raise TargetDirectoryNotFoundException()
        if not exists(join(self.tool_dir, 'run')):
            raise MissingRunFileException()
        if not exists(join(self.tool_dir, 'manifest.json')):
            raise MissingManifestFileException()
        if not exists(join(self.tool_dir, 'examples.sh')):
            raise MissingExamplesFileException()

    def _prepare_tool_dir(self):
        pass

    def _test(self):
        pass

    def _archive(self):
        make_archive(self.tool_dir, 'zip', self.tool_dir)

    def pack_tool(self):
        self._check_tool_directory_structure()
        self._test()
        self._prepare_tool_dir()
        self._archive()
