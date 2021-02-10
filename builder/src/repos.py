from abc import ABC
import subprocess
import os
import builder.src.exceptions as exceptions


class Repo(ABC):
    repo_url = None
    release = None
    repo_dir = None
    name = None

    @classmethod
    def update(self):
        pass

    @classmethod
    def configure(self):
        pass


def Git(Repo):
    def __init__(self, repo_url, repo_dir, name=None, branch=None):
        self.repo_url = repo_url
        self.repo_dir = repo_dir
        self.branch = branch
        if name:
            self.name = name
        else:
            # grab name from repo url
            self.name = self.repo_url.split("/")[-1].split(".")[0]
        super().__init__()

    def update(self):
        if os.path.exists(f"{self.repo_dir}/{name}"):

            output = subprocess.run(
                "git pull",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=f"{self.repo_dir}/{name}",
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
        if self.branch:
            output = subprocess.run(
                f"git checkout {self.branch}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=f"{self.repo_dir}/{self.name}",
            )

    def configure(self):
        self.update()
        self.set_branch()
