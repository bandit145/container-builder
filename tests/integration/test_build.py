from builder.src.build import Build
from builder.src.strategies import MockStrat
import json
import os
import logging


def import_config(file):

    with open(file, "r") as conf:
        return json.load(conf)


def test_build():
    cwd = os.getcwd()
    os.chdir("tests/containers")
    conf = import_config("doh/info.json")
    build = Build(logging, "TEST_USER_NAME", "TEST_USER_PASS")
    img = build.build(f'{conf["repo"]}:latest', "doh")
    os.chdir(cwd)
    assert img.tags[0] == f'{conf["repo"]}:latest'


def test_test():
    cwd = os.getcwd()
    os.chdir("tests/containers")
    conf = import_config("doh/info.json")
    tests = import_config("doh/test.json")
    build = Build(logging, "TEST_USER_NAME", "TEST_USER_PASS")
    img = build.build(f'{conf["repo"]}:latest', "doh")
    build.test(f'{conf["repo"]}:latest', None, tests)
    os.chdir(cwd)
