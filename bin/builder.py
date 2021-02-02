#!/usr/bin/env python3
import argparse
import docker
import os
import sys
import json

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
parser.add_argument("-w", "--workers", help="number of workers", type=int, default=4)
parser.add_argument("--userenv", help="env var with username")
parser.add_argument("--passwordenv", help="env var with password")

args = parser.parse_args()


def get_labels(labels):
    label_dict = {}
    if labels:
        for item in labels.split(","):
            if "=" not in item:
                print("==> {0} syntax incorrect".format(item), file=sys.stderr)
                sys.exit(1)
            key, value = item.split("=")
            label_dict[key] = item
        return label_dict
    else:
        return None


def build_container(client, cont, tag, labels={}):
    try:
        print("==> Starting build of container {0}".format(cont))
        image = client.images.build(
            path=cont, tag=tag, labels=labels, rm=True, forcerm=True
        )
        try:
            [print("==>", x["stream"]) for x in image[1] if "stream" in x.keys()]
        except KeyError:
            [print("==>", x) for x in image[1]]
            sys.exit(1)
        return image[0]
    except docker.errors.BuildError as error:
        print("==> Build failure", str(error), file=sys.stderr)
        sys.exit(1)
    except docker.errors.APIError:
        print(
            "==> Docker API error. Is the docker daemon running? Do you have permission?"
        )
        sys.exit(1)


def test_container(client, cont, cont_long_name, capabilites):
    print("==> Loading tests for {0}".format(cont))
    with open(cont + "/test.json", "r") as test:
        tests = json.load(test)
    print("==> Starting test of container {0}".format(cont))
    running_cont = client.containers.run(
        cont_long_name, detach=True, cap_add=capabilites
    )
    for test in tests:
        output = running_cont.exec_run(test["command"])
        try:
            assert eval(test["assert"].strip() + " " + '"' + str(output.output) + '"')
        except AssertionError:
            print("==> Test failed", file=sys.stderr)
            print("==> assert {0} {1}".format(test["assert"], str(output.output)))
            running_cont.remove(force=True)
            sys.exit(1)
    running_cont.remove(force=True)
    print("==> Tests pass for {0}".format(cont))


def get_creds():
    user = os.getenv(args.userenv)
    password = os.getenv(args.passwordenv)
    if not password or not user:
        print("==> user or password env var does not exist", file=sys.stderr)
        sys.exit(1)
    return {"username": user, "password": password}


def push_container(client, cont, repo):
    print("==> Pushing container {0} to {1}".format(cont, repo))
    print(repo)
    output = client.images.push(repo, auth_config=get_creds())
    print(output)
    for item in output:
        if "errorDetail" in item:
            sys.exit(1)


def get_cont_info(cont):
    try:
        with open(cont + "/info.json", "r") as cont_info:
            return json.load(cont_info)
    except IOError:
        print("==> Could not find {0}".format(cont + "/info.json"), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(
            "==> Json decode error for {0}".format(cont + "/info.json"), file=sys.stderr
        )
        sys.exit(1)


def container_process(cont, tag, labels):
    client = docker.from_env()
    info = get_cont_info(cont)
    if not tag:
        tag = info["tag"]
    if "capabilites" not in info.keys():
        capabilites = None
    else:
        capabilites = info["capabilites"]
    image = build_container(client, cont, info["repo"] + tag, labels)
    if args.test:
        test_container(client, cont, info["repo"] + tag, capabilites)
    if args.push:
        push_container(client, cont, info["repo"] + tag.split(":")[0])


def main():
    labels = get_labels(args.labels)
    dirs = [
        x for x in os.listdir(".") if x != "venv" and "." not in x and os.path.isdir(x)
    ]
    if args.dir and args.dir in dirs:
        container_process(args.dir, args.tag, labels)
    elif args.dir and args.dir not in dirs:
        print("==> Container {0} not found".format(cont), file=sys.stderr)
        sys.exit(1)
    else:
        for cont in dirs:
            container_process(cont, None, None)


if __name__ == "__main__":
    main()
