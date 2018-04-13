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
                    "description": arg.get('help', ''),
            }
            if 'input' in _id or 'output' in _id:
                entry['collection'] = 'nargs' in arg and arg['nargs'] != 1
            if 'input' in _id: 
                manifest['inputs'].append(entry)
            elif 'output' in _id:
                manifest['outputs'].append(entry)
            else:
                if 'default' in arg:
                    entry['default'] = arg['default']
                if 'choices' in arg:
                    entry['options'] = arg['choices']
                if 'type' in arg:
                    entry['type'] = arg['type']
                manifest['parameters'].append(entry)
        return manifest

    def generate_manifest(self, tool_name):
        manifest_json = json.dumps(self.manifest(), indent=4)
        manifest_file_name = tool_name + '.manifest.json'
        with open(manifest_file_name, 'w') as manifest_file:
            manifest_file.write(manifest_json)

