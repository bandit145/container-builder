from container_builder.src.build import Build
import json
import docker
import os
import logging


def import_config(file):

    with open(file, "r") as conf:
        return json.load(conf)


def create_client():
    return docker.from_env()


def test_build():
    cwd = os.getcwd()
    os.chdir("tests/containers")
    conf = import_config("doh/info.json")
    build = Build(logging, "TEST_USER_NAME", "TEST_USER_PASS")
    build.prep("doh", f"{cwd}/tests/data/")
    img = build.build(f'{conf["repo"]}:latest', "doh")
    build.cleanup("doh")
    os.chdir(cwd)
    assert img.tags[0] == f'{conf["repo"]}:latest'


def test_test():
    client = create_client()
    cwd = os.getcwd()
    os.chdir("tests/containers")
    conf = import_config("doh/info.json")
    tests = import_config("doh/test.json")
    build = Build(logging, "TEST_USER_NAME", "TEST_USER_PASS")
    build.prep("doh", f"{cwd}/tests/data/")
    img = build.build(f'{conf["repo"]}:latest', "doh")
    build.test(f'{conf["repo"]}:latest', None, tests)
    build.cleanup("doh")
    os.chdir(cwd)
    # check that no dangling containers exist
    assert client.images.list(filters={"dangling": True}) == []
    cont = client.containers.run(f'{conf["repo"]}:latest', detach=True)
    code, out = cont.exec_run("doh-server -version")
    # check that right version was built
    assert "2.2.1" in str(out)
