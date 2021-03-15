from abc import ABC, abstractmethod
import subprocess
import semver
import requests
import builder.src.exceptions as exceptions

# Resolution strategies come in after a build has completed with various ways to determine
# when a pushable change has occured


class Strategy(ABC):
    def __init__(self, repo):
        self.repo = repo

    @abstractmethod
    def execute(self, **kwargs):
        pass


class MockStrat(Strategy):
    def __init__(self, repo):
        super().__init__(repo)

    def execute(self, **kwargs):
        pass

class Branch(Strategy):
    def __init__(self, repo):
        super().__init__(repo)

    def execute(self, cont, **kwargs):
        build = kwargs["build"]
        config = kwargs["config"]
        self.repo.set_branch(config["strategy"]["args"]["branch"])
        build.run(
            cont,
            config,
            tag=f"{config['repo']}:latest",
            build_repo=self.repo.path,
            latest=True,
        )


class Tag(Strategy):
    def __init__(self, repo):
        super().__init__(repo)

    # docker container repo
    def get_remote_repo_tags(self, repo):
        repo = repo.split("/")
        repo_domain = repo[0]
        del repo[0]
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

    def get_local_repo_tags(self):
        output = subprocess.run(
            "git tag",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.repo.path,
        )
        if output.returncode != 0:
            raise exceptions.StrategyException(
                f"Something went wrong with listing tags {output.stdout}"
            )
        tags = []
        for tag in str(output.stdout).strip("b'").split("\\n"):
            tag = tag.strip("v")
            try:
                tags.append(semver.VersionInfo.parse(tag))
            # assume there are some nonsense tags and just throw them away
            except ValueError:
                continue
        return sorted(tags, reverse=True)

    def execute(self, cont, **kwargs):
        build = kwargs["build"]
        config = kwargs["config"]
        rmt_tags = set(self.get_remote_repo_tags(config["repo"]))
        lcl_tags = set(self.get_local_repo_tags())
        tag_diff = sorted(lcl_tags.difference(rmt_tags), reverse=True)
        for vsn_tag in tag_diff:
            if vsn_tag >= semver.VersionInfo.parse(
                config["strategy"]["args"]["version"]
            ):
                self.repo.set_branch(
                    f"{config['strategy']['args']['tag_prefix']}{vsn_tag}"
                )
                if list(tag_diff).index(vsn_tag) == 0:
                    build.run(
                        cont,
                        config,
                        tag=f"{config['repo']}:{vsn_tag}",
                        build_repo=self.repo.path,
                        latest=True,
                    )
                else:
                    build.run(
                        cont,
                        config,
                        tag=f"{config['repo']}:{vsn_tag}",
                        build_repo=self.repo.path,
                        latest=False,
                    )


# extra references for config file
track_branch = Branch
track_tag = Tag
