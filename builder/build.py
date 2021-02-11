from builder.src.config import Config
from builder.src.build import Build
import builder.src.repos as repos
import builder.src.strategies as strats
import argparse
import multiprocessing
import os


def parse_args():
	parser = argparse.ArgumentParser(description="build containers")
	parser.add_argument(
	    "-d", "--dir", help="directory to build from. If not used builds all"
	)
	parser.add_argument("-t", "--tag", help="tag for build")
	parser.add_argument("-l", "--labels", help="labels in label=thing,label2=thing")
	parser.add_argument(
	    "-p", "--push", help="push container when done", action="store_true"
	)
	parser.add_argument("--test", help="run tests before pushing", action="store_true")
	parser.add_argument("-w", "--workers", help="number of workers", type=int, default=4)
	parser.add_argument("--userenv", help="env var with username")
	parser.add_argument("--passwordenv", help="env var with password")
	return parser.parse_args()


def discover_containers():
	conts = []
	for item in os.listdir('.'):
		if item.path.isdir(item):
			if item.path.exists(f'{item}/Dockerfile'):
				conts.append(item)
	return conts


def configure_logging():
	pass

def build_container(cont, args):
	logger = configure_logging()
	build = Build(logger, args.user_env_Var, args.pass_env_var, **{'test_flag': args.test, 'push_flag': args.push})
	conf = Config()
	conf.load(f'{cont}/info.json')
	build.run(cont, conf.config)


def execute_container_builds():
	pass

def run():
	args = parse_args()
	