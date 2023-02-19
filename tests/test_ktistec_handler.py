import os
from unittest import mock
from unittest.mock import patch

import click
import pytest
import requests_mock
from requests import Session

from src.kt.ktistec_handler import KtistecHandler, KtistecHandlerException
from src.kt.profile import ProfileConfig


class TestKtistecHandler:
    @pytest.fixture
    def profile_config(self):
        return ProfileConfig(
            server_url="https://one.example.com",
            user_name="test_user_one",
            password="test_passwd_one",
        )

    @pytest.fixture
    def sessions_response_body(self):
        return open(
            f"{os.getcwd()}/tests/resources/ktistec_handler/dummy_sessions_response_body",
            "r",
        ).read()

    @pytest.fixture
    def target(self, profile_config):
        return KtistecHandler(
            ctx=click.Context(command=click.Command("test")),
            profile=profile_config,
        )

    @requests_mock.Mocker(kw="mock")
    def test_get_csrf_token_success(
        self, target, sessions_response_body, **kwargs
    ):
        url = "https://one.example.com"
        kwargs["mock"].get(
            url,
            text=sessions_response_body,
        )

        assert target._get_csrf_token(url) == "beb886633614303dd2c5774a25a347ee"

    @requests_mock.Mocker(kw="mock")
    def test_get_csrf_token_fail(
        self, target, sessions_response_body, **kwargs
    ):
        sessions_response_body = sessions_response_body.replace(
            "beb886633614303dd2c5774a25a347ee", ""
        )
        url = "https://one.example.com"
        kwargs["mock"].get(
            url,
            text=sessions_response_body,
        )

        with pytest.raises(KtistecHandlerException) as e:
            target._get_csrf_token(url)
            assert str(e) == "Failed to get CSRF Token."

    @patch.object(Session, "post")
    def test_post_success(self, requests, target):
        target._login = mock.Mock()
        target._get_csrf_token = mock.Mock()
        target._get_csrf_token.return_value = "beb886633614303dd2c5774a25a347ee"

        target.post("test_message", [])

        requests.assert_called_once_with(
            url="https://one.example.com/actors/test_user_one/outbox",
            headers={
                "accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "type": "Publish",
                "public": True,
                "content": "<div>test_message</div>",
                "authenticity_token": "beb886633614303dd2c5774a25a347ee",
            },
        )

    @patch.object(Session, "post")
    def test_post_success_with_one_link(self, requests, target):
        target._login = mock.Mock()
        target._get_csrf_token = mock.Mock()
        target._get_csrf_token.return_value = "beb886633614303dd2c5774a25a347ee"

        target.post("test_message", ["http://example.com"])

        requests.assert_called_once_with(
            url="https://one.example.com/actors/test_user_one/outbox",
            headers={
                "accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "type": "Publish",
                "public": True,
                "content": '<div>test_message<br><a href="http://example.com">http://example.com</a></div>',
                "authenticity_token": "beb886633614303dd2c5774a25a347ee",
            },
        )

    @patch.object(Session, "post")
    def test_post_success_with_two_link(self, requests, target):
        target._login = mock.Mock()
        target._get_csrf_token = mock.Mock()
        target._get_csrf_token.return_value = "beb886633614303dd2c5774a25a347ee"

        target.post(
            "test_message", ["http://one.example.com", "http://two.example.com"]
        )

        requests.assert_called_once_with(
            url="https://one.example.com/actors/test_user_one/outbox",
            headers={
                "accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "type": "Publish",
                "public": True,
                "content": '<div>test_message<br><a href="http://one.example.com">http://one.example.com</a><br><a href="http://two.example.com">http://two.example.com</a></div>',
                "authenticity_token": "beb886633614303dd2c5774a25a347ee",
            },
        )
