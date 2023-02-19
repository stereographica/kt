import os
import tomllib
from copy import deepcopy
from dataclasses import asdict, dataclass
from tomllib import TOMLDecodeError

import click
import toml
from tabulate import tabulate

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
    def __init__(self) -> None:
        self._profile_path = f"{os.path.expanduser('~')}/.kt/profile"

    def loads(self) -> dict[str, ProfileConfig]:
        try:
            with open(self._profile_path, "rb") as f:
                toml_data: dict[str, dict[str, dict[str, str]]] = tomllib.load(
                    f
                )

            return {
                profile_name: ProfileConfig(**profile)
                for profile_name, profile in toml_data["profiles"].items()
            }

        except FileNotFoundError:
            raise ProfileNotFoundException("Config file not found.")
        except TOMLDecodeError:
            raise ProfileException("Bad toml file.")

    def load(self, profile_name: str | None = None) -> ProfileConfig:
        profiles = self.loads()

        if profile_name:
            try:
                if f"{profile_name}:default" in profiles:
                    return profiles[f"{profile_name}:default"]
                else:
                    return profiles[profile_name]
            except KeyError:
                raise ProfileException(
                    "Specified profile name not found in config."
                )

        else:
            try:
                default = [n for n in profiles.keys() if n.endswith("default")][
                    0
                ]
                return profiles[default]
            except IndexError:
                raise ProfileException(
                    "Default profile config not found. You can configure profile by running `ktctl profile`"
                )

    def _save_toml(self, data: dict[str, ProfileConfig]) -> None:
        os.makedirs(self._profile_path[:-8], exist_ok=True)
        toml.dump(
            {
                "profiles": {
                    profile_name: asdict(profile)
                    for profile_name, profile in data.items()
                }
            },
            open(self._profile_path, "w"),
        )

    def save(
        self,
        ctx: click.Context,
    ) -> None:
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
                    "\nValidation Error: Server URL must be start with protocol [http://|https://]\n",
                    err=True,
                )
                return prompt_server_url(ctx, click.prompt(msg))

        profiles: dict[str, ProfileConfig] = {}
        try:
            profiles = self.loads()
        except ProfileNotFoundException:
            pass

        profile_name = click.prompt(
            "profile name: ",
        )
        server_url = prompt_server_url(ctx)
        user_name = click.prompt(
            "user name: ",
        )
        password = click.prompt("password: ", hide_input=True)
        profile = ProfileConfig(
            server_url=server_url, user_name=user_name, password=password
        )

        profiles[profile_name] = profile
        self._save_toml(profiles)

        click.echo(f"Profile `{profile_name}` saved.")

    def remove(self, name: str) -> None:
        profiles = self.loads()

        name_to_show = deepcopy(name)
        if f"{name}:default" in profiles:
            name = f"{name}:default"
        elif name not in profiles:
            raise ProfileException(
                "Specified profile name not found in config."
            )

        if click.confirm(
            f"Do you really want to remove profile `{name_to_show}` ?"
        ):

            del profiles[name]
            self._save_toml(profiles)

            click.echo(f"Profile `{name_to_show}` removed.")

    def list_profile(self) -> None:
        profiles = self.loads()

        click.echo(
            tabulate(
                [
                    [name, profile.server_url, profile.user_name]
                    for name, profile in profiles.items()
                ],
                ["Profile Name", "Server URL", "User Name"],
            )
        )

    def set_default(self, ctx: click.Context, name: str) -> None:
        profiles = self.loads()
        default = None

        try:
            default = [n for n in profiles.keys() if n.endswith("default")][0]
        except IndexError:
            pass

        if name not in profiles and f"{name}:default" not in profiles:
            raise ProfileException("Specified profile not found.")

        if default:
            if name == default.split(":")[0]:
                raise ProfileException(
                    "Specified profile name is already set as default."
                )
            if click.confirm(
                f"Profile {default.split(':')[0]} is already set as default.\nDo you want to set profile {name} as default?"
            ):
                p = deepcopy(profiles)
                del profiles[name]
                profiles[f"{name}:default"] = p[name]
                del profiles[default]
                profiles[default.split(":")[0]] = p[default]

                self._save_toml(profiles)
            else:
                ctx.exit(0)
        else:

            p = deepcopy(profiles)
            del profiles[name]
            profiles[f"{name}:default"] = p[name]

            self._save_toml(profiles)

        click.echo(f"Set profile `{name}` as default.")
