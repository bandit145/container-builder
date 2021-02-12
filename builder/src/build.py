import docker
import os
import re
import requests
import datetime
import semver


class Build:
    test_flag = True
    push_flag = False

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

    def build(self, tag, cont):
        self.logger.info(f"Starting build of container {cont}")
        image = self.client.images.build(path=cont, tag=tag, rm=True)
        try:
            [self.logger.info(x["stream"]) for x in image[1] if "stream" in x.keys()]
        except KeyError:
            [self.logger.info(x) for x in image[1]]
            raise Exception(f"{cont} build failed!")
        return image[0]

    def read_test(cont):
        with open(f"{cont}/info.json", mode="r") as conf:
            test = json.load(conf)
        return test

    def pull(self, repo, tag):
        try:
            img = self.client.images.pull(repo, tag)
        except docker.Errors.APIError:
            self.logger.error(f"{repo}:{tag} does not exist")

    def run(self, cont, config, strat):
        repo, tag = config["tag"].split(":")[0]
        tests = self.read_test(cont)
        tags = self.get_repo_tags(repo)
        existing_img = self.pull(repo, tags[0])
        img = self.build(config["tag"], cont)
        if existing_img:
            img_same = strat.compare(img, existing_img)
            self.logger.info(f"Images are the same: {img_same}")
        if self.test_flag:
            self.test(config["tag"], config["capabilities"], tests)
        if self.push_flag:
            if not img_same:
                self.push(cont, repo)

    def get_repo_tags(self, repo):
        repo_domain, repo = repo.split("/")
        repo = "/".join(repo)
        req = requests.get(f"https://{repo_domain}/v2/{repo}/tags/list")
        # deal with betas etc.
        # add in  master/main/latest support
        tags = sorted(
            [
                semver.VersionInfo.parse(x.strip("v"))
                for x in req.json()["tags"]
                if x != "latest"
            ],
            reverse=True,
        )
        return tags

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
