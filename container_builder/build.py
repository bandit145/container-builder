from container_builder.src.config import Config
from container_builder.src.build import Build
import logging
import container_builder.src.repos as repos
from container_builder.src.exceptions import BuildException, StrategyException, RepoException
import container_builder.src.strategies as strats
import argparse
import docker
import multiprocessing
import os
import sys
import atexit


def parse_args():
    parser = argparse.ArgumentParser(description="build containers")
    parser.add_argument(
        "-d",
        "--dir",
        help="directory to build from. If not used builds all",
        default=".",
    )
    parser.add_argument("-l", "--labels", help="labels in label=thing,label2=thing")
    parser.add_argument(
        "-p",
        "--push",
        help="push container when done",
        action="store_true",
        default=False,
    )
    parser.add_argument("--test", help="run tests before pushing", action="store_true")
    parser.add_argument(
        "-w", "--workers", help="number of workers", type=int, default=4
    )
    parser.add_argument(
        "--repo-dir",
        help="directory to clone repos to",
        default="/tmp/container-builder/",
    )
    parser.add_argument(
        "--log-dir",
        help="logging directory",
        default="/var/log/container-builder",
    )
    parser.add_argument(
        "--log-level", help="logging level", default="info", choices=["info", "debug"]
    )
    parser.add_argument("--userenv", help="env var with username")
    parser.add_argument("--passwordenv", help="env var with password")
    return parser.parse_args()


def discover_containers(cont_dir):
    conts = []
    for item in os.listdir(cont_dir):
        if os.path.isdir(item):
            if os.path.exists(f"{item}/Dockerfile"):
                conts.append(item)
    return conts


def clean_dangling_containers():
    client = docker.from_env()
    [
        client.images.remove(x.id, force=True)
        for x in client.images.list(filters={"dangling": True})
    ]


# logger per runner
def configure_logging(cont, log_dir, log_level):
    if not os.path.isdir(log_dir):
        raise Exception("log directory not created")
    logger = logging.getLogger(cont)
    logger.setLevel(getattr(logging, log_level.upper()))
    fh = logging.FileHandler(f"{log_dir}/{cont}.log")
    logger.addHandler(fh)
    return logger


def build_container(data):
    cont = data[0]
    args = data[1]
    logger = configure_logging(cont, args.log_dir, args.log_level)
    build = Build(
        logger,
        args.userenv,
        args.passwordenv,
        **{"test_flag": args.test, "push_flag": args.push},
    )
    conf = Config()
    conf.load(f"{cont}/info.json")
    repo_name = list(conf.config["src"]["type"])
    repo_name[0] = repo_name[0].upper()
    repo_name = "".join(repo_name)
    if hasattr(repos, repo_name):
        # get repo_dir from somewhere
        repo = getattr(repos, repo_name)(args.repo_dir, **conf.config["src"]["args"])
    else:
        raise Exception(f"{repo_name} repo type not found!")
    if hasattr(strats, conf.config["strategy"]["name"]):
        strat = getattr(strats, conf.config["strategy"]["name"])(repo)
    else:
        raise Exception(f"{conf.config['strategy']['name']} strategy not found!")
    try:
        strat.execute(cont, build=build, config=conf.config)
    except (BuildException, StrategyException) as error:
        print(
            "Something went wrong during the build process for",
            f"{cont}.",
            "Reason:",
            error
        )
        print(f"See logs at {args.log_dir}/{cont} for more details")
    except RepoException as error:
        print("Something went wrong with repo operations for {cont}", "Reason:",error)

def execute_container_builds(args):
    if "Dockerfile" in os.listdir(args.dir):
        conts = [args.dir]
    else:
        conts = discover_containers(args.dir)
    with multiprocessing.Pool(args.workers) as pool:
        results = pool.map(build_container, [(x, args) for x in conts])


def run():
    try:
        args = parse_args()
        atexit.register(clean_dangling_containers)
        execute_container_builds(args)
    except KeyboardInterrupt:
        print("User cancelled!")