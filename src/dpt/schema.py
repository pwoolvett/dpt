
from enum import Enum
import json
import os
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import toml
import yaml

from pydantic import BaseSettings as PydanticBaseSettings
from pydantic import Field
from pydantic import validator
from pydantic.utils import deep_update
from pydantic.env_settings import env_file_sentinel
import sys

class BaseSettings(PydanticBaseSettings):

    @classmethod
    def from_file(
        cls,
        config_file: Optional[Union[str, Path]] = None,
        **kw,
    ):
        """Instantiate passing data as kwargs."""

        config_file = config_file or os.environ.get("DPT_CFG_FILE")
        if not config_file:
            return cls(**kw)

        config_path = Path(config_file).resolve()
        try:
            return cls(__config_path__=config_path, **kw)
        except Exception as err:
            print(f"Incorrectly formatted {config_path} ({err})")
            sys.exit(1)

    def __init__(
        __pydantic_self__,
        __config_path__:Optional[Union[str, Path]]=None,
        _env_file = env_file_sentinel,
        **values
    ) -> None:
        """Instantiate Settings object from envfile, envvars, and cfgfile.
        Provided values are overwritten/merged according to the
        following order:
          
          1. class defaults
          2. __config_path__
          3. _env_file
          4. envs
          5. instantiation

        * This means that for clashing, non-complex (as in not models,
        dicts, etc) variable names, their corresponding values are
        overriden in that order.

        * Complex objects are merged using pydantic deepcopy. 

        * Arrays or list-like do not count as "complex", so they are
          always overriden.

        Example:
            Given the following content in `oddl.json`:
            ```bash
            $ cat oddl.json
            ...
              "PASS": "JSON_PW",
                 "ALARM": 0.2,
                 "ALERT": 0.5,
            ...
            $ ODDL_PASS=ENV_PW ODDL_CAMERAS_CONFIG='{"LEFT": {"ALARM": 999}}' python
            >>> import oddl
            >>> oddl.SETTINGS.PASS # environment overrides json
            'ENV_PW'
            >>> oddl.SETTINGS.CAMERAS_CONFIG.LEFT.ALARM # environment merges json
            999.0
            >>> oddl.SETTINGS.CAMERAS_CONFIG.LEFT.ALERT # other settings from json kept intact
            0.5
            ```
        """
        if __config_path__:
            path = Path(__config_path__).resolve()
            parser = {
                ".json": json.loads,
                ".toml": toml.loads,
                ".yml": yaml.safe_load,
                ".yaml": yaml.safe_load,
            }[path.suffix]
            with open(path) as fp:
                raw = fp.read()

            init_kw = json.loads(json.dumps(parser(raw)))

        else:
            init_kw = {}

        super().__init__(**deep_update(
            init_kw,
            __pydantic_self__._build_values(values, _env_file=_env_file),
        ))

class ReadmeExt(Enum):
    """README file extension"""
    RST = ".rst"
    MD = ".rst"

Env = Field(
    None,
    description="Environment variables",
    examples=[
        {
            "POETRY_VIRTUALENVS_IN_PROJECT":"true",
            "DISPLAY": "=:0",
            "COLORTERM": "truecolor",
        }
    ],
)

Args = Field(
    None,
    description="Dockerfile Arguments",
    examples=[
        {
            "WITH_VALUE":"true",
            "WITHOUT_VALUE": "",
        }
    ],
)

class Spacing(BaseSettings):
    """Esthetic spaces between sections"""
    n="\n"
    nn="\n"*2
    header="# Made with <3 using dpt. Check it out at git.io/dpt"
    z=""
    t="\n"*2 + "#"*80 + "\n"*2
    footer=""

class Target(BaseSettings):

    __examples__ = []

    repository: Optional[str] = Field(
        None,
        description="Docker image repository",
        examples=["python", "nvcr.io/deepstream-l4t"]
    )
    tag: Optional[str] = Field(
        None,
        description="Docker image repository",
        examples=["python", "nvcr.io/deepstream-l4t"]
    )
    image: Optional[str] = Field(
        None,
        description="Docker image, including repository and tag",
        examples=["python:3.9-alpine", "nvcr.io/deepstream-l4t:base"]
    )

    env: Optional[Dict[str, str]] = Env
    args: Optional[Dict[str, Optional[str]]] = Args

    reqs: Optional[List[Dict[str, List[str]]]] = Field(
        None,
        description="installer -> dependencies groups to install",
        examples=[
            [
                {
                    "apk add --no-cache": [
                        "musl-dev",
                        "curl",
                        "git",
                    ],
                },
                {
                    "git clone": ["https://a-dependency.git"],
                    "apk del": ["git", "curl"]
                }
            ],
        ]
    )

    poetry_extras: Optional[List[str]] = Field(
        None,
        description="Poetry extras (groups) to include when installing",
        examples=[
            ["db", "cli", ]
        ]
    )

    @validator("image")
    def consistent_image(cls, v, values, **kwargs):
        repository = values.get("repository")
        tag = values.get("tag")

        if not v:
            if repository and tag:
                return f"{repository}:{tag}"
            if not (repository or tag):
                return "python:3.9-alpine"

        img_repo, img_tag = v.split(":")
        if repository:
            assert repository == img_repo
        else:
            values["repository"] = img_repo

        if tag:
            assert tag == img_tag
        else:
            values["tag"] = img_tag

        return v

class Dev(Target):
    """Configuration for the developer (dev) target"""


    poetry_version: str = Field(
        "1.1.4"
    )

class Prod(Target):
    """Configuration for the production target"""

    entrypoint_script: Optional[str] = Field(
        None,
        description="ENTRYPOINT (script) for the docker image"
    )
    cmd: Optional[str] = Field(
        None,
        description="CMD script for the docker image"
    )

class Dockerfile(BaseSettings):

    package: str = Field(
        ...,
        description="Python package name"
    )

    readme_ext: ReadmeExt = Field(
        ReadmeExt.RST,
        description=ReadmeExt.__doc__
    )
    scripts_path: Path = Field(
        Path("/usr/local/sbin"),
        description="Path to store scripts - Should be in $PATH!"
    )
    args: Optional[Dict[str, Optional[str]]] = Args

    dev: Dev = Field(
        ...,
        description=Dev.__doc__,
        examples=Dev.__examples__,
    )


    prod: Prod = Field(
        ...,
        description=Prod.__doc__,
        examples=Prod.__examples__,
    )

    request:str = Field(
        "/usr/bin/curl -L -o",
        description="Binary with args to execute when downloading files",
        examples=["/usr/bin/wget -O"]
    )

    spacing:Spacing = Field(
        Spacing(),
        description=Spacing.__doc__
    )
    def render(self, env):
        template = env.get_template('Dockerfile.jinja')
        return template.render(json.loads(self.json()))
