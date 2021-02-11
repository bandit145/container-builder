from builder.src.build import Build
import json


def import_config(file):

	with open(f'tests/data/{file}', 'r') as conf:
		return json.load(conf)


def test_build():
	conf = import_config('info.json')
	build = Build(logger, args.user_env_Var, args.pass_env_var)
	build.run()