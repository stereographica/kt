import io
import os
from unittest.mock import Mock, mock_open, patch

import click
import pytest

from src.kt.profile import (
    Profile,
    ProfileConfig,
    ProfileException,
    ProfileNotFoundException,
)


class TestProfile:
    @pytest.fixture
    def dummy_profile(self):
        return open(
            f"{os.getcwd()}/tests/resources/profile/dummy_profile", "rb"
        ).read()

    @pytest.fixture
    def dummy_profile_configs(self):
        return {
            "foo:default": ProfileConfig(
                server_url="https://one.example.com",
                user_name="test_user_one",
                password="test_passwd_one",
            ),
            "bar": ProfileConfig(
                server_url="https://two.example.com",
                user_name="test_user_two",
                password="test_passwd_two",
            ),
        }

    @patch("os.path.expanduser")
    def test_loads_success(
        self, mock_expanduser, dummy_profile, dummy_profile_configs
    ):
        mock_io = mock_open(read_data=dummy_profile)
        mock_expanduser.return_value = "/home/test_user"
        with patch("builtins.open", mock_io):
            target = Profile()
            res = target.loads()
            mock_io.assert_called_once_with("/home/test_user/.kt/profile", "rb")
            assert res == dummy_profile_configs

    @patch("os.path.expanduser")
    def test_loads_file_not_found(
        self,
        mock_expanduser,
    ):
        mock_io = mock_open()
        mock_io.side_effect = FileNotFoundError
        mock_expanduser.return_value = "/home/test_user"
        with patch("builtins.open", mock_io):
            target = Profile()
            with pytest.raises(ProfileNotFoundException) as e:
                target.loads()
                assert str(e) == "Config file not found."

    @patch("os.path.expanduser")
    def test_loads_bad_toml_file(self, mock_expanduser):
        mock_io = mock_open(read_data=b"foobar")
        mock_expanduser.return_value = "/home/test_user"
        with patch("builtins.open", mock_io):
            target = Profile()
            with pytest.raises(ProfileException) as e:
                target.loads()
                assert str(e) == "Bad toml file."

    def test_load_specify_profile_name_success(self, dummy_profile_configs):
        mock_loads = Mock()
        mock_loads.return_value = dummy_profile_configs
        with patch("src.kt.profile.Profile.loads", mock_loads):
            target = Profile()
            res = target.load("bar")
            assert res == dummy_profile_configs["bar"]

    def test_load_specify_default_profile_name_success(
        self, dummy_profile_configs
    ):
        mock_loads = Mock()
        mock_loads.return_value = dummy_profile_configs
        with patch("src.kt.profile.Profile.loads", mock_loads):
            target = Profile()
            res = target.load("foo")
            assert res == dummy_profile_configs["foo:default"]

    def test_load_specify_profile_name_not_found(self, dummy_profile_configs):
        mock_loads = Mock()
        mock_loads.return_value = dummy_profile_configs
        with patch("src.kt.profile.Profile.loads", mock_loads):
            target = Profile()
            with pytest.raises(ProfileException) as e:
                target.load("baz")
                assert str(e) == "Specified profile name not found in config."

    def test_load_default_profile_success(self, dummy_profile_configs):
        mock_loads = Mock()
        mock_loads.return_value = dummy_profile_configs
        with patch("src.kt.profile.Profile.loads", mock_loads):
            target = Profile()
            res = target.load()
            assert res == dummy_profile_configs["foo:default"]

    def test_load_default_profile_not_found(self, dummy_profile_configs):
        mock_loads = Mock()
        mock_loads.return_value = dummy_profile_configs
        del dummy_profile_configs["foo:default"]
        with patch("src.kt.profile.Profile.loads", mock_loads):
            target = Profile()
            with pytest.raises(ProfileException) as e:
                target.load()
                assert (
                    str(e)
                    == "Default profile config not found. You can configure profile by running `ktctl profile add`"
                )

    @patch("os.makedirs")
    @patch("os.path.expanduser")
    def test_save_toml(
        self,
        mock_expanduser,
        mock_makedirs,
        dummy_profile,
        dummy_profile_configs,
    ):
        mock_io = mock_open()
        mock_expanduser.return_value = "/home/test_user"
        with patch("builtins.open", mock_io):
            target = Profile()
            target._save_toml(dummy_profile_configs)
            mock_makedirs.assert_called_once_with(
                "/home/test_user/.kt", exist_ok=True
            )
            mock_io.assert_called_once_with("/home/test_user/.kt/profile", "w")
            mock_io.__call__().write.assert_called_once_with(
                dummy_profile.decode()
            )

    def test_save_success(self, dummy_profile_configs, monkeypatch):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs
        target._save_toml = Mock()

        dummy_profile_configs["test_profile_name"] = ProfileConfig(
            server_url="https://example.com",
            user_name="test_user_name",
            password="test_passwd",
        )

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(
                "test_profile_name\nhttps://example.com\ntest_user_name\n"
            ),
        )
        with patch("getpass.getpass", side_effect=["test_passwd"]):
            target.save(click.Context(command=click.Command("test")))

        target.loads.assert_called()
        target._save_toml.assert_called_with(dummy_profile_configs)

    def test_save_success_file_not_found(self, monkeypatch):
        target = Profile()
        target.loads = Mock()
        target.loads.side_effect = ProfileNotFoundException
        target._save_toml = Mock()

        profile_configs = {}
        profile_configs["test_profile_name"] = ProfileConfig(
            server_url="https://example.com",
            user_name="test_user_name",
            password="test_passwd",
        )

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(
                "test_profile_name\nhttps://example.com\ntest_user_name\n"
            ),
        )
        with patch("getpass.getpass", side_effect=["test_passwd"]):
            target.save(click.Context(command=click.Command("test")))

        target.loads.assert_called()
        target._save_toml.assert_called_with(profile_configs)

    def test_save_success_on_second_server_url_input(
        self, dummy_profile_configs, monkeypatch
    ):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs
        target._save_toml = Mock()

        dummy_profile_configs["test_profile_name"] = ProfileConfig(
            server_url="https://example.com",
            user_name="test_user_name",
            password="test_passwd",
        )

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(
                "test_profile_name\nexample.com\nhttps://example.com\ntest_user_name\n"
            ),
        )
        with patch("getpass.getpass", side_effect=["test_passwd"]):
            target.save(click.Context(command=click.Command("test")))

        target.loads.assert_called()
        target._save_toml.assert_called_with(dummy_profile_configs)

    def test_save_validation_error_server_url(
        self, dummy_profile_configs, monkeypatch, capsys
    ):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs
        target._save_toml = Mock()

        dummy_profile_configs["test_profile_name"] = ProfileConfig(
            server_url="https://example.com",
            user_name="test_user_name",
            password="test_passwd",
        )

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("test_profile_name\nexample.com\n"),
        )

        try:
            target.save(click.Context(command=click.Command("test")))
        except click.exceptions.Abort:
            pass

        captured = capsys.readouterr()

        assert (
            captured.err
            == "\nValidation Error: Server URL must be start with protocol [http://|https://]\n\n"
        )

        assert (
            captured.out
            == "profile name: : ktistec server url: : ktistec server url: : "
        )

        target._save_toml.assert_not_called()

    def test_remove_success(self, dummy_profile_configs, monkeypatch, capsys):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs
        target._save_toml = Mock()

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("y\n"),
        )

        try:
            target.remove("bar")
        except click.exceptions.Abort:
            pass

        target.loads.assert_called()

        captured = capsys.readouterr()

        assert (
            captured.out
            == "Do you really want to remove profile `bar` ? [y/N]: Profile `bar` removed.\n"
        )

        target._save_toml.assert_called_once_with(
            {
                "foo:default": ProfileConfig(
                    server_url="https://one.example.com",
                    user_name="test_user_one",
                    password="test_passwd_one",
                ),
            }
        )

    def test_remove_default_success(
        self, dummy_profile_configs, monkeypatch, capsys
    ):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs
        target._save_toml = Mock()

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("y\n"),
        )

        try:
            target.remove("foo")
        except click.exceptions.Abort:
            pass

        target.loads.assert_called()

        captured = capsys.readouterr()

        assert (
            captured.out
            == "Do you really want to remove profile `foo` ? [y/N]: Profile `foo` removed.\n"
        )

        target._save_toml.assert_called_once_with(
            {
                "bar": ProfileConfig(
                    server_url="https://two.example.com",
                    user_name="test_user_two",
                    password="test_passwd_two",
                ),
            }
        )

    def test_remove_cancel(self, dummy_profile_configs, monkeypatch, capsys):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs
        target._save_toml = Mock()

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("n\n"),
        )

        try:
            target.remove("foo")
        except click.exceptions.Abort:
            pass

        target.loads.assert_called()

        captured = capsys.readouterr()

        assert (
            captured.out
            == "Do you really want to remove profile `foo` ? [y/N]: "
        )

        target._save_toml.assert_not_called()

    def test_remove_not_found(self, dummy_profile_configs, monkeypatch, capsys):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs
        target._save_toml = Mock()

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("\n"),
        )

        with pytest.raises(ProfileException) as e:
            try:
                target.remove("not_found")
            except click.exceptions.Abort:
                pass

            assert str(e) == "Specified profile name not found in config."

    def test_list_profile(self, dummy_profile_configs, capsys):
        target = Profile()
        target.loads = Mock()
        target.loads.return_value = dummy_profile_configs

        target.list_profile()

        captured = capsys.readouterr()

        assert (
            captured.out
            == """Profile Name    Server URL               User Name
--------------  -----------------------  -------------
foo:default     https://one.example.com  test_user_one
bar             https://two.example.com  test_user_two
"""
        )

    def test_set_default(self, dummy_profile_configs, capsys, monkeypatch):
        target = Profile()
        target.loads = Mock()
        target._save_toml = Mock()
        target.loads.return_value = dummy_profile_configs

        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("y\n"),
        )

        target.set_default(click.Context(command=click.Command("test")), "bar")

        captured = capsys.readouterr()
        assert (
            captured.out
            == "Profile foo is already set as default.\nDo you want to set profile bar as default? [y/N]: Set profile `bar` as default.\n"
        )

        target._save_toml.assert_called_once_with(
            {
                "foo": ProfileConfig(
                    server_url="https://one.example.com",
                    user_name="test_user_one",
                    password="test_passwd_one",
                ),
                "bar:default": ProfileConfig(
                    server_url="https://two.example.com",
                    user_name="test_user_two",
                    password="test_passwd_two",
                ),
            }
        )

    def test_set_default_already_default(
        self, dummy_profile_configs, capsys, monkeypatch
    ):
        target = Profile()
        target.loads = Mock()
        target._save_toml = Mock()
        target.loads.return_value = dummy_profile_configs

        with pytest.raises(ProfileException) as e:
            target.set_default(
                click.Context(command=click.Command("test")), "foo"
            )
            assert str(e) == "Specified profile name is already set as default."

    def test_set_default_no_specified_profile(
        self, dummy_profile_configs, capsys, monkeypatch
    ):
        target = Profile()
        target.loads = Mock()
        target._save_toml = Mock()
        target.loads.return_value = dummy_profile_configs

        with pytest.raises(ProfileException) as e:
            target.set_default(
                click.Context(command=click.Command("test")), "baz"
            )
            assert str(e) == "Specified profile not found."

    def test_set_default_no_default(self):
        target = Profile()
        target.loads = Mock()
        target._save_toml = Mock()
        target.loads.return_value = {
            "foo": ProfileConfig(
                server_url="https://one.example.com",
                user_name="test_user_one",
                password="test_passwd_one",
            ),
            "bar": ProfileConfig(
                server_url="https://two.example.com",
                user_name="test_user_two",
                password="test_passwd_two",
            ),
        }

        target.set_default(click.Context(command=click.Command("test")), "bar")
        target._save_toml.assert_called_once_with(
            {
                "foo": ProfileConfig(
                    server_url="https://one.example.com",
                    user_name="test_user_one",
                    password="test_passwd_one",
                ),
                "bar:default": ProfileConfig(
                    server_url="https://two.example.com",
                    user_name="test_user_two",
                    password="test_passwd_two",
                ),
            }
        )

    def test_set_default_no_config(self):
        target = Profile()
        target.loads = Mock()
        target._save_toml = Mock()
        target.loads.return_value = {}

        with pytest.raises(ProfileException) as e:
            target.set_default(
                click.Context(command=click.Command("test")), "bar"
            )
            assert str(e) == "Specified profile not found."
