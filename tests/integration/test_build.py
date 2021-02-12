from builder.src.build import Build
from builder.src.strategies import Strategy
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
    img = build.build(conf["repo"] + conf["tag"], "doh")
    os.chdir(cwd)
    assert img.tags[0] == conf["repo"] + conf["tag"]


def test_test():
    cwd = os.getcwd()
    os.chdir("tests/containers")
    conf = import_config("doh/info.json")
    tests = import_config("doh/test.json")
    build = Build(logging, "TEST_USER_NAME", "TEST_USER_PASS")
    img = build.build(conf["repo"] + conf["tag"], "doh")
    build.test(conf["repo"] + conf["tag"], None, tests)
    os.chdir(cwd)


def test_tags():
	build = Build(logging, "TEST_USER_NAME", "TEST_USER_PASS")
	assert '2.6.0' in build.get_repo_tags('quay.io/prometheus/prometheus')
