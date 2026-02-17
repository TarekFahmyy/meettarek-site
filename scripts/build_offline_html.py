#!/usr/bin/env python3
import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OFFLINE = ROOT / "offline"


def to_relative(from_file: Path, to_file: Path) -> str:
    return Path(".") / Path(
        __import__("os").path.relpath(to_file, from_file.parent)
    )


def main():
    assets = json.loads((ROOT / "content" / "assets.json").read_text(encoding="utf-8"))
    mappings = {}
    for item in assets.get("downloaded", []):
        url = item["url"]
        local = ROOT / item["path"]
        mappings[url] = local

    if OFFLINE.exists():
        shutil.rmtree(OFFLINE)
    OFFLINE.mkdir(parents=True, exist_ok=True)

    html_files = [ROOT / "index.html"] + sorted((ROOT / "projects").glob("*/index.html")) + [ROOT / "projects" / "index.html"]

    written = 0
    for src in html_files:
        if not src.exists():
            continue
        rel = src.relative_to(ROOT)
        dst = OFFLINE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        text = src.read_text(encoding="utf-8", errors="ignore")

        for url, local in mappings.items():
            if not local.exists():
                continue
            rel_local = str(to_relative(dst, local)).replace("\\", "/")
            if not rel_local.startswith("."):
                rel_local = "./" + rel_local

            escaped_url = html.escape(url, quote=True)
            text = text.replace(url, rel_local)
            text = text.replace(escaped_url, rel_local)

        dst.write_text(text, encoding="utf-8")
        written += 1

    print(f"Offline HTML files written: {written}")


if __name__ == "__main__":
    main()
