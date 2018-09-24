'''Defines a CoReSyF Tool consisting of a SNAP single gpt operation.'''
import os
import subprocess
import re
from tool import CoReSyFTool
from manifest import InvalidManifestException


class TooManyInputArgumentsException(Exception):
    pass


class TooManyOutputArgumentsException(Exception):
    pass


class GPTExecutionException(Exception):
    """Error occurred during a SNAP gpt execution."""

    ERROR_REGEX = re.compile('Error:')

    def __init__(self, returncode, msg):
        self.returncode = returncode
        self.errors = [line[7:] for line in msg.split(
            os.linesep) if self.ERROR_REGEX.match(line)]
        super(GPTExecutionException, self).__init__(self.errors)


class GPTGraphFileNotFound(Exception):
    pass


class GPTCoReSyFTool(CoReSyFTool):
    '''CoReSyF Tool consisting of a single SNAP gpt operation.'''

    DEFAULT_FORMAT = 'GeoTIFF-BigTIFF'
    TIF_EXT = 'tif'
    DEFAULT_GPT_GRAPH_FILE_NAME = 'gpt_graph.xml'
    GEOTIFF_TYPE = 'GeoTIFF'

    def _graph_file_path(self, operation_dict):
        graph_file_name = self.DEFAULT_GPT_GRAPH_FILE_NAME
        if isinstance(operation_dict['graph'], basestring):
            graph_file_name = operation_dict['graph']
        return os.path.join(self.context_directory, graph_file_name)

    # this overrides the super-class method extending it's validation behaviour
    # the method is invoked during super-class __init__
    def _validate_operation(self, operation):
        if 'operation' not in operation and ('graph' not in operation or not
                                             operation['graph']):
            raise InvalidManifestException(
                            'An operation or graph flag should be present.')
        if 'operation' in operation and ('graph' in operation and
                                         operation['graph']):
            raise InvalidManifestException(
                            'Cannot be operation and graph at same time.')
        if self.operation.get('graph') is not None:
            graph_file = self._graph_file_path(operation)
            if not os.path.exists(graph_file):
                raise GPTGraphFileNotFound(graph_file)

    def run(self, bindings):
        #if len(self.arg_parser.inputs) > 1:
        #    raise TooManyInputArgumentsException()
        if len(self.arg_parser.outputs) > 1:
            raise TooManyOutputArgumentsException()

        bindings = bindings.copy()
        operator = self.operation.get('operation')
        if 'graph' in self.operation and self.operation['graph']:
            graph_file = self._graph_file_path(self.operation)
            if not os.path.exists(graph_file):
                raise GPTGraphFileNotFound(graph_file)
            operator = graph_file
        if 'parameters' in self.operation:
            bindings.update(self.operation['parameters'])
        source = bindings.pop(self.arg_parser.inputs[0])
        if self._has_geotiff_source(): 
            source_with_ext = self._add_tif_file_extension(source) 
        else:
            source_with_ext = source
        target = bindings.pop(self.arg_parser.outputs[0])
        self._call_gpt(operator, source_with_ext, target, bindings)
        # Remove source file extension (case it was added)
        if self._has_geotiff_source():
            self._remove_tif_file_extension(source)
        # This is needed because SNAP automatically adds file extensions, but
        # output files can not have a name different from the specified in
        # the command line.
        self._remove_tif_file_extension(target)

    def _has_geotiff_source(self):
        return self._get_source_type() == self.GEOTIFF_TYPE

    def _get_source_type(self):
        return self.manifest['inputs'][0]['type']

    def _build_gpt_shell_command(self, operator, source, target, options):
        source = os.path.abspath(source)
        target = os.path.abspath(target)
        args = ['gpt', operator, '-f', self.DEFAULT_FORMAT,
                '-t', target]
        args.extend([self._option_str(arg, value)
                     for arg, value in options.items()])
        args.append(source)
        return args

    def _call_gpt(self, operator, source, target, options):
        args = self._build_gpt_shell_command(operator, source, target, options)
        self._get_logger().info('calling GPT: %s', ' '.join(args))
        self._call_shell_command(args)

    def _option_str(self, prefix, value):
        return ('-{}={}' if isinstance(value, basestring)
                else '-{}={}').format(prefix, str(value))

    def _call_shell_command(self, args):
        process = subprocess.Popen(args,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        self._get_logger().info(stderr)
        if process.returncode:
            raise GPTExecutionException(process.returncode, stderr)

    def _remove_tif_file_extension(self, target):
        gpt_file_name = target + '.' + self.TIF_EXT
        if os.path.exists(gpt_file_name):
            os.rename(gpt_file_name, target)

    def _add_tif_file_extension(self, source):
        if os.path.exists(source) and self._has_no_tif_extension(source):
            source_with_ext = source + '.' + self.TIF_EXT
            os.rename(source, source_with_ext)
            return source_with_ext
        else:
            return source

    def _has_no_tif_extension(self, file_name):
        return os.path.splitext(str(file_name))[-1] != '.' + self.TIF_EXT