"""Tests del notificador de Telegram (mockeados, no se llama a la API real)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from scripts.telegram_notify import (
    EXIT_MISSING_ENV,
    EXIT_NETWORK,
    EXIT_NO_TEXT,
    EXIT_OK,
    main,
    send_message,
)


def test_send_message_success():
    with patch("scripts.telegram_notify.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        ok = send_message("TOKEN", "12345", "hola")

        assert ok is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.args[0] == "https://api.telegram.org/botTOKEN/sendMessage"
        assert call_args.kwargs["json"]["chat_id"] == "12345"
        assert call_args.kwargs["json"]["text"] == "hola"
        assert call_args.kwargs["json"]["parse_mode"] == "HTML"


def test_send_message_http_error_returns_false():
    with patch("scripts.telegram_notify.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401")
        mock_post.return_value = mock_response

        assert send_message("t", "1", "x") is False


def test_send_message_connection_error_returns_false():
    with patch("scripts.telegram_notify.requests.post") as mock_post:
        mock_post.side_effect = requests.ConnectionError("network down")
        assert send_message("t", "1", "x") is False


def test_send_message_timeout_returns_false():
    with patch("scripts.telegram_notify.requests.post") as mock_post:
        mock_post.side_effect = requests.Timeout("timed out")
        assert send_message("t", "1", "x") is False


def test_main_missing_env(monkeypatch, capsys):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with patch("sys.argv", ["telegram_notify"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == EXIT_MISSING_ENV
    assert "Faltan" in capsys.readouterr().err


def test_main_only_token(monkeypatch, capsys):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with patch("sys.argv", ["telegram_notify"]):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == EXIT_MISSING_ENV


def test_main_no_text(monkeypatch, capsys):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    with patch("sys.argv", ["telegram_notify"]):
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with pytest.raises(SystemExit) as exc:
                main()
    assert exc.value.code == EXIT_NO_TEXT
    assert "Uso" in capsys.readouterr().err


def test_main_with_argv_message(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    with patch("sys.argv", ["telegram_notify", "hola", "mundo"]):
        with patch("scripts.telegram_notify.send_message", return_value=True) as mock_send:
            rc = main()
    assert rc == EXIT_OK
    mock_send.assert_called_once_with("abc", "123", "hola mundo")


def test_main_with_stdin_message(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    with patch("sys.argv", ["telegram_notify"]):
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            mock_stdin.read.return_value = "desde stdin\n"
            with patch("scripts.telegram_notify.send_message", return_value=True) as mock_send:
                rc = main()
    assert rc == EXIT_OK
    mock_send.assert_called_once_with("abc", "123", "desde stdin")


def test_main_network_error(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    with patch("sys.argv", ["telegram_notify", "msg"]):
        with patch("scripts.telegram_notify.send_message", return_value=False):
            rc = main()
    assert rc == EXIT_NETWORK
