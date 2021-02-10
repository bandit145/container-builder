from builder.src.repos import Git
import subprocess

GIT_URL = "https://github.com/bandit145/test-repo.git"
REPO_DIR = "/tmp/"


def test_git_clone():
    git = Git(GIT_URL, REPO_DIR, None, "v1.0")
    git.update()
    git.set_branch()
    output = subprocess.run(
        "git describe --tags",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=f"{REPO_DIR}/{git.name}",
    )
    assert "v1.0" in str(output.stdout)
