"""Snapshot a LIVE site into a ZIP (HTML + linked CSS/JS/images/fonts/PDFs) so the patch flow needs no repository.

For a hand-coded static site this reproduces the site files. It cannot see server-side code (PHP/ASP logic, form
handlers, hidden or unlinked files): those never leave the server. Only use it on sites you own or manage.
"""
from __future__ import annotations

import io
import os
import re
import time
import zipfile
from dataclasses import dataclass, field
from urllib.parse import unquote, urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..constants import TEXT_EXT
from .crawler import HEADERS, _host, normalize_url

PAGE_EXT = {"", ".html", ".htm", ".php", ".asp", ".aspx"}
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"}
SKIP_PREFIX = ("data:", "mailto:", "tel:", "javascript:", "#", "blob:")
CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")\s]+)['\"]?\s*\)", re.I)
CSS_IMPORT_RE = re.compile(r"@import\s+(?:url\()?\s*['\"]([^'\"]+)['\"]", re.I)


@dataclass
class Snapshot:
    zip_bytes: bytes = b""
    files: dict[str, str] = field(default_factory=dict)  # text files that can be patched
    binaries: list[str] = field(default_factory=list)  # images, fonts, pdfs... (kept in the ZIP, never edited)
    warnings: list[str] = field(default_factory=list)
    pages: int = 0
    total_bytes: int = 0


def url_to_path(url: str, content_type: str = "") -> tuple[str | None, str | None]:
    """Map a URL to a relative file path. Returns (path, warning)."""
    p = unquote(urlparse(url).path)
    if ".." in p.split("/") or "\\" in p or len(p) > 300:
        return None, f"Skipped suspicious path: {url}"
    if p == "" or p.endswith("/"):
        return p.lstrip("/") + "index.html", None
    name = p.rsplit("/", 1)[-1]
    if "." not in name:
        if "html" in content_type.lower():
            return p.lstrip("/") + ".html", f"{p} has no file extension; saved as {p.lstrip('/')}.html. Check how your host serves this URL before uploading."
        return p.lstrip("/"), None
    return p.lstrip("/"), None


def _add(lst: list[str], ref: str | None, base: str) -> None:
    if not ref:
        return
    ref = ref.strip()
    if not ref or ref.lower().startswith(SKIP_PREFIX):
        return
    full, _ = urldefrag(urljoin(base, ref))
    if urlparse(full).scheme in ("http", "https") and _host(full) == _host(base):
        lst.append(normalize_url(full))


def css_refs(css: str, base: str) -> list[str]:
    out: list[str] = []
    for m in list(CSS_URL_RE.finditer(css)) + list(CSS_IMPORT_RE.finditer(css)):
        _add(out, m.group(1), base)
    return out


def extract_refs(html: str, base: str) -> tuple[list[str], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    pages: list[str] = []
    assets: list[str] = []
    for a in soup.find_all("a", href=True):
        tmp: list[str] = []
        _add(tmp, a["href"], base)
        for u in tmp:
            ext = os.path.splitext(urlparse(u).path)[1].lower()
            if ext in PAGE_EXT:
                pages.append(u)
            elif ext in DOC_EXT:
                assets.append(u)
    for tag, attr in (("link", "href"), ("script", "src"), ("img", "src"), ("source", "src"), ("video", "src"), ("video", "poster"), ("audio", "src")):
        for t in soup.find_all(tag):
            _add(assets, t.get(attr), base)
    for t in soup.find_all(["img", "source"]):
        for part in (t.get("srcset") or "").split(","):
            _add(assets, part.strip().split(" ")[0] if part.strip() else "", base)
    for st in soup.find_all("style"):
        assets.extend(css_refs(st.get_text(), base))
    for t in soup.find_all(style=True):
        assets.extend(css_refs(t["style"], base))
    return pages, assets


def snapshot_site(
    url: str,
    *,
    max_pages: int = 30,
    max_files: int = 600,
    max_total_mb: int = 60,
    max_file_mb: int = 10,
    delay: float = 0.1,
    session=None,
    progress=None,
) -> Snapshot:
    s = session or requests.Session()
    if hasattr(s, "headers"):
        s.headers.update(HEADERS)
    start = normalize_url(url if url.startswith("http") else "https://" + url)
    snap = Snapshot()
    raw: dict[str, bytes] = {}
    seen: set[str] = set()
    page_q, asset_q = [start], []
    limit_total, limit_file = max_total_mb * 1024 * 1024, max_file_mb * 1024 * 1024

    def store(u: str, resp, ctype: str) -> bool:
        path, warn = url_to_path(u, ctype)
        if warn:
            snap.warnings.append(warn)
        if path is None or path in raw:
            return False
        body = resp.content
        if len(body) > limit_file:
            snap.warnings.append(f"Skipped (over {max_file_mb} MB): {path}")
            return False
        if snap.total_bytes + len(body) > limit_total:
            snap.warnings.append(f"Stopped adding files: size limit of {max_total_mb} MB reached at {path}")
            return False
        raw[path] = body
        snap.total_bytes += len(body)
        return True

    def fetch(u: str):
        try:
            r = s.get(u, timeout=25, allow_redirects=True)
        except Exception as exc:
            snap.warnings.append(f"Could not fetch {u}: {exc}")
            return None
        if r.status_code != 200:
            snap.warnings.append(f"HTTP {r.status_code} for {u}")
            return None
        if _host(r.url) != _host(u):
            snap.warnings.append(f"Redirected off-site, skipped: {u}")
            return None
        return r

    # ---- pages (breadth-first)
    while page_q and snap.pages < max_pages and len(raw) < max_files:
        u = page_q.pop(0)
        if u in seen:
            continue
        seen.add(u)
        r = fetch(u)
        if r is None:
            continue
        ctype = r.headers.get("content-type", "")
        if "html" not in ctype.lower():
            asset_q.append(u)
            continue
        if not store(u, r, ctype):
            continue
        snap.pages += 1
        if os.path.splitext(urlparse(u).path)[1].lower() in (".php", ".asp", ".aspx"):
            snap.warnings.append(f"{u} is a dynamic page: the saved copy is rendered HTML, so server-side logic would be lost if you overwrite it. Leave it out of uploads.")
        pg, assets = extract_refs(r.text, r.url)
        page_q.extend(x for x in pg if x not in seen)
        asset_q.extend(assets)
        if progress:
            progress(snap.pages, max_pages, u)
        if delay:
            time.sleep(delay)

    # ---- well-known files
    for extra in ("/robots.txt", "/sitemap.xml"):
        full = urljoin(start, extra)
        r = fetch(full)
        if r is not None and "html" not in r.headers.get("content-type", "").lower():
            store(full, r, r.headers.get("content-type", ""))

    # ---- assets (CSS is parsed for url() references)
    while asset_q and len(raw) < max_files:
        u = asset_q.pop(0)
        if u in seen:
            continue
        seen.add(u)
        r = fetch(u)
        if r is None:
            continue
        ctype = r.headers.get("content-type", "")
        if not store(u, r, ctype):
            continue
        if os.path.splitext(urlparse(u).path)[1].lower() == ".css":
            try:
                asset_q.extend(x for x in css_refs(r.content.decode("utf-8", errors="ignore"), r.url) if x not in seen)
            except Exception:
                pass
        if delay:
            time.sleep(delay / 2)
    if asset_q:
        snap.warnings.append(f"File limit reached ({max_files}); {len(asset_q)} asset(s) were not downloaded.")

    # ---- split text (patchable) vs binary, build ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, body in sorted(raw.items()):
            z.writestr(path, body)
            if os.path.splitext(path)[1].lower() in TEXT_EXT:
                try:
                    snap.files[path] = body.decode("utf-8")
                    continue
                except UnicodeDecodeError:
                    snap.warnings.append(f"{path} is not UTF-8 text; it will be kept but not patched.")
            snap.binaries.append(path)
    snap.zip_bytes = buf.getvalue()
    if snap.pages == 0:
        snap.warnings.append("No pages could be downloaded. Check the URL and that the site is online.")
    return snap
