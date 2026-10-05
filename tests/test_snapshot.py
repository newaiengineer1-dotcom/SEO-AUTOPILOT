import io
import zipfile

from src.flows import build_patch
from src.tools import site_io
from src.tools.snapshot import extract_refs, snapshot_site, url_to_path
from tests.helpers import facts, filled_draft

PNG = b"\x89PNG\r\n\x1a\n\x00\x01"
HOME = """<!DOCTYPE html><html><head><title>Kunergy</title><meta name="viewport" content="width=device-width">
<link rel="stylesheet" href="css/style.css"><link rel="icon" href="/favicon.ico"></head>
<body><img src="images/png logo.png"><img src="/images/a.jpg" srcset="/images/a-2x.jpg 2x">
<a href="about.html">About</a> <a href="/brochure.pdf">PDF</a> <a href="https://other.com/x">ext</a> <a href="#contact">c</a> <a href="/old">old</a>
<h1>WELCOME</h1><p>Commerical solar</p><footer>&copy; 2024 Kunergy</footer></body></html>"""


class R:
    def __init__(self, body, ctype, url, status=200):
        self.content = body if isinstance(body, bytes) else body.encode()
        self.text, self.headers, self.url, self.status_code = self.content.decode("utf-8", "ignore"), {"content-type": ctype}, url, status


class Site:
    base = "https://site.test"
    routes = {
        "/": (HOME, "text/html"),
        "/about.html": ("<html><head><title>About us page</title></head><body><h1>About</h1></body></html>", "text/html"),
        "/old": ("<html><body><h1>Old</h1></body></html>", "text/html; charset=utf-8"),
        "/css/style.css": ("body{background:url(../images/bg.jpg)} @import 'extra.css';", "text/css"),
        "/css/extra.css": ("h1{color:red}", "text/css"),
        "/images/bg.jpg": (PNG, "image/jpeg"),
        "/images/png logo.png": (PNG, "image/png"),
        "/images/a.jpg": (PNG, "image/jpeg"),
        "/images/a-2x.jpg": (PNG, "image/jpeg"),
        "/favicon.ico": (PNG, "image/x-icon"),
        "/brochure.pdf": (b"%PDF-1.4", "application/pdf"),
        "/robots.txt": ("User-agent: *\n", "text/plain"),
    }
    headers = {}

    def get(self, url, **kw):
        from urllib.parse import unquote, urlparse

        path = unquote(urlparse(url).path) or "/"
        if path in self.routes:
            body, ct = self.routes[path]
            return R(body, ct, url)
        return R("nope", "text/html", url, 404)


def test_url_to_path():
    assert url_to_path("https://x.com/")[0] == "index.html"
    assert url_to_path("https://x.com/uae/")[0] == "uae/index.html"
    assert url_to_path("https://x.com/images/png%20logo.png")[0] == "images/png logo.png"
    path, warn = url_to_path("https://x.com/old", "text/html")
    assert path == "old.html" and warn
    assert url_to_path("https://x.com/a/../b")[0] is None


def test_extract_refs():
    pages, assets = extract_refs(HOME, "https://site.test/")
    assert "https://site.test/about.html" in pages and "https://site.test/old" in pages
    assert "https://other.com/x" not in pages + assets
    assert "https://site.test/css/style.css" in assets and "https://site.test/images/a-2x.jpg" in assets
    assert "https://site.test/brochure.pdf" in assets and "https://site.test/images/png%20logo.png" in assets or "https://site.test/images/png logo.png" in assets


def test_snapshot_builds_full_site_zip():
    snap = snapshot_site("https://site.test", delay=0, session=Site())
    assert snap.pages == 3
    names = set(zipfile.ZipFile(io.BytesIO(snap.zip_bytes)).namelist())
    for expected in ["index.html", "about.html", "old.html", "css/style.css", "css/extra.css", "images/bg.jpg", "images/png logo.png", "images/a-2x.jpg", "favicon.ico", "brochure.pdf", "robots.txt"]:
        assert expected in names, expected
    assert "index.html" in snap.files and "css/style.css" in snap.files and "images/bg.jpg" in snap.binaries and "favicon.ico" in snap.binaries
    assert any("no file extension" in w for w in snap.warnings)


def test_snapshot_limits_and_failures():
    snap = snapshot_site("https://site.test", max_pages=1, delay=0, session=Site())
    assert snap.pages == 1 and "about.html" not in snap.files
    tiny = snapshot_site("https://site.test", max_total_mb=0, delay=0, session=Site())
    assert any("size limit" in w or "No pages" in w for w in tiny.warnings)
    dead = snapshot_site("https://nowhere.test", delay=0, session=type("S", (), {"get": lambda self, u, **k: R("x", "text/html", u, 500)})())
    assert dead.pages == 0 and any("No pages" in w for w in dead.warnings)


def test_snapshot_feeds_patch_and_export_keeps_binaries():
    snap = snapshot_site("https://site.test", delay=0, session=Site())
    patch = build_patch(snap.files, [filled_draft("uae/solar-installation-dubai/")], facts())
    assert patch.qa.passed, [(i.code, i.message) for i in patch.qa.errors]
    out = zipfile.ZipFile(io.BytesIO(site_io.export_zip(snap.zip_bytes, patch.files, "")))
    assert out.read("images/bg.jpg") == PNG and out.read("brochure.pdf") == b"%PDF-1.4"
    assert b"Commercial solar" in out.read("index.html") and "uae/solar-installation-dubai/index.html" in out.namelist()
    assert "sitemap.xml" in out.namelist()
