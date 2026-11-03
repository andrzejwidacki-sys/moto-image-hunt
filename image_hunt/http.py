"""Small polite HTTP client: retries, per-host spacing, readable errors."""
from __future__ import annotations

import sys
import time
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HttpError(Exception):
    def __init__(self, status: int, url: str, body: str = ""):
        super().__init__(f"HTTP {status} for {url}: {body[:200]}")
        self.status = status
        self.url = url
        self.body = body


class Http:
    def __init__(self, user_agent: str, min_interval: float = 0.25, verbose: bool = False):
        self.verbose = verbose
        self.deadline: float | None = None  # time.monotonic() value; set per source by the runner
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        retry = Retry(
            total=4,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.min_interval = min_interval
        self._last: dict[str, float] = {}

    def _check_deadline(self, url: str) -> None:
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise HttpError(0, url, "source time budget exceeded")

    def _log(self, status, started: float, url: str, params: dict | None) -> None:
        if self.verbose:
            parts = urlsplit(url)
            q = (params or {}).get("q") or (params or {}).get("srsearch") or (params or {}).get("cmtitle") or ""
            print(f"[http] {status} {time.monotonic() - started:5.1f}s {parts.netloc}{parts.path} {str(q)[:60]}",
                  file=sys.stderr, flush=True)

    def _wait(self, url: str, interval: float | None = None) -> None:
        host = urlsplit(url).netloc
        gap = self.min_interval if interval is None else interval
        wait = self._last.get(host, 0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    def get_json(self, url: str, params: dict | None = None, headers: dict | None = None,
                 interval: float | None = None, timeout: int = 40) -> dict:
        self._check_deadline(url)
        self._wait(url, interval)
        self._check_deadline(url)
        started = time.monotonic()
        try:
            r = self.session.get(url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            self._log("ERR", started, url, params)
            raise HttpError(0, url, str(exc)) from exc
        self._log(r.status_code, started, url, params)
        if r.status_code >= 400:
            raise HttpError(r.status_code, r.url, r.text)
        try:
            return r.json()
        except ValueError as exc:
            raise HttpError(r.status_code, r.url, "response is not JSON: " + r.text[:120]) from exc

    def post_form(self, url: str, data: dict, timeout: int = 40) -> dict:
        self._wait(url)
        try:
            r = self.session.post(url, data=data, timeout=timeout)
        except requests.RequestException as exc:
            raise HttpError(0, url, str(exc)) from exc
        if r.status_code >= 400:
            raise HttpError(r.status_code, r.url, r.text)
        return r.json()
