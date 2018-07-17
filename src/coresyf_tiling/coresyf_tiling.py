#!/usr/bin/python2
from coresyftools.tool import CoReSyFTool


class CustomException(Exception):
    """Exception thrown when the ...."""
    def __init__(self, values):
        message = ('Something is wrong: "{}"! ')
        super(CustomException, self).__init__(message.format(values))


class CoresyfTiling(CoReSyFTool):

    def aux_func(self, bindings, other=''):
        '''
        Description.
        :param dict bindings: description.
        :param str other: description.
        '''

    def run(self, bindings):
        self.aux_func(bindings)
