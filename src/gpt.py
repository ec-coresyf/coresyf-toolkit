

'''
This module is used to run the gpt executable in batch-mode.

'''

''' SYSTEM MODULES '''
import os
import subprocess
from coresyf_tool_base import CoReSyFTool

class GPTCoReSyFTool(CoReSyFTool):

    def __init__(self, tool_manifest, gpt_command):
        super(GPTCoReSyFTool, self).__init__(tool_manifest)
        self.gpt_command = gpt_command


    def run(self, bindings):
        source = bindings.pop('Ssource')
        target = bindings.pop('Ttarget')
        call_gpt(self.gpt_command, source, target, bindings)




def parameter(prefix, value):
    f = ("-%s=\"%s\"" if isinstance(value, basestring) else "-%s=%s")
    return f % (prefix, value)


def call_gpt(operator, source, target, options):
    # ------------------------------------#
    # Building gpt command line #
    # ------------------------------------#
    # Create absolute target and source paths 
    source = os.path.abspath(source)
    target = os.path.abspath(target)

    gpt_options = ' '.join([parameter(key, value) for key, value in options.items() if value is not None])
    targetopt = ("-t \"%s\"" % target if target else "")
    gpt_command = "gpt %s -f GeoTIFF %s -Ssource=\"%s\" %s" % (operator, targetopt, source, gpt_options)

    # ------------------------------------#
    #    Run gpt command line   #
    # ------------------------------------#
    print ('\n invoking: ' + gpt_command)
    try:
        process = subprocess.Popen(gpt_command,
                                   shell=True,
                                   #executable='/bin/bash',
                                   #cwd=running_dir,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, )
        # Reads the output and waits for the process to exit before returning
        stdout, stderr = process.communicate()
        print (stdout)
        if stderr:
            raise Exception(stderr)  # or  if process.returncode:
        if 'Error' in stdout:
            raise Exception()
    except Exception as message:
        print(str(message))
        # sys.exit(1)  # or sys.exit(process.returncode)
    
    # Change output name (dummy resolution to solve SNAP bug of automatically adding extension)
    if os.path.exists(target + ".tif"):
        os.rename(target + ".tif", target)
