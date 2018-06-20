#!/usr/bin/python2
from coresyftools.tool import CoReSyFTool


class IncorrectRanges(Exception):
    """Exception thrown when the text file contains incorrect ranges."""
    def __init__(self, range_values):
        message = ('Incorrect range: "{}"! ' +
                   'Use a text file with valid range format! Example:\n' +
                   '0 - 5 : 1\n' +
                   '6 - 9 : 3')
        super(IncorrectRanges, self).__init__(message.format(range_values))


def create_gdal_calc_expression(file_path):
    '''
    It opens a text file with the correspondence between the input and output
    classes and returns a string with a gdal_calc expression representing the
    logic of the data transformation.
    :param str file_path: path of the text file.
    '''
    with open(file_path) as file_classes:
        content = file_classes.readlines()
    interval_list = [x.strip() for x in content]

    ranges_exp = ''
    try:
        for interval in interval_list:
            part_exp = ''
            min_val, max_val = interval.split(':')[0].split("-")
            final_value = int(interval.split(':')[-1])
            if min_val:
                min_val = int(min_val)
                part_exp += '(A>={})'.format(min_val)
            if max_val:
                max_val = int(max_val)
                if part_exp:
                    part_exp += '*'
                part_exp += '(A<={})'.format(max_val)

            part_exp = '{}*({})'.format(final_value,
                                        part_exp)     # 2*((A>=0)*(A<=6))
            if ranges_exp:
                ranges_exp += ' + '
            ranges_exp += part_exp  # 2*((A>=0)*(A<=6)) + 3*((A>=15)*(A<=16))

        ranges_exp = '(' + ranges_exp + ')'
    except ValueError:
        raise IncorrectRanges(interval)
    return ranges_exp


class CoresyfImageReclass(CoReSyFTool):

    def reclassify_image(self, bindings, expression):
        '''
        Reclassifies an input raster ('Ssource') by running gdal_cal with the
        expression representing the logic of the data transformation.
        :param dict bindings: containning the following keys and values:
                              - 'Ssource' - input raster path;
                              - 'Ttarget' - output raster path;
                              - 'NoDataValue' - output no data value.
        :param str expression: expression to be executed.
        '''
        command_template = 'gdal_calc.py --calc="{}"'.format(expression)
        command_template += ' -A {Ssource} --outfile={Ttarget}'
        command_template += ' --NoDataValue={NoDataValue}'
        self.logger.debug('Command: %s', str(command_template))
        self.invoke_shell_command(command_template, **bindings)

    def run(self, bindings):
        filepath_classes = bindings['Sclass']
        gdal_cal_exp = create_gdal_calc_expression(filepath_classes)
        self.reclassify_image(bindings, gdal_cal_exp)
