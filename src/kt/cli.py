import click

from kt.ktistec_handler import KtistecHandler
from kt.profile import Profile, ProfileNotFoundException

__all__ = ["main"]


@click.command()
@click.argument("message")
@click.option("--link", "-l", multiple=True)
@click.option("--debug", is_flag=True)
@click.pass_context
def main(
    ctx: click.Context, message: str, link: list[str], debug: bool
) -> None:
    # check profile exists
    profile = Profile()

    try:
        current_profile = profile.load()
    except ProfileNotFoundException:
        profile.save(ctx)
        current_profile = profile.load()
    except Exception as e:
        click.echo(str(e))
        ctx.exit(1)

    try:
        handler = KtistecHandler(ctx, current_profile)
        handler.post(message, link)
    except Exception as e:
        click.echo(str(e), err=True)
        if debug:
            raise e

    ctx.exit(0)


@click.group()
def ctl_main():
    pass


@ctl_main.group()
def profile():
    pass


@profile.command()
@click.pass_context
def add(ctx: click.Context):
    profile = Profile()
    profile.save(ctx)


@profile.command()
@click.option("--name", required=True, type=str)
@click.option("--debug", is_flag=True)
@click.pass_context
def remove(ctx: click.Context, name: str, debug: bool):
    profile = Profile()
    try:
        profile.remove(name)
    except Exception as e:
        click.echo(str(e), err=True)
        if debug:
            raise e


@profile.command()
@click.option("--debug", is_flag=True)
@click.pass_context
def list(ctx: click.Context, debug: bool):
    profile = Profile()
    try:
        profile.list_profile()
    except Exception as e:
        click.echo(str(e), err=True)
        if debug:
            raise e
