from __future__ import annotations

import requests


USER_AGENT = "potential-spork/0.1 (+https://github.com/)"
DEFAULT_TIMEOUT_SECONDS = 30


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_html(session: requests.Session, url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text
