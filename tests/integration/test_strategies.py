import builder.src.strategies as strats
import builder.src.repos as repos
from builder.src.build  import Build
from builder.src.config import Config
import logging
import json
import os
GIT_URL = "https://github.com/bandit145/test-repo.git"
REPO_DIR = "/tmp/"
CONTAINER_REPO = 'tests/containers/'


def import_config(file):
    conf = Config()
    conf.load('tests/containers/doh-tag-strat/info.json')
    return conf.config


def test_remote_tag_strategy():
    strat = strats.Tag(
        repos.TestRepo("/tmp/", **{"url": None, "name": None, "branch": None})
    )
    assert "2.6.0" in strat.get_remote_repo_tags(
        "quay.io/prometheus/prometheus"
    )


def test_local_tag_strategy():
    strat = strats.Tag(repos.Git("/tmp/", **{"url": GIT_URL}))
    strat.repo.update()
    assert len(strat.get_local_repo_tags()) == 2
    assert "1.0.0" in strat.get_local_repo_tags()


def test_tag_strategy():
    config = import_config('tests/containers/doh-tag-strat/info.json')
    print(config)
    build = Build(logging, 'fake_docker', 'fake_docker')
    repo = repos.Git("/tmp/", **config['src']['args'])
    repo.update()
    strat = strats.Tag(repo)
    cwd = os.getcwd()
    os.chdir(CONTAINER_REPO)
    strat.execute('doh-tag-strat', build=build, config=config)    
    os.chdir(cwd)
