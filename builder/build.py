from builder.src.config import Config
from builder.src.build import Build
import builder.src.repos as repos
import builder.src.strategies as strats
import argparse
import multiprocessing
import os


def parse_args():
    parser = argparse.ArgumentParser(description="build containers")
    parser.add_argument(
        "-d", "--dir", help="directory to build from. If not used builds all"
    )
    parser.add_argument("-t", "--tag", help="tag for build")
    parser.add_argument("-l", "--labels", help="labels in label=thing,label2=thing")
    parser.add_argument(
        "-p", "--push", help="push container when done", action="store_true"
    )
    parser.add_argument("--test", help="run tests before pushing", action="store_true")
    parser.add_argument(
        "-w", "--workers", help="number of workers", type=int, default=4
    )
    parseer.add_argument(
        "--repo-dir",
        help="directory to clone repos to",
        default="/tmp/container-builder/",
    )
    parser.add_argument("--userenv", help="env var with username")
    parser.add_argument("--passwordenv", help="env var with password")
    return parser.parse_args()


def discover_containers():
    conts = []
    for item in os.listdir("."):
        if item.path.isdir(item):
            if item.path.exists(f"{item}/Dockerfile"):
                conts.append(item)
    return conts


# logger per runner
def configure_logging():
    pass


def build_container(cont, args):
    logger = configure_logging()
    build = Build(
        logger,
        args.user_env_Var,
        args.pass_env_var,
        **{"test_flag": args.test, "push_flag": args.push},
    )
    conf = Config()
    conf.load(f"{cont}/info.json")
    repo_name = list(conf["src"]["type"])
    repo_name[0] = repo_name[0].upper()
    repo_name = "".join(repo_name)
    if hasattr(repos, repo_name):
        # get repo_dir from somewhere
        repo = getattr(repos, repo_name)(args.repo_dir, **conf["src"]["args"])
    else:
        raise Exception(f"{repo_name} repo type not found!")
    if hasattr(strats, conf["strategy"]["name"]):
        strat = getattr(strats, conf["strategy"]["name"])(conf["strategy"]["args"])(
            repo
        )
    else:
        raise Exception(f"{conf['strategy']['name']} strategy not found!")
    build.run(cont, conf.config, strat)


def execute_container_builds():
    pass


def run():
    args = parse_args()
