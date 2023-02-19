import click
import requests
from bs4 import BeautifulSoup

from .profile import ProfileConfig
from .util import Logger

logger = Logger().get_logger()


class KtistecHandlerException(Exception):
    pass


class KtistecHandler:
    def __init__(self, ctx: click.Context, profile: ProfileConfig):
        self._profile = profile
        self.ctx = ctx
        self._session = requests.session()
        self._headers = {
            "accept": "text/html",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self._sessions_url = self._profile.server_url + "/sessions"
        self._auth_token = ""

    def _get_csrf_token(self, url) -> str:
        res = self._session.get(
            url=url,
            headers=self._headers,
        )
        logger.debug(res.status_code)
        logger.debug(res.text)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        token: str = soup.find(
            "input", attrs={"name": "authenticity_token", "type": "hidden"}
        ).get(  # type: ignore
            "value"
        )

        if len(token) <= 0:
            raise KtistecHandlerException("Failed to get CSRF Token.")

        return token

    def _login(self) -> None:
        token = self._get_csrf_token(self._sessions_url)
        res = self._session.post(
            url=self._sessions_url,
            headers=self._headers,
            data={
                "username": self._profile.user_name,
                "password": self._profile.password,
                "authenticity_token": token,
            },
        )
        logger.debug(res.status_code)
        logger.debug(res.text)
        res.raise_for_status()

    def post(self, message: str, link: list[str]) -> None:
        self._login()
        token = self._get_csrf_token(self._profile.server_url)
        link_tags = "".join([f'<br><a href="{url}">{url}</a>' for url in link])

        res = self._session.post(
            url=f"{self._profile.server_url}/actors/{self._profile.user_name}/outbox",
            headers=self._headers,
            data={
                "type": "Publish",
                "public": True,
                "content": f"<div>{message}{link_tags}</div>",
                "authenticity_token": token,
            },
        )
        logger.debug(f"<div>{message}{link_tags}</div>")
        logger.debug(res.status_code)
        logger.debug(res.text)
        res.raise_for_status()
