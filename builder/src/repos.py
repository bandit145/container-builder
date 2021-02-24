from abc import ABC, abstractmethod
import subprocess
import os
import builder.src.exceptions as exceptions


class Repo(ABC):
    repo_url = None
    release = None
    repo_dir = None
    name = None

    def __init__(self, repo_url, repo_dir, name, release):
        self.repo_url = repo_url
        self.release = release
        self.name = name
        self.repo_dir = repo_dir
        self.path = f"{self.repo_dir}/{self.name}"

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def configure(self):
        pass

    @abstractmethod
    def cleanup(self):
        pass

class TestRepo(Repo):
    def __init__(self, repo_dir, **kwargs):
        super().__init__(kwargs["url"], repo_dir, kwargs['name'], kwargs["branch"])

    def update(self):
        pass
    def configure(self):
        pass

    def cleanup(self):
        pass


class Git(Repo):
    def __init__(self, repo_dir, **kwargs):
        if "name " not in kwargs.keys():
            name = kwargs["url"].split("/")[-1].split(".")[0]
        super().__init__(kwargs["url"], repo_dir, name, kwargs["branch"])

    def update(self):
        if os.path.exists(f"{self.repo_dir}/{self.name}"):

            output = subprocess.run(
                "git fetch --all --tags",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=f"{self.repo_dir}/{self.name}",
            )
        else:
            output = subprocess.run(
                f"git clone {self.repo_url} {self.name}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.repo_dir,
            )
        if output.returncode != 0:
            raise exceptions.RepoException(output.stdout)

    def set_branch(self):
        # not used for anything yet but it should be used to reset to a working branch
        current_branch = str(
            subprocess.run(
                f"git branch --show-current",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=f"{self.repo_dir}/{self.name}",
                check=True,
            ).stdout
        ).strip("\n")
        if self.release:
            output = subprocess.run(
                f"git checkout {self.release}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=f"{self.repo_dir}/{self.name}",
            )

    def cleanup(self):
        pass

    def configure(self):
        self.update()
        self.set_branch()
