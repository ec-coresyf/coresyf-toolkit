#!/usr/bin/env python
import os

from gpt_coresyf_tool import GPTCoReSyFTool

TOOL_DEF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'coresyf_calibration_tool.json')

if __name__ == '__main__':
    TOOL = GPTCoReSyFTool(TOOL_DEF_FILE)
    TOOL.execute()
