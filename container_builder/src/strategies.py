from abc import ABC, abstractmethod
import subprocess
import semver
import requests
import container_builder.src.exceptions as exceptions

# Resolution strategies come in after a build has completed with various ways to determine
# when a pushable change has occured


class Strategy(ABC):
    def __init__(self, repo):
        self.repo = repo

    @abstractmethod
    def execute(self, cont, **kwargs):
        pass

    @classmethod
    def validate_config(self, config, schema):
        new_conf = {}
        conf_keys = config.keys()
        for k, v in schema.items():
            if v["required"] and k not in conf_keys:
                raise exceptions.ConfigException(f"Config missing {k}")
            elif "default" in v.keys() and k not in conf_keys:
                new_conf[k] = v["default"]
            elif k in conf_keys:
                new_conf[k] = config[k]
        return new_conf


class MockStrat(Strategy):
    def __init__(self, repo):
        super().__init__(repo)

    def execute(self, cont, **kwargs):
        pass


class BlindBuild(Strategy):
    SCHEMA = {}

    def __init__(self, repo):
        super().__init__(repo)

    def execute(self, cont, **kwargs):
        build = kwargs["build"]
        config = kwargs["config"]
        build.run(
            cont,
            config,
            tag=f"{config['repo']}:latest",
            build_repo=None,
            latest=True,
        )


class Branch(Strategy):
    SCHEMA = {"branch": {"required": True}}

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

    SCHEMA = {
        "force_semver": {"required": False, "default": False},
        "replace_text": {"required": False},
        "tag_prefix": {"required": False},
        "version": {"required": True},
    }

    def __init__(self, repo):
        super().__init__(repo)

    # docker container repo
    def get_remote_repo_tags(self, repo):
        repo = repo.split("/")
        repo_domain = repo[0]
        del repo[0]
        repo = "/".join(repo)
        try:
            req = requests.get(f"https://{repo_domain}/v2/{repo}/tags/list")
        except requests.RequestException as error:
            raise StrategyException(f"Error grabbing remote repo tags {error}")

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

    def get_local_repo_tags(self, replace_text, force_semver, tag_prefix):
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
            tag = tag.strip(tag_prefix)
            if replace_text:
                tag = tag.replace(replace_text["match"], replace_text["replacement"])
            # force semver format
            if force_semver and len(tag.split(".")) < 3:
                tag += ".0"
            try:
                tags.append(semver.VersionInfo.parse(tag))
            # assume there are some nonsense tags and just throw them away
            except ValueError:
                continue
        return sorted(tags, reverse=True)

    def execute(self, cont, **kwargs):
        build = kwargs["build"]
        config = kwargs["config"]
        if "replace_text" in config["strategy"]["args"].keys():
            replace_text = config["strategy"]["args"]["replace_text"]
        else:
            replace_text = None
        if "force_semver" in config["strategy"]["args"].keys():
            force_semver = config["strategy"]["args"]["force_semver"]
        else:
            force_semver = None
        if "tag_prefix" in config["strategy"]["args"].keys():
            tag_prefix = config["strategy"]["args"]["tag_prefix"]
        else:
            force_semver = "v"
        rmt_tags = set(self.get_remote_repo_tags(config["repo"]))
        lcl_tags = set(self.get_local_repo_tags(replace_text, force_semver, tag_prefix))
        tag_diff = sorted(lcl_tags.difference(rmt_tags), reverse=True)
        for vsn_tag in tag_diff:
            if vsn_tag >= semver.VersionInfo.parse(
                config["strategy"]["args"]["version"]
            ):
                if replace_text:
                    repo_tag = str(vsn_tag).replace(
                        replace_text["replacement"], replace_text["match"]
                    )
                else:
                    repo_tag = vsn_tag
                if force_semver:
                    repo_tag = repo_tag.strip(f'{replace_text["match"]}0')
                self.repo.set_branch(f"{tag_prefix}{repo_tag}")
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
blind_build = BlindBuild
