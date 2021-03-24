# container-builder

This is a little tool for running container builds from dockerfiles in sub directories.


CLI usage:
```
usage: builder [-h] [-d DIR] [-l LABELS] [-p] [--test] [-w WORKERS] [--repo-dir REPO_DIR] [--log-dir LOG_DIR] [--log-level {info,debug}] [--userenv USERENV] [--passwordenv PASSWORDENV]

build containers

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     directory to build from. If not used builds all
  -p, --push            push container when done
  --test                run tests before pushing
  -w WORKERS, --workers WORKERS
                        number of workers
  --repo-dir REPO_DIR   directory to clone repos to
  --log-dir LOG_DIR     logging directory
  --log-level {info,debug}
                        logging level
  --userenv USERENV     env var with username
  --passwordenv PASSWORDENV
                        env var with password

```

## Usage
If we have a repo like so:
```
thing1/
|
|- Dockerfile
|- info.json
|- test.json
thing2/
|
|- Dockerfile
|- info.json
|- test.json
```
The Dockerfile is self explanatory but the two other files are for us. 
info.json contains all the meta information needed for the build such as the repo to push the end container to, the type of source, and build strategy to use.

- repo is is the remote repo to push the finished container to.
- src is where we are pulling the source code to pack into the container (there is a NoRepo type if you are just building a container with
no code or artifacts to pull down and include)
- strategy is the build strategy type used for the container in question.
	
	There are 3 build strategies:
		
	- blind_build: This has no args other then empty dict "{}".
		
	- branch: You must provide the git branch to track; args: {"branch": "devel"}.
		
	- track_tag: Track semver tags with these supported args.
		
		- force_semver: true/false; this option if it finds a tag number without a trailing zero, it adds a ".0" to make it semver compliant.
			
		- replace_text: {"match": "-", "replacement": "."} replaces all occurrences of match with replacement.
			
		- tag_prefix: prefix of tag e.g. "v".
			
		- version: oldest tag to build back to e.g. "I want to build version 2.1.2 and up"

info.json example:
```
{
	"repo":"quay.io/bandit145/apache",
	"src":{
		"type": "NoRepo",
	        "args": {
		       "url": null
	        }
	},
	"strategy": {
		"name": "blind_build",
	        "args": {}
	}
}

```

The test.json file (this is optional, or will be in the future) is a list of commands that will exec in a running version of the built container
and assert the results  (what is in assert is just eval(item) so it must be valid python).

The assert line can be read as "'httpd' in {command_output}"

test.json example:
```
[
	{
		"command": "ps",
		"assert": "'httpd' in"
	}

]
```

TODOS:

Set config validation for repos and strategies.

Allow test files to be optional even if --test is specified.

Add types and use mypy in this repo

Throw CI in this repo (yeah not specifically an issue with this code base but whatever)
