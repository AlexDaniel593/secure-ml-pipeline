"""Envía notificaciones a Telegram.

Responsabilidad única (SRP): dado un texto y credenciales, enviar
un mensaje a un chat específico. Sin lógica de negocio, sin estado.

Uso:
    export TELEGRAM_BOT_TOKEN=...
    export TELEGRAM_CHAT_ID=...
    python -m scripts.telegram_notify "Inicio de revisión"
    echo "mensaje" | python -m scripts.telegram_notify

Códigos de salida:
    0  mensaje enviado
    1  faltan variables de entorno
    2  no se proporcionó texto
    3  error de red / API
"""

from __future__ import annotations

import os
import sys

import requests

API_BASE = "https://api.telegram.org"
EXIT_OK = 0
EXIT_MISSING_ENV = 1
EXIT_NO_TEXT = 2
EXIT_NETWORK = 3


def send_message(token: str, chat_id: str, text: str, parse_mode: str | None = None) -> bool:
    """Envía un mensaje. Devuelve True si fue exitoso, False en caso contrario."""
    url = f"{API_BASE}/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        print(f"[telegram_notify] Error enviando mensaje: {exc}", file=sys.stderr)
        return False


def read_text() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    if not sys.stdin.isatty():
        return sys.stdin.read().rstrip("\n")
    print(
        "Uso: python -m scripts.telegram_notify <mensaje>  o  echo 'msg' | python -m scripts.telegram_notify",
        file=sys.stderr,
    )
    raise SystemExit(EXIT_NO_TEXT)


def get_credentials() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(
            "Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en el entorno.",
            file=sys.stderr,
        )
        raise SystemExit(EXIT_MISSING_ENV)
    return token, chat_id


def main() -> int:
    token, chat_id = get_credentials()
    text = read_text()
    return EXIT_OK if send_message(token, chat_id, text) else EXIT_NETWORK


if __name__ == "__main__":
    raise SystemExit(main())
