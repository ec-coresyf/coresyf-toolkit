#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for intercal argument parsing"""

from tools.auxil import create_parser
import os
import pytest

@pytest.fixture()
def cli():
    parser = create_parser()
    return parser

def test_cli_parse_workdir(cli):
    opts = cli.parse_args(['-w', './'])
    assert os.path.exists(opts.workdir)

def test_cli_parse_reffile(cli):
    opts = cli.parse_args(['-r', 'tests/data/isempty.tiff'])
    assert os.path.isfile(opts.reffile)

def test_cli_parse_infile(cli):
    opts = cli.parse_args(['-i', 'tests/data/isempty.tiff'])
    assert os.path.isfile(opts.infile)

def test_cli_parse_shapefile(cli):
    opts = cli.parse_args(['-s', 'tests/data/isempty.tiff'])
    assert os.path.isfile(opts.shp)

def test_cli_default_debug(cli):
    opts = cli.parse_args([])
    assert opts.debug is False

def test_cli_default_type(cli):
    opts = cli.parse_args([])
    assert opts.type == 'irmad'

def test_cli_workdir_notexist(cli):
    with pytest.raises(SystemExit):
        cli.parse_args(['-w', 'notexist'])

def test_cli_reffile_notexist(cli):
    with pytest.raises(SystemExit):
        cli.parse_args(['-r', 'notexist'])

def test_cli_infile_notexist(cli):
    with pytest.raises(SystemExit):
        cli.parse_args(['-i', 'notexist'])

def test_cli_shapefile_notexist(cli):
    with pytest.raises(SystemExit):
        cli.parse_args(['-s', 'notexist'])

def test_cli_type_notexist(cli):
    with pytest.raises(SystemExit):
        cli.parse_args(['-t', 'notexist'])

def test_cli_debug_is_set(cli):
    opts = cli.parse_args(['--debug'])
    assert opts.debug is True

def test_cli_band_is_default(cli):
	opts = cli.parse_args(['--bands'])
	assert opts.bands == []

def test_cli_band_1_arg(cli):
	opts = cli.parse_args(['--bands', '1'])
	assert opts.bands == [1]

def test_cli_band_2_args(cli):
	opts = cli.parse_args(['--bands','1','2'])
	assert opts.bands == [1, 2]	

def test_cli_band_3_args(cli):
	opts = cli.parse_args(['--bands','1','2','3'])
	assert opts.bands == [1, 2, 3]		

def test_cli_band_4_args(cli):
	opts = cli.parse_args(['--bands','2','3','4','8'])
	assert opts.bands == [2, 3, 4, 8]	

