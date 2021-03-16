import docker
import os
import json
import shutil
import datetime
from container_builder.src.exceptions import BuildException


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
            raise BuildException(
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
            raise BuildException(f"{cont} build failed!")

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
        self.logger.info(f"Build started on {datetime.datetime.now()}")
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
            self.logger.info(error)
            raise BuildException(error)
        finally:
            self.cleanup(cont)
            self.logger.info(f"Build ended on {datetime.datetime.now()}")

    def prep(self, cont, build_repo):
        cwd = os.getcwd()
        if not os.path.exists(self.build_dir):
            os.mkdir(self.build_dir)
        if not os.path.exists(f"{self.build_dir}/{cont}/"):
            shutil.copytree(f"{cwd}/{cont}", f"{self.build_dir}/{cont}/")
        # mock repos can be used, if that is the case, this will be None
        if build_repo:
            shutil.copytree(build_repo, f"{self.build_dir}/{cont}/build-dir/")

    def cleanup(self, cont):
        shutil.rmtree(f"{self.build_dir}/{cont}")
        # [
        #     self.client.images.remove(x.id, force=True)
        #     for x in self.client.images.list(filters={"dangling": True})
        # ]
        # this isn't implemented in podmans docker faux api so we do it the hard way ^
        # self.client.images.prune(filters={'dangling': True})

    def test(self, tag, capabilities, tests):
        running_cont = self.client.containers.run(
            f"{tag}", detach=True, cap_add=capabilities
        )
        try:
            for test in tests:
                # ECH, rewrite this without assertion
                try:
                    output = running_cont.exec_run(test["command"])
                    assert eval(f'{test["assert"].strip()} str({str(output.output)})')
                except (AssertionError, SyntaxError):
                    self.logger.info(
                        f"{tag} test failed: assert {test['assert']} {output.output}"
                    )
                    running_cont.remove(force=True)
                    raise BuildException("Container test failed!")
        except docker.errors.APIError as error:
            self.logger.info(f"{tag} test failed due to docker api error: {error}")
            raise BuildException("Could not exec into container for test")
        finally:
            running_cont.remove(force=True)
        self.logger.info(f"All {len(tests)} tests passed")

    def push(self, cont, repo, extra_tag=None):
        self.logger.info(f"pushing container {cont} to {repo}")
        output = self.client.images.push(
            repo, tag=extra_tag, auth_config=self.get_creds()
        )
        self.logger.debug(f"{cont} push output: {output}")
        for item in output:
            if "errorDetail" in item:
                self.logger.info(f"Failed to push {cont}: {item}")
                raise BuildException(f"failed to push {cont}")
