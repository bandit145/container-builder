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
    def compare(self, **kwargs):
        pass


class MockStrat(Strategy):
    def __init__(self, repo):
        super().__init__(repo)

    def compare(self):
        return True


class Branch(Strategy):
    def __init__(self, repo):
        super().__init__(repo)

    def compare(self, **kwargs):
        return kwargs["new_img"].id != kwargs["img"].id


class Tag(Strategy):
    def __init__(self, repo):
        super().__init__(repo)

    # docker container repo
    def get_remote_repo_tags(self, repo):
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
        for tag in str(output.stdout).split("\n"):
            tag = tag.strip("v")
            try:
                tags.append(semver.VersionInfo.parse(tag))
            # assume there are some nonsense tags and just throw them away
            except ValueError:
                continue
        return sorted(tags, reverse=True)

    def compare(self, **kwargs):
        return kwargs["latest"] != kwargs["remote_latest"]


# extra references for config file
track_branch = Branch
track_tag = Tag
