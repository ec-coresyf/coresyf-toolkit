'''Defines a CoReSyF Tool consisting of a SNAP single gpt operation.'''
import os
import subprocess
import re
from coresyf_tool_base import CoReSyFTool


class GPTExecutionException(Exception):
    '''Error occurred during a SNAP gpt execution'''

    ERROR_REGEX = re.compile('Error:')

    def __init__(self, returncode, msg):
        self.returncode = returncode
        self.errors = [line[7:] for line in msg.split(
            os.linesep) if self.ERROR_REGEX.match(line)]
        super(GPTExecutionException, self).__init__(self.errors)


class GPTCoReSyFTool(CoReSyFTool):
    '''CoReSyF Tool consisting of a single SNAP gpt operation.'''

    DEFAULT_FORMAT = 'GeoTIFF'
    DEFAULT_EXT = 'tif'

    def _get_manifest_schema(self):
        manifest_schema = super(GPTCoReSyFTool, self)._get_manifest_schema()
        manifest_schema['operation'] = {
            'type': 'string',
            'required': True
        }
        return manifest_schema

    def run(self, bindings):
        operation = self.manifest['operation']
        source = bindings.pop('Ssource')
        target = bindings.pop('Ttarget')
        self._call_gpt(operation, source, target, bindings)
        # This is needed because SNAP automatically adds file extensions, but
        # output files can not have a name different from the specified in
        # the command line.
        self._remove_snap_file_extension(target)

    def _call_gpt(self, operator, source, target, options):
        source = os.path.abspath(source)
        target = os.path.abspath(target)
        args = ['gpt', operator, '-f', self.DEFAULT_FORMAT,
                '-t', target]
        args.extend([self._option_str(arg, value)
                     for arg, value in options.items()])
        args.append(source)
        self._get_logger().info('calling GPT: %s', ' '.join(args))
        self._call_shell_command(args)

    def _option_str(self, prefix, value):
        return ('-{}={}' if isinstance(value, basestring) else '-{}={}').format(prefix, str(value))

    def _call_shell_command(self, args):
        process = subprocess.Popen(args,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        # Reads the output and waits for the process to exit before returning
        stdout, stderr = process.communicate()
        self._get_logger().debug(stderr)
        if process.returncode:
            raise GPTExecutionException(process.returncode, stderr)

    def _remove_snap_file_extension(self, target):
        gpt_file_name = target + '.' + self.DEFAULT_EXT
        if os.path.exists(gpt_file_name):
            os.rename(gpt_file_name, target)
