import json
import os


class Config:

    schema = {
        "tag": {"required": False},
        "repo": {"required": True},
        "capabilities": {"required": False, "default": []},
    }

    config = None

    def __init__(self):
        pass

    def validate(self, config):
        new_conf = {}
        conf_keys = config.keys()
        for k, v in self.schema.items():
            if v["required"] and k not in conf_keys:
                raise Exception(f"Config missing {k}")
            elif "default" in v.keys() and k not in conf_keys:
                new_conf[k] = v['default']
            else:
                new_conf[k] = config[k]
        return new_conf

    def read_file(self, path):
        if not os.path.exists(path):
            raise Exception(f"{path} does not exist!")
        with open(path, mode="r") as conf:
            config = json.load(conf)
        return config

    def load(self, path):
        self.config = self.validate(self.read_file(path))
        
