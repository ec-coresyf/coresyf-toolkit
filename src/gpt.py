import subprocess


def parameter(prefix, value):
    f = ("-%s=\"%s\"" if isinstance(value, basestring) else "-%s=%s")
    return f % (prefix, value)


def call_gpt(operator, source, target, options):
    # ------------------------------------#
    # Building gpt command line #
    # ------------------------------------#
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
    except Exception, message:
        print(str(message))
        # sys.exit(1)  # or sys.exit(process.returncode)