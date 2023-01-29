import os
import tomllib
from dataclasses import asdict, dataclass
from tomllib import TOMLDecodeError

import click
import toml

from kt.util import Logger

logger = Logger().get_logger()


class ProfileNotFoundException(Exception):
    pass


class ProfileException(Exception):
    pass


@dataclass(frozen=True)
class ProfileConfig:
    server_url: str
    user_name: str
    password: str


class Profile:
    def __init__(self):
        self._profile_path = f"{os.path.expanduser('~')}/.kt/profile"

    def load(self, profile_name: str | None = None) -> ProfileConfig:
        try:
            with open(self._profile_path, "rb") as f:
                profiles: dict[str, dict[str, dict[str, str]]] = tomllib.load(f)
        except FileNotFoundError:
            raise ProfileNotFoundException("Profile not found.")
        except TOMLDecodeError:
            raise ProfileException("Bad toml file.")
        except:
            logger.exception("Unknown Error")
            raise ProfileException("Unknown error.")

        if profile_name:
            try:
                return ProfileConfig(**profiles["profiles"][profile_name])
            except KeyError:
                raise ProfileException("Specified profile name not found in config.")
            except TypeError:
                raise ProfileException("Invalid profile format.")
            except:
                logger.exception("Unknown Error")
                raise ProfileException("Unknown error.")
        else:
            try:
                default = [n for n in profiles["profiles"].keys() if n.endswith("default")][0]
                return ProfileConfig(**profiles["profiles"][default])
            except IndexError:
                raise ProfileException(
                    "Default profile config not found. You can configure profile by running `kt --init`"
                )
            except TypeError:
                raise ProfileException("Invalid profile format.")
            except:
                logger.exception("Unknown Error")
                raise ProfileException("Unknown error.")

    def init(self, ctx: click.Context):
        def prompt_server_url(ctx: click.Context, value: str | None = None):
            msg = "ktistec server url: "
            input = ""
            if not value:
                input = click.prompt(msg)
            else:
                input = str(value)
            try:
                if not (input[0:7] == "http://" or input[0:8] == "https://"):
                    raise ValueError(value)
                else:
                    return input
            except ValueError:
                click.echo(
                    "\nValidation Error: Server URL must be start with protocol [http://|https://]\n"
                )
                return prompt_server_url(ctx, click.prompt(msg))

        profile_name = click.prompt(
            "profile name: ",
        )
        server_url = prompt_server_url(ctx)
        user_name = click.prompt(
            "user name: ",
        )
        password = click.prompt("password: ", hide_input=True)
        profile = ProfileConfig(server_url=server_url, user_name=user_name, password=password)

        os.makedirs(self._profile_path[:-8], exist_ok=True)
        toml.dump(
            {"profiles": {profile_name + ":default": asdict(profile)}},
            open(self._profile_path, "w"),
        )
        click.echo("\nProfile saved.")
