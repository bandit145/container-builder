import json
import os
from container_builder.src.exceptions import ConfigException
import container_builder.src.strategies as strats


class Config:

    schema = {
        "repo": {"required": True},
        "capabilities": {"required": False, "default": []},
        "strategy": {"required": True},
        "src": {"required": True},
    }

    config = None

    def __init__(self):
        pass

    def validate(self, config):
        new_conf = {}
        conf_keys = config.keys()
        for k, v in self.schema.items():
            if v["required"] and k not in conf_keys:
                raise ConfigException(f"Config missing {k}")
            elif "default" in v.keys() and k not in conf_keys:
                new_conf[k] = v["default"]
            elif "strategy" == k:
                if not hasattr(strats, config[k]["name"]):
                    raise ConfigException(
                        f"strategy {config[k]['name']} does not exist"
                    )
                strat = getattr(strats, config[k]["name"])
                new_conf[k] = config[k]
                new_conf[k]["args"] = strat.validate_config(
                    config[k]["args"], strat.SCHEMA
                )
            elif k in conf_keys:
                new_conf[k] = config[k]
        return new_conf

    def read_file(self, path):
        if not os.path.exists(path):
            raise ConfigException(f"{path} does not exist!")
        with open(path, mode="r") as conf:
            config = json.load(conf)
        return config

    def load(self, path):
        self.config = self.validate(self.read_file(path))
