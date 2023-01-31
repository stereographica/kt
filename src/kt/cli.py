import click

from kt.ktistec_handler import KtistecHandler
from kt.profile import Profile, ProfileNotFoundException

__all__ = ["main"]


@click.command()
@click.argument("message")
@click.option("--link", "-l", multiple=True)
@click.pass_context
def main(ctx: click.Context, message: str, link: list[str]) -> None:
    # check profile exists
    profile = Profile()

    try:
        current_profile = profile.load()
    except ProfileNotFoundException:
        profile.init(ctx)
        current_profile = profile.load()
    except Exception as e:
        click.echo(str(e))
        ctx.exit(1)

    try:
        handler = KtistecHandler(ctx, current_profile)
        handler.post(message, link)
    except Exception as e:
        click.echo(str(e))
        raise e
        # ctx.exit(1)

    ctx.exit(0)
