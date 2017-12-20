#!/usr/bin/env python
import os
from os import mkdir, rename, listdir
from os.path import join, basename, splitext
from glob import glob
from shutil import copy, make_archive


def prepare_tool(output_dir, name, run_file, manifest_file):
    tool_dir = join(output_dir, name)
    mkdir(tool_dir)
    copy(run_file, join(tool_dir, 'run'))
    copy(manifest_file, join(tool_dir, 'manifest.json'))
    make_archive(tool_dir, 'zip', tool_dir)


def prepare_toolkit(toolkit_dir, output_dir):
    run_file = join(toolkit_dir, 'run.py')
    manifests = [join(toolkit_dir, file)
                 for file in listdir(toolkit_dir) if file.endswith('.json')]
    for manifest_file in manifests:
        tool_name = splitext(basename(manifest_file))[0]
        prepare_tool(output_dir, tool_name, run_file, manifest_file)


if __name__ == '__main__':
    prepare_toolkit('./src/gpt_toolkit', './target')