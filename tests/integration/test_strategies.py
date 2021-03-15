import builder.src.strategies as strats
import builder.src.repos as repos
from builder.src.build import Build
from builder.src.config import Config
import docker
import logging
import json
import os

GIT_URL = "https://github.com/bandit145/test-repo.git"
REPO_DIR = "/tmp/"
CONTAINER_REPO = "tests/containers/"

def create_client():
    return docker.from_env()


def import_config(file):
    conf = Config()
    conf.load(file)
    return conf.config


def test_remote_tag_strategy():
    strat = strats.Tag(
        repos.TestRepo("/tmp/", **{"url": None, "name": None, "branch": None})
    )
    assert "2.6.0" in strat.get_remote_repo_tags("quay.io/prometheus/prometheus")


def test_local_tag_strategy():
    strat = strats.Tag(repos.Git("/tmp/", **{"url": GIT_URL}))
    strat.repo.update()
    assert len(strat.get_local_repo_tags()) == 2
    assert "1.0.0" in strat.get_local_repo_tags()


def test_tag_strategy():
    client = create_client()
    config = import_config("tests/containers/doh-tag-strat/info.json")
    TEST_TAG1 = f"{config['repo']}:2.2.3"
    TEST_TAG2 = f"{config['repo']}:2.2.4"
    TEST_TAG3 = f"{config['repo']}:latest"
    build = Build(logging, "fake_docker", "fake_docker")
    repo = repos.Git("/tmp/", **config["src"]["args"])
    repo.update()
    strat = strats.Tag(repo)
    cwd = os.getcwd()
    os.chdir(CONTAINER_REPO)
    strat.execute("doh-tag-strat", build=build, config=config)
    os.chdir(cwd)
    #get all built images tags
    tags = [x.tags[0] for x in client.images.list(config['repo'])]
    assert TEST_TAG1 in tags
    assert TEST_TAG2 in tags
    # test that if I boot the 2.0.0 one the code version is that
    cont1 = client.containers.run(TEST_TAG1, detach=True)
    cont2 = client.containers.run(TEST_TAG2, detach=True)
    cont3 = client.containers.run(TEST_TAG3, detach=True)
    code, out = cont1.exec_run('doh-server -version')
    assert '2.2.3' in str(out)
    code, out = cont2.exec_run('doh-server -version')
    assert '2.2.4' in str(out)
    cont1.remove(force=True)
    cont2.remove(force=True)
    cont3.remove(force=True)


def test_branch_strategy():
    client = create_client()
    config = import_config("tests/containers/doh-branch-strat/info.json")
    build = Build(logging, "fake_docker", "fake_docker")
    repo = repos.Git("/tmp/", **config["src"]["args"])
    repo.update()
    strat = strats.Branch(repo)
    cwd = os.getcwd()
    os.chdir(CONTAINER_REPO)
    strat.execute("doh-branch-strat", build=build, config=config)
    os.chdir(cwd)
    cont = client.containers.run(f"{config['repo']}:latest", detach=True)
    code, out = cont.exec_run('doh-server -version')
    assert '2.0.0' in str(out)
    cont.remove(force=True)
    