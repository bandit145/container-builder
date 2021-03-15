from container_builder.src.config import Config

CONFIG_FILE = "tests/data/info.json"


def test_config():
    config = Config()
    conf = config.read_file(CONFIG_FILE)
    new_conf = config.validate(conf)
    assert new_conf["capabilities"] == []
    assert new_conf["repo"] == "quay.io/bandit145/dnsmasq"
