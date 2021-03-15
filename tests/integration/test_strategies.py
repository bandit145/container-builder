import builder.src.strategies as strats
import builder.src.repos as repos
from builder.src.build import Build
from builder.src.config import Config
import docker
import logging
import json
import os

GIT_URL = "https://github.com/bandit145/test-repo.git"
WEIRD_SEMVER_GIT_REPO = "https://gitlab.isc.org/isc-projects/bind9.git"
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
        repos.TestRepo(REPO_DIR, **{"url": None, "name": None, "branch": None})
    )
    assert "2.6.0" in strat.get_remote_repo_tags("quay.io/prometheus/prometheus")


def test_local_tag_strategy():
    strat = strats.Tag(repos.Git(REPO_DIR, **{"url": GIT_URL}))
    strat.repo.update()
    assert len(strat.get_local_repo_tags(None, False)) == 2
    assert "1.0.0" in strat.get_local_repo_tags(None, False)


def test_touched_up_local_tags():
    config = import_config("tests/containers/isc-bind/info.json")
    strat = strats.Tag(repos.Git(REPO_DIR, **{"url": WEIRD_SEMVER_GIT_REPO}))
    strat.repo.update()
    tags = strat.get_local_repo_tags(
        config["strategy"]["args"]["replace_text"],
        config["strategy"]["args"]["force_semver"],
    )
    assert "9.17.0" in tags


def test_tag_strategy():
    client = create_client()
    config = import_config("tests/containers/doh-tag-strat/info.json")
    TEST_TAG1 = f"{config['repo']}:2.2.3"
    TEST_TAG2 = f"{config['repo']}:2.2.4"
    build = Build(logging, "fake_docker", "fake_docker")
    repo = repos.Git(REPO_DIR, **config["src"]["args"])
    repo.update()
    strat = strats.Tag(repo)
    cwd = os.getcwd()
    os.chdir(CONTAINER_REPO)
    strat.execute("doh-tag-strat", build=build, config=config)
    os.chdir(cwd)
    # get all built images tags
    tags = [x.tags[0] for x in client.images.list(config["repo"])]
    assert TEST_TAG1 in tags
    assert TEST_TAG2 in tags
    # test that if I boot the 2.0.0 one the code version is that
    cont1 = client.containers.run(TEST_TAG1, detach=True)
    cont2 = client.containers.run(TEST_TAG2, detach=True)
    code, out = cont1.exec_run("doh-server -version")
    assert "2.2.3" in str(out)
    code, out = cont2.exec_run("doh-server -version")
    assert "2.2.4" in str(out)
    cont1.remove(force=True)
    cont2.remove(force=True)


def test_tag_strategy_with_non_standard_isc_repo():
    client = create_client()
    config = import_config("tests/containers/isc-bind/info.json")
    build = Build(logging, "fake_docker", "fake_docker")
    repo = repos.Git(REPO_DIR, **config["src"]["args"])
    repo.update()
    strat = strats.Tag(repo)
    cwd = os.getcwd()
    os.chdir(CONTAINER_REPO)
    # don't test this container
    build.test_flag = False
    strat.execute("isc-bind", build=build, config=config)
    os.chdir(cwd)


def test_branch_strategy():
    client = create_client()
    config = import_config("tests/containers/doh-branch-strat/info.json")
    build = Build(logging, "fake_docker", "fake_docker")
    repo = repos.Git(REPO_DIR, **config["src"]["args"])
    repo.update()
    strat = strats.Branch(repo)
    cwd = os.getcwd()
    os.chdir(CONTAINER_REPO)
    strat.execute("doh-branch-strat", build=build, config=config)
    os.chdir(cwd)
    cont = client.containers.run(f"{config['repo']}:latest", detach=True)
    code, out = cont.exec_run("doh-server -version")
    assert "2.0.0" in str(out)
    cont.remove(force=True)
