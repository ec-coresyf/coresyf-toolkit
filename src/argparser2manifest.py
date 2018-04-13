import json

class ArgumentParser:

    def __init__(self, *args, **kwargs):
        self.args = {}

    def __getattr__(self, name):
        pass

    def add_argument(self, *opts, **kwargs):
        longest_opts = max(opts, key=len)
        _id = longest_opts[2:]
        self.args[_id] = kwargs

    def manifest(self):
        manifest = {
            "inputs": [],
            "parameters": [],
            "outputs": []
        }
        for _id, arg in self.args.items():
            entry = {
                    "identifier": _id,
                    "name": _id,
                    "description": arg['help'],
            }
            if 'input' in _id or 'output' in _id:
                entry['collection'] = arg['nargs'] != 1
            if 'input' in _id: 
                manifest['input'].append(entry)
            elif 'output' in _id:
                manifest['output'].append(entry)
            else:
                entry['default'] = arg['default']
                entry['options'] = arg['choices']
                entry['type'] = arg['type']
                manifest['parameter'].append(entry)
            return manifest

    def generate_manifest(self):
        manifest_json = json.dumps(self.manifest())
        manifest_file_name = ""
        with open(manifest_file_name, 'w') as manifest_file:
            manifest_file.write(manifest_json)

