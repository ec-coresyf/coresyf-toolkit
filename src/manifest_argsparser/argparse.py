import json
from pathlib import Path

class ArgumentParser:

    def __init__(self, *args, **kwargs):
        self.args = {}
        self.input_options = set()
        self.output_options = set()

    def __getattr__(self, name):
        pass
    
    def get_arguments_list(self):
        for _id, arg in self.args.items():
            yield (_id, arg['help'])
    
    def set_inputs(self, inputs):
        self.input_options = set(inputs)
    
    def set_outputs(self, outputs):
        self.output_options = set(outputs)

    def add_argument(self, *opts, **kwargs):
        longest_opts = max(opts, key=len)
        _id = longest_opts[2:]
        self.args[_id] = kwargs

    def _entry(self, _id, arg, in_out=False):
        entry = {
                "identifier": _id,
                "name": _id,
                "description": arg.get('help', ''),
        }
        if in_out:
           entry['collection'] = arg.get('nargs') != 1
        return entry

    def manifest(self):
        manifest = {
            "inputs": [],
            "parameters": [],
            "outputs": []
        }
        for _id in self.input_options:
            arg = self.args[_id]
            manifest['inputs'].append(self._entry(_id, arg, True))
        for _id in self.output_options:
            arg = self.args[_id]
            manifest['outputs'].append(self._entry(_id, arg, True))
        outputs = set(self.args.keys()) - self.input_options - self.output_options
        for _id in outputs:
            arg = self.args[_id]
            entry = self._entry(_id, arg) 
            if 'default' in arg:
                entry['default'] = arg['default']
            if 'choices' in arg:
                entry['options'] = arg['choices']
            if 'type' in arg:
                entry['type'] = arg['type']
            manifest['parameters'].append(entry)
        return manifest

  
