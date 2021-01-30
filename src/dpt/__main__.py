
import json
from pathlib import Path
import sys 

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import StrictUndefined
import toml
import yaml


env = Environment(
    loader=PackageLoader(__package__, 'templates'),
    autoescape=False,
    line_statement_prefix=">>> ",
    undefined=StrictUndefined,
)


def strarray(data):
    if isinstance(data, str):
        return f'"{data}"'
    return ', '.join(
        f'"{part}"' for part in data
    )

def parse(source_file):
    path = Path(source_file).resolve()
    parser = {
        ".json": json.loads,
        ".toml": toml.loads,
        ".yml": yaml.safe_load,
        ".yaml": yaml.safe_load,
    }[path.suffix]
    with open(path) as fp:
        raw = fp.read()
    return json.loads(json.dumps(parser(raw)))

def flatten(array):
    for requirement_dict in array:
        for command, args in requirement_dict.items():
            yield command, args

def main(source_file):
    env.filters['strarray'] = strarray
    env.filters['flatten'] = flatten

    dockerfile = env.get_template('Dockerfile.jinja')
    parsed_content = dockerfile.render(parse(source_file))
        # cmd=['--help'],
        # dev_image="python",
        # dev_tag="3.9-alpine",
        # build_reqs=[
        #     ("apk add --no-cache", [
        #         "gcc",
        #         "libressl-dev",
        #         "musl-dev",
        #         "libffi-dev",
        #         "curl",
        #         "git",
        #         "python3-dev",
        #     ]),
        # ],
        # poetry_version="1.1.4",
        # request_file="/usr/bin/curl -Lo",
        # scripts_path="/usr/bin",
        # package="demo",
        # prod_image="python",
        # prod_tag="3.9-alpine",
        # runtime_reqs=[
        #     ("apk add --no-cache", [
        #         "libcurl",
        #     ]),
        # ],
        # entrypoint_script="wait-for-it.sh"
    # )
    print(parsed_content)

def cli():
    return main(sys.argv[1])
