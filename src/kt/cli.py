import os
import tempfile
from subprocess import call

import click

from .ktistec_handler import KtistecHandler
from .message_builder import MessageBuilder
from .profile import Profile, ProfileNotFoundException

__all__ = ["main"]

EDITOR = os.environ.get("EDITOR", "vim")

initial_message = ""


@click.command()
@click.option("--post", "-p", type=str)
@click.option("--edit", "-e", is_flag=True)
@click.option("--debug", is_flag=True)
@click.option("--profile", type=str)
@click.pass_context
def main(
    ctx: click.Context,
    post: str | None,
    profile: str | None,
    edit: bool,
    debug: bool,
) -> None:
    # check profile exists
    p = Profile()

    try:
        current_profile = p.load(profile)
    except ProfileNotFoundException as e:
        click.echo(str(e), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(str(e))
        ctx.exit(1)

    post_message = ""

    if not post and not edit:
        click.echo("Please input post content.")
        ctx.exit(1)

    if edit:
        with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
            tf.write(initial_message.encode())
            tf.flush()
            call([EDITOR, tf.name])

            with open(tf.name, "r") as f:
                post_message = f.read()

    else:
        if post:
            post_message = post
        else:
            click.echo("Please input post content.")

    mb = MessageBuilder(post_message)
    built_message = mb.build()

    try:
        handler = KtistecHandler(ctx, current_profile)
        handler.post(built_message)
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
def remove(name: str, debug: bool):
    profile = Profile()
    try:
        profile.remove(name)
    except Exception as e:
        click.echo(str(e), err=True)
        if debug:
            raise e


@profile.command(name="list")
@click.option("--debug", is_flag=True)
def list_cmd(debug: bool):
    profile = Profile()
    try:
        profile.list_profile()
    except Exception as e:
        click.echo(str(e), err=True)
        if debug:
            raise e


@profile.command(name="set-default")
@click.option("--name", type=str)
@click.option("--debug", is_flag=True)
@click.pass_context
def set_default(ctx: click.Context, name: str, debug: bool):
    profile = Profile()
    try:
        profile.set_default(ctx, name)
    except Exception as e:
        click.echo(str(e), err=True)
        if debug:
            raise e
