
import json
from pathlib import Path
import sys
from typing import Dict
from typing import List
from typing import Optional

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import StrictUndefined
import toml
import yaml

from dpt.schema import Dockerfile

env = Environment(
    loader=PackageLoader(__package__, 'templates'),
    autoescape=False,
    line_statement_prefix=">>> ",
    undefined=StrictUndefined,
)



# def parse(source_file):
#     path = Path(source_file).resolve()
#     parser = {
#         ".json": json.loads,
#         ".toml": toml.loads,
#         ".yml": yaml.safe_load,
#         ".yaml": yaml.safe_load,
#     }[path.suffix]
#     with open(path) as fp:
#         raw = fp.read()
#     return json.loads(json.dumps(parser(raw)))


def register(env_: Environment):

    def decorator(function):
        env_.filters[function.__name__] = function
        return function

    return decorator

@register(env)
def cmdparse(data):
    if not data:
        return ""

    if isinstance(data, str):
        return f'CMD ["{data}"]'
    if isinstance(data, list):
        return 'CMD ['+', '.join(
            f'"{part}"' for part in data
        )+']'
    raise ValueError


@register(env)
def reqsparse(array,):
    instructions = []
    for requirement_dict in array:
        instruction = ""
        for command, args in requirement_dict.items():
            instruction = instruction + f" \\\n    && {command}"
            for arg in args:
                instruction = instruction + f" \\\n        {arg}"
        instructions.append("RUN" + instruction.lstrip().lstrip("\\").lstrip().lstrip("&&"))
    together = '\n'.join(instructions)
    return f"{together}"



@register(env)
def envparse(
    env:Optional[Dict[str, str]],
    joiner=" ",
) -> str:
    if not env:
        return ""
    return joiner + joiner.join(
        f"{varname}={varvalue}"
        for varname, varvalue in env.items()
    )


@register(env)
def extrasparse(
    extras:Optional[List[str]],
) -> str:
    if not extras:
        return ""
    return " ".join(
        f"-E {extra}"
        for extra in extras
    )



@register(env)
def argparse(
    args:Optional[Dict[str, str]],
) -> str:
    if not args:
        return ""
    return "\n".join(
        f"ARG {varname}{('='+varvalue) if varvalue else ''}"
        for varname, varvalue in args.items()
    )

def main(config_file, **kw):

    dockerfile = Dockerfile.from_file(
        config_file=config_file,
        **kw
    )
    parsed_content = dockerfile.render(env=env)

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
