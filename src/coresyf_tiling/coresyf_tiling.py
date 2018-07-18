#!/usr/bin/python2
import os
import glob
from coresyftools.gpt_tool import GPTCoReSyFTool


class IncorrectOutputNumber(Exception):
    """Exception thrown when the number of outputs is different from the
    expected one."""
    def __init__(self, found_outputs, expected_value):
        message = ('Number of found outputs: "{}"! ' +
                   'Expected number of outputs "{}"')
        super(IncorrectOutputNumber, self).__init__(
                    message.format(found_outputs, expected_value))


class CoresyfTiling(GPTCoReSyFTool):

    def create_temp_bindings(self, bindings):
        '''
        Creates a temporary bindings for executing the SNAP TileWriter operator,
        namely the list of 'Ttarget' output file paths is replaced by one base
        output path. The "TileWriter" uses this base output path to create the
        tiles (example: /dirpath/base_tile_name_1, /dirpath/base_tile_name_2...)
        :param dict bindings: containning the tool bindings.
        :param dict bindings_temp: the bindings containing the base output path.
        '''
        bindings_temp = bindings.copy()
        temp_target_base = os.path.dirname(bindings['Ttarget'][0]) + "out_tile"
        bindings_temp['Ttarget'] = temp_target_base
        return bindings_temp

    def rename_output_tiles(self, tile_pattern_name, dest_tile_names):
        '''
        Renames all files matching the provided pattern to the names included
        in the list of destination pathnames.
        :param str tile_pattern_name: string containing the pathname pattern.
        :param list dest_tile_names: list of destination pathnames.
        '''
        output_list = glob.glob(tile_pattern_name + '*')
        dir_path = os.path.dirname(tile_pattern_name)
        if len(output_list) != len(dest_tile_names):
            raise IncorrectOutputNumber(len(output_list), len(dest_tile_names))
        for n in range(len(output_list)):
            os.rename(os.path.join(dir_path, output_list[n]),
                      dest_tile_names[n])

    def _build_gpt_shell_command(self, operator, source, target, options):
        '''
        This function overwrites the one in the superclass, in order to execute
        gpt with the specific TileWriter parameters, replacing the default
        flags "-t" (target) and "-f" (format) as they are only used if the
        graph does not specify its own write operator.
        '''
        source = os.path.abspath(source)
        target = os.path.abspath(target)
        args = ['gpt', operator,
                self._option_str('PformatName', self.DEFAULT_FORMAT),
                self._option_str('PtargetBaseFile', target)]
        args.extend([self._option_str(arg, value)
                     for arg, value in options.items()])
        args.append(source)
        return args

    def run(self, bindings):
        bindings_temp = self.create_temp_bindings(bindings)
        super(CoresyfTiling, self).run(bindings_temp)
        tile_pattern_name = bindings_temp['Ttarget']
        target_names = bindings['Ttarget']
        self.rename_output_tiles(tile_pattern_name, target_names)
