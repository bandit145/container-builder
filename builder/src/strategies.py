from abc import ABC, abstractmethod
import subprocess
import semver
import builder.src.exceptions as exceptions

# Resolution strategies come in after a build has completed with various ways to determine
# when a pushable change has occured


class Strategy(ABC):

    def __init__(self, repo):
        self.repo = repo

    @abstractmethod
    def compare(self, **kwargs):
        pass


class TestStrat(Strategy):
    def  __init__(self, repo):
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

    def get_tags(self):
        output = subprocess.run("git tag", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=self.repo.path)
        if output.returncode != 0:
            raise exceptions.StrategyException(f"Something went wrong with listing tags {output.stdout}")
        tags = []
        for tag in str(output.stdout).split('\n'):
            tag = tag.strip('v')
            try:
                tags.append(semver.VersionInfo.parse(tag))
            #assume there are some nonsense tags and just throw them away
            except ValueError:
                continue
        return sorted(tags, reverse=True)


    def compare(self, **kwargs):
        return kwargs["latest"] != kwargs["remote_latest"]

#extra references for config file
track_branch = Branch
track_tag = Tag
