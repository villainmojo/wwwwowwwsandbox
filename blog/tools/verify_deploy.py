#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Post-deploy verification checks for SENGVIS Playground.

Requirements (from user):
- Check origin first (server-local) to bypass CDN cache.
- Also check public domain.
- Only warn (do not fail deploy). Always exit 0.

Origin check method:
- Request http://127.0.0.1/<path> with Host header set to the real domain.
  (Nginx commonly returns 403/404 without correct Host.)

Usage
  python3 blog/tools/verify_deploy.py

Optional env
  VERIFY_HOST=www.bimarchi-pg.com   (default)
  VERIFY_ORIGIN_IP=127.0.0.1       (default)
"""

from __future__ import annotations

import json
import os
import ssl
import time
import urllib.request
from urllib.error import URLError, HTTPError

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


VERIFY_HOST = os.environ.get("VERIFY_HOST", "bimarchi-pg.com")
VERIFY_ORIGIN_IP = os.environ.get("VERIFY_ORIGIN_IP", "127.0.0.1")

LIVE_ROOT = "/var/www/sengvis-playground"
LOCAL_INDEX_JSON = os.path.join(LIVE_ROOT, "blog", "posts", "index.json")

DEFAULT_CHECKS: list[tuple[str, str, str]] = [
    # (name, path, must_contain)
    ("home", "/", "Seungil"),
    ("v2home", "/v2home/", "SEUNGIL"),
    ("blog", "/blog/", "자유 실험실"),
    ("posts_index", "/blog/posts/index.json", '"posts"'),
    ("rss", "/blog/rss.xml", "<rss"),
    ("sitemap", "/sitemap.xml", "<urlset"),
]


def read_latest_post_id() -> int | None:
    try:
        with open(LOCAL_INDEX_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        posts = data.get("posts") or []
        if not posts:
            return None
        pid = posts[0].get("id")
        return pid if isinstance(pid, int) else None
    except Exception:
        return None


def contains(body: bytes, needle: str) -> bool:
    if not needle:
        return True
    try:
        return needle.encode("utf-8") in body
    except Exception:
        return False


def fetch_origin(path: str):
    # Do NOT follow redirects here; we want to validate the origin response.
    opener = urllib.request.build_opener(_NoRedirect())
    url = f"http://{VERIFY_ORIGIN_IP}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Host": VERIFY_HOST,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Connection": "close",
        },
    )
    t0 = time.time()
    try:
        r = opener.open(req, timeout=7.0)
        body = r.read(200_000)
        ms = int((time.time() - t0) * 1000)
        return r.status, body, ms
    except HTTPError as e:
        ms = int((time.time() - t0) * 1000)
        # still return the response body if present
        try:
            body = e.read(200_000) if getattr(e, 'fp', None) else b''
        except Exception:
            body = b''
        return int(getattr(e, 'code', 0) or 0), body, ms


def fetch_public(path: str):
    url = f"https://{VERIFY_HOST}{path}"
    req = urllib.request.Request(
        url,
        headers={
            # Cloudflare may block non-browser UAs; use a common UA.
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Connection": "close",
        },
    )
    t0 = time.time()
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=10.0, context=ctx) as r:
            body = r.read(200_000)
            ms = int((time.time() - t0) * 1000)
            return r.status, body, ms
    except HTTPError as e:
        ms = int((time.time() - t0) * 1000)
        try:
            body = e.read(200_000) if getattr(e, 'fp', None) else b''
        except Exception:
            body = b''
        return int(getattr(e, 'code', 0) or 0), body, ms


def run_check(kind: str, name: str, path: str, must: str):
    try:
        if kind == "origin":
            status, body, ms = fetch_origin(path)
        else:
            status, body, ms = fetch_public(path)
        # Public domain may return 403 due to Cloudflare bot protection.
        # Treat 403 as "reachable" (OK) but skip body-contains checks.
        if kind == "public" and status == 403:
            return True, status, ms

        # For origin checks, a redirect (301/302) is fine (often HTTP→HTTPS).
        if kind == "origin" and (300 <= status < 400):
            return True, status, ms

        ok = (200 <= status < 400) and contains(body, must)
        return ok, status, ms
    except URLError:
        return False, 0, -1
    except Exception:
        return False, 0, -1


def main() -> int:
    latest_id = read_latest_post_id()
    checks = list(DEFAULT_CHECKS)
    if latest_id:
        checks.insert(3, ("latest_post", f"/blog/{latest_id}/", "자유 실험실"))

    rows: list[tuple[str, str, str, bool, int, int]] = []
    warns = 0

    for kind in ("origin", "public"):
        for (name, path, must) in checks:
            ok, status, ms = run_check(kind, name, path, must)
            if not ok:
                warns += 1
            rows.append((kind, name, path, ok, status, ms))

    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    print(f"[verify] {ts} UTC")
    print(f"[verify] origin=http://{VERIFY_ORIGIN_IP} Host={VERIFY_HOST}")
    print(f"[verify] public=https://{VERIFY_HOST}")
    if latest_id:
        print(f"[verify] latest_post_id={latest_id}")

    for kind, name, path, ok, status, ms in rows:
        badge = "OK" if ok else "WARN"
        t = f"{ms}ms" if ms >= 0 else "-"
        print(f"[{badge}] {kind:6} {status:3} {t:>6} {path} ({name})")

    if warns:
        print(f"[verify] WARNINGS={warns} (deploy not failed by design)")
    else:
        print("[verify] OK")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
