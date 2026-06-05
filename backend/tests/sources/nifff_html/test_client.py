from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from app.sources.nifff_html.client import USER_AGENT, build_session, fetch_html


def test_build_session_sets_user_agent() -> None:
    session = build_session()

    assert isinstance(session, requests.Session)
    assert session.headers["User-Agent"] == USER_AGENT


def test_fetch_html_returns_response_text() -> None:
    session = Mock(spec=requests.Session)
    response = Mock()
    response.text = "<html>ok</html>"
    session.get.return_value = response

    html = fetch_html(session, "https://example.test/catalog")

    assert html == "<html>ok</html>"
    session.get.assert_called_once_with("https://example.test/catalog", timeout=30)
    response.raise_for_status.assert_called_once_with()


def test_fetch_html_propagates_http_error() -> None:
    session = Mock(spec=requests.Session)
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("boom")
    session.get.return_value = response

    with pytest.raises(requests.HTTPError):
        fetch_html(session, "https://example.test/catalog")
