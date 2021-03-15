import docker
import os
import re
import requests
import datetime
import semver
import json
import shutil
import time


class Build:
    test_flag = True
    push_flag = False
    build_dir = "/tmp/container-builder"

    def __init__(self, logger, user_env_var, pass_env_var, **kwargs):
        self.client = docker.from_env()
        self.user_env_var = user_env_var
        self.pass_env_var = pass_env_var
        self.logger = logger
        if "test_flag" in kwargs.keys():
            self.test_flag = kwargs["test_flag"]
        if "push_flag" in kwargs.keys():
            self.push_flag = kwargs["push_flag"]

    def get_creds(self):
        username = os.getenv(self.user_env_var)
        password = os.getenv(self.pass_env_var)
        if not username or not password:
            raise Exception(
                f"Could not find {self.user_env_var} or {self.pass_env_var}"
            )
        return {"username": username, "password": password}

    def build(self, tag, cont, build_args={}):
        self.logger.info(f"Starting build of container {cont}")
        # I think rm true only works sometimes(?) so we do false here so there isn't one missing
        # (I think this might be a race condition) with docker/podman
        image = self.client.images.build(
            path=f"{self.build_dir}/{cont}", tag=tag, buildargs=build_args
        )
        try:
            [self.logger.info(x["stream"]) for x in image[1] if "stream" in x.keys()]
        except KeyError:
            [self.logger.info(x) for x in image[1]]
            raise Exception(f"{cont} build failed!")

        return image[0]

    def read_test(self, cont):
        with open(f"{cont}/test.json", mode="r") as conf:
            test = json.load(conf)
        return test

    def pull(self, repo, tag):
        try:
            img = self.client.images.pull(repo, tag)
        except docker.Errors.APIError:
            self.logger.error(f"{repo}:{tag} does not exist")

    def run(self, cont, config, tag, build_repo, latest=False):
        extra_tag = None
        if latest:
            extra_tag = "latest"
        self.prep(cont, build_repo)
        tests = self.read_test(cont)
        try:
            img = self.build(tag, cont)
            if self.test_flag:
                self.test(tag, config["capabilities"], tests)
            if self.push_flag:
                self.push(cont, tag, extra_tag)
        except Exception as error:
            raise Exception(error)
        finally:
            self.cleanup(cont)

    def prep(self, cont, build_repo):
        cwd = os.getcwd()
        if not os.path.exists(self.build_dir):
            os.mkdir(self.build_dir)
        shutil.copytree(f"{cwd}/{cont}", f"{self.build_dir}/{cont}/")
        shutil.copytree(build_repo, f"{self.build_dir}/{cont}/build-dir/")

    def cleanup(self, cont):
        shutil.rmtree(f"{self.build_dir}/{cont}")
        [
            self.client.images.remove(x.id, force=True)
            for x in self.client.images.list(filters={"dangling": True})
        ]
        # this isn't implemented in podmans docker faux api so we do it the hard way ^
        # self.client.images.prune(filters={'dangling': True})

    def test(self, tag, capabilities, tests):
        running_cont = self.client.containers.run(
            f"{tag}", detach=True, cap_add=capabilities
        )
        for test in tests:
            output = running_cont.exec_run(test["command"])
            try:
                assert eval(f'{test["assert"].strip()} str({str(output.output)})')
            except (AssertionError, SyntaxError):
                self.logger.info(
                    f"{tag} test failed: assert {test['assert']} {output.output}"
                )
                running_cont.remove(force=True)
                raise Exception("Container test failed!")
        running_cont.remove(force=True)

    def push(self, cont, repo, extra_tag=None):
        self.logger.info(f"pushing container {cont} to {repo}")
        output = self.client.images.push(
            repo, tag=extra_tag, auth_config=self.get_creds()
        )
        self.logger.debug(f"{cont} push output: {output}")
        for item in output:
            if "errorDetail" in item:
                self.logger.info(f"Failed to push {cont}: {item}")
                raise Exception(f"failed to push {cont}")
