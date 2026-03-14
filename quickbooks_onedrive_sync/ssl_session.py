"""Shared requests Session factory with TLS + proxy support.

In environments that use a TLS-inspecting proxy (e.g. this sandbox),
the proxy's CA certificate must be trusted explicitly and the proxy
URL must be passed to urllib3.  This module centralises that logic so
every HTTP client (qb_time, onedrive) works out of the box.

The combined CA bundle is built once at import time from:
  1. /usr/local/share/ca-certificates/swp-ca-production.crt  (sandbox proxy CA)
  2. certifi's default bundle                                  (public CAs)

On a normal machine neither file causes issues — the sandbox CA won't
exist and certifi's bundle is used as-is.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

_SANDBOX_CA = Path("/usr/local/share/ca-certificates/swp-ca-production.crt")
_COMBINED_CA: str | None = None


def _build_ca_bundle() -> str:
    """Return path to a CA bundle that includes the sandbox proxy CA if present."""
    global _COMBINED_CA
    if _COMBINED_CA and Path(_COMBINED_CA).exists():
        return _COMBINED_CA

    certifi_bundle = certifi.where()

    if not _SANDBOX_CA.exists():
        _COMBINED_CA = certifi_bundle
        return _COMBINED_CA

    # Write combined bundle to a temp file (persists for the process lifetime)
    tmp = tempfile.NamedTemporaryFile(
        prefix="combined-ca-", suffix=".pem", delete=False
    )
    tmp.write(_SANDBOX_CA.read_bytes())
    tmp.write(Path(certifi_bundle).read_bytes())
    tmp.flush()
    tmp.close()
    _COMBINED_CA = tmp.name
    return _COMBINED_CA


class _ProxySSLAdapter(HTTPAdapter):
    """HTTPAdapter that injects a custom ssl_context into every connection pool."""

    def __init__(self, ca_bundle: str, *args, **kwargs) -> None:
        self._ca_bundle = ca_bundle
        super().__init__(*args, **kwargs)

    def _ssl_ctx(self):
        ctx = create_urllib3_context()
        ctx.load_verify_locations(self._ca_bundle)
        return ctx

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._ssl_ctx()
        super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **kwargs):
        kwargs["ssl_context"] = self._ssl_ctx()
        return super().proxy_manager_for(proxy, **kwargs)


def build_session(headers: dict | None = None) -> requests.Session:
    """Return a Session pre-configured with proxy and CA bundle."""
    ca_bundle = _build_ca_bundle()
    session = requests.Session()
    adapter = _ProxySSLAdapter(ca_bundle)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Pick up proxy from environment (requests reads https_proxy / HTTPS_PROXY)
    # Explicit proxy dict ensures both lower- and upper-case env vars are honoured.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    if proxy:
        session.proxies.update({"https": proxy, "http": proxy})

    if headers:
        session.headers.update(headers)

    return session
