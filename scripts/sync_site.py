#!/usr/bin/env python3
import hashlib
import html
import json
import os
import re
import sys
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen

BASE_URL = "https://meettarek.framer.website"
SEED_PATHS = [
    "/",
    "/projects",
    "/projects/bio-innovation",
    "/projects/circular-economy-bm",
    "/projects/city-services",
    "/projects/digital-future",
    "/projects/digital-vultures",
    "/projects/india-digital-financial-inclusion",
    "/projects/sok-mara-sustainability-strategy",
    "/projects/usaid-asist-digital-records",
    "/projects/vtt-mycelium-leather",
    "/projects/witness-experince",
]
ALLOWED_EXTERNAL_HOSTS = {
    "framerusercontent.com",
    "framer.com",
    "fonts.gstatic.com",
    "www.googletagmanager.com",
    "googletagmanager.com",
}
VALID_PATH_RE = re.compile(r"^/(?:$|[a-z0-9][a-z0-9/_-]*)$")
FORCE_REFRESH = True

HREF_RE = re.compile(r"href=\"([^\"]+)\"", re.IGNORECASE)
SRC_RE = re.compile(r"src=\"([^\"]+)\"", re.IGNORECASE)
META_CONTENT_RE = re.compile(
    r'<meta[^>]+name=\"(?:framer-search-index|framer-search-index-fallback)\"[^>]+content=\"([^\"]+)\"',
    re.IGNORECASE,
)
CSS_URL_RE = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_RE = re.compile(r'<meta[^>]+name="([^"]+)"[^>]+content="([^"]*)"', re.IGNORECASE)
CANONICAL_RE = re.compile(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', re.IGNORECASE)
H_RE = re.compile(r"<h([1-4])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
A_RE = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"[^>]*>', re.IGNORECASE)
ALT_RE = re.compile(r'alt="([^"]*)"', re.IGNORECASE)


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def fetch_bytes(url: str, timeout: int = 30) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SiteMirrorBot/1.0)"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def collect_paths_from_json(value, out: set):
    if isinstance(value, dict):
        for v in value.values():
            collect_paths_from_json(v, out)
        return
    if isinstance(value, list):
        for v in value:
            collect_paths_from_json(v, out)
        return
    if isinstance(value, str):
        if is_valid_internal_path(value):
            out.add(value)
            return
        # also capture full URLs pointing to this site
        if value.startswith(BASE_URL):
            pu = urlparse(value)
            p = pu.path or "/"
            if is_valid_internal_path(p):
                out.add(p)


def local_page_path(root: Path, path: str) -> Path:
    path = path.split("#", 1)[0].split("?", 1)[0]
    if not path or path == "/":
        return root / "index.html"
    p = path.strip("/")
    return root / p / "index.html"


def is_valid_internal_path(path: str) -> bool:
    if not path:
        return False
    if not VALID_PATH_RE.match(path):
        return False
    return True


def map_asset_path(root: Path, url: str) -> Path:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    p = unquote(parsed.path.lstrip("/"))
    if not p:
        p = "index"
    if parsed.query:
        qhash = hashlib.sha1(parsed.query.encode("utf-8")).hexdigest()[:10]
        if "." in p.split("/")[-1]:
            stem, ext = p.rsplit(".", 1)
            p = f"{stem}__q_{qhash}.{ext}"
        else:
            p = f"{p}__q_{qhash}"
    return root / "assets" / "external" / host / p


def extract_asset_urls(html_text: str, current_url: str):
    urls = set()
    for raw in HREF_RE.findall(html_text):
        u = html.unescape(raw.strip().strip("'\""))
        if not u or u.startswith("mailto:") or u.startswith("tel:") or u.startswith("javascript:"):
            continue
        urls.add(urljoin(current_url, u))
    for raw in SRC_RE.findall(html_text):
        u = html.unescape(raw.strip().strip("'\""))
        if not u or u.startswith("data:") or u.startswith("mailto:") or u.startswith("tel:") or u.startswith("javascript:"):
            continue
        urls.add(urljoin(current_url, u))
    for raw in META_CONTENT_RE.findall(html_text):
        u = html.unescape(raw.strip().strip("'\""))
        if u:
            urls.add(urljoin(current_url, u))
    for raw in CSS_URL_RE.findall(html_text):
        u = html.unescape(raw.strip().strip("'\""))
        if not u or u.startswith("data:"):
            continue
        urls.add(urljoin(current_url, u))
    return urls


def extract_nav_links(html_text: str, current_url: str):
    links = set()
    for raw in re.findall(r"<a[^>]+href=\"([^\"]+)\"", html_text, flags=re.IGNORECASE):
        u = html.unescape(raw.strip().strip("'\""))
        if not u or u.startswith("#") or u.startswith("mailto:") or u.startswith("tel:") or u.startswith("javascript:"):
            continue
        links.add(urljoin(current_url, u))
    return links


def parse_page(path: str, content: str):
    title_match = TITLE_RE.search(content)
    title = clean_text(title_match.group(1)) if title_match else ""
    meta = {k.lower(): html.unescape(v) for k, v in META_RE.findall(content)}
    canonical = ""
    canonical_match = CANONICAL_RE.search(content)
    if canonical_match:
        canonical = html.unescape(canonical_match.group(1))

    headings = [
        {
            "level": int(level),
            "text": clean_text(text),
        }
        for level, text in H_RE.findall(content)
        if clean_text(text)
    ]
    paragraphs = [clean_text(p) for p in P_RE.findall(content)]
    paragraphs = [p for p in paragraphs if p]

    links = []
    for href, text in A_RE.findall(content):
        href = html.unescape(href)
        t = clean_text(text)
        links.append({"href": href, "text": t})

    images = []
    for tag in re.findall(r"<img[^>]+>", content, flags=re.IGNORECASE):
        sm = re.search(r'src="([^"]+)"', tag, flags=re.IGNORECASE)
        am = ALT_RE.search(tag)
        if sm:
            images.append({
                "src": html.unescape(sm.group(1)),
                "alt": html.unescape(am.group(1)) if am else "",
            })

    return {
        "path": path,
        "title": title,
        "description": meta.get("description", ""),
        "canonical": canonical,
        "headings": headings,
        "paragraphs": paragraphs,
        "links": links,
        "images": images,
    }


def build_project_record(page):
    slug = page["path"].strip("/").split("/", 1)[-1]
    paragraphs = page["paragraphs"]
    headings = page["headings"]

    project_title = ""
    for h in headings:
        if h["text"] and len(h["text"]) > 5:
            project_title = h["text"]
            break

    year = ""
    for p in paragraphs[:30]:
        if re.fullmatch(r"20\d{2}", p):
            year = p
            break

    def after_label(label: str):
        for i, p in enumerate(paragraphs):
            if p.strip().lower() == label:
                if i + 1 < len(paragraphs):
                    return paragraphs[i + 1]
        return ""

    services = after_label("services")
    client = after_label("client")
    team = after_label("team")
    overview = ""
    for i, p in enumerate(paragraphs):
        if p.strip().lower() == "overview" and i + 1 < len(paragraphs):
            overview = paragraphs[i + 1]
            break
    if not overview:
        overview = paragraphs[0] if paragraphs else ""

    return {
        "slug": slug,
        "url": page["path"],
        "title": project_title or page["title"],
        "year": year,
        "services": [s.strip() for s in services.split("•") if s.strip()] if services else [],
        "client": client,
        "team": team,
        "overview": overview,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    crawled_pages = {}
    queue = deque(urljoin(BASE_URL, p) for p in SEED_PATHS)
    seen = set(queue)
    discovered_search_indexes = set()

    while queue:
        url = queue.popleft()
        parsed = urlparse(url)
        if parsed.netloc != urlparse(BASE_URL).netloc:
            continue
        path = parsed.path or "/"
        out = local_page_path(root, path)
        out.parent.mkdir(parents=True, exist_ok=True)

        try:
            if FORCE_REFRESH or (not out.exists()) or out.stat().st_size == 0:
                content = fetch_bytes(url).decode("utf-8", errors="ignore")
                out.write_text(content, encoding="utf-8")
            else:
                content = out.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            print(f"WARN page fetch failed: {url} ({exc})", file=sys.stderr)
            continue

        crawled_pages[path] = content

        # Discover dynamic pages from Framer search index JSON.
        for idx_url in META_CONTENT_RE.findall(content):
            idx_full = urljoin(url, html.unescape(idx_url.strip()))
            if idx_full in discovered_search_indexes:
                continue
            discovered_search_indexes.add(idx_full)
            try:
                idx_data = json.loads(fetch_bytes(idx_full).decode("utf-8", errors="ignore"))
                extra_paths = set()
                collect_paths_from_json(idx_data, extra_paths)
                for ep in sorted(extra_paths):
                    full = urljoin(BASE_URL, ep)
                    if full not in seen:
                        seen.add(full)
                        queue.append(full)
            except Exception as exc:
                print(f"WARN search index fetch failed: {idx_full} ({exc})", file=sys.stderr)

        for found in extract_nav_links(content, url):
            p2 = urlparse(found)
            if p2.netloc == urlparse(BASE_URL).netloc:
                clean = f"{p2.scheme}://{p2.netloc}{p2.path}"
                # Keep crawl constrained to same site and reasonable depth
                if clean not in seen and is_valid_internal_path(p2.path):
                    seen.add(clean)
                    queue.append(clean)

    page_files = sorted({local_page_path(root, p) for p in crawled_pages.keys() if local_page_path(root, p).exists()})

    all_asset_urls = set()
    all_internal_links = set()
    for pf in page_files:
        txt = pf.read_text(encoding="utf-8", errors="ignore")
        page_url = urljoin(BASE_URL, "/" + str(pf.relative_to(root)).replace("index.html", "").strip("/"))
        for u in extract_asset_urls(txt, page_url):
            pu = urlparse(u)
            if pu.netloc == urlparse(BASE_URL).netloc:
                ipath = pu.path or "/"
                if is_valid_internal_path(ipath):
                    all_internal_links.add(ipath)
            elif pu.netloc:
                all_asset_urls.add(u)

    downloaded_assets = []
    failed_assets = []

    for u in sorted(all_asset_urls):
        pu = urlparse(u)
        host = pu.netloc.lower()
        if host not in ALLOWED_EXTERNAL_HOSTS:
            continue
        if pu.path in ("", "/"):
            continue
        out = map_asset_path(root, u)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            if FORCE_REFRESH or (not out.exists()) or out.stat().st_size == 0:
                data = fetch_bytes(u)
                out.write_bytes(data)
                downloaded_assets.append({"url": u, "path": str(out.relative_to(root)), "bytes": len(data), "cached": False})
            else:
                downloaded_assets.append({"url": u, "path": str(out.relative_to(root)), "bytes": out.stat().st_size, "cached": True})
        except Exception as exc:
            failed_assets.append({"url": u, "error": str(exc)})

    pages = []
    for pf in sorted(page_files):
        rel = "/" + str(pf.relative_to(root)).replace("index.html", "").rstrip("/")
        if rel == "":
            rel = "/"
        pages.append(parse_page(rel, pf.read_text(encoding="utf-8", errors="ignore")))

    projects = [build_project_record(p) for p in pages if p["path"].startswith("/projects/") and p["path"] != "/projects"]

    content_dir = root / "content"
    reports_dir = root / "reports"
    content_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    (content_dir / "pages.json").write_text(json.dumps(pages, indent=2, ensure_ascii=True), encoding="utf-8")
    (content_dir / "projects.json").write_text(json.dumps(projects, indent=2, ensure_ascii=True), encoding="utf-8")
    (content_dir / "assets.json").write_text(json.dumps({
        "downloaded": downloaded_assets,
        "failed": failed_assets,
    }, indent=2, ensure_ascii=True), encoding="utf-8")

    internal_status = []
    for p in sorted(all_internal_links):
        lp = local_page_path(root, p)
        internal_status.append({
            "url_path": p,
            "exists_local": lp.exists(),
            "local_path": str(lp.relative_to(root)),
        })

    report = {
        "generated_at_epoch": int(time.time()),
        "base_url": BASE_URL,
        "page_count": len(pages),
        "project_count": len(projects),
        "internal_links_found": len(all_internal_links),
        "external_assets_downloaded": len(downloaded_assets),
        "external_assets_failed": len(failed_assets),
        "internal_link_status": internal_status,
    }
    (reports_dir / "integrity_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    cms = {
        "site": {
            "name": pages[0]["title"] if pages else "",
            "description": pages[0]["description"] if pages else "",
            "base_url": BASE_URL,
        },
        "projects": projects,
    }
    (content_dir / "cms.json").write_text(json.dumps(cms, indent=2, ensure_ascii=True), encoding="utf-8")

    # Remove stale local project folders that are no longer present remotely.
    valid_project_slugs = {p["slug"] for p in projects}
    projects_root = root / "projects"
    if projects_root.exists():
        for d in projects_root.iterdir():
            if not d.is_dir():
                continue
            if d.name not in valid_project_slugs:
                for child in sorted(d.rglob("*"), reverse=True):
                    if child.is_file() or child.is_symlink():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        try:
                            child.rmdir()
                        except OSError:
                            pass
                try:
                    d.rmdir()
                except OSError:
                    pass

    print(f"Pages: {len(pages)}")
    print(f"Projects: {len(projects)}")
    print(f"Assets downloaded: {len(downloaded_assets)}")
    print(f"Assets failed: {len(failed_assets)}")


if __name__ == "__main__":
    main()
