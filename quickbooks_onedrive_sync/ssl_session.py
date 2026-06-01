"""Builds a requests.Session for API calls."""

from __future__ import annotations

import requests


def build_session(headers: dict | None = None) -> requests.Session:
    s = requests.Session()
    if headers:
        s.headers.update(headers)
    return s
