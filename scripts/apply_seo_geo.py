#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://www.meettarek.com"
PERSON_NAME = "Tarek Fahmy"
PERSON_IMAGE = "https://framerusercontent.com/images/Uku4Pg6AOrzsuF1EmwNym8jXKuI.png"
LINKEDIN_URL = "https://www.linkedin.com/in/meettarek/"
X_URL = "https://x.com/messagetarek"
EMAIL = "hello@meettarek.com"


def collapse_ws(text: str, limit: int = 160) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    if len(value) <= limit:
        return value
    clipped = value[: limit - 1]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped + "."


def set_title(html: str, title: str) -> str:
    return re.sub(r"<title>.*?</title>", f"<title>{title}</title>", html, count=1, flags=re.IGNORECASE | re.DOTALL)


def upsert_meta_name(html: str, name: str, content: str) -> str:
    pattern = re.compile(
        rf'<meta[^>]+name="{re.escape(name)}"[^>]*>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    replacement = f'<meta name="{name}" content="{content}">'
    if pattern.search(html):
        return pattern.sub(replacement, html, count=1)
    return html.replace("</head>", f"    {replacement}\n</head>", 1)


def upsert_meta_property(html: str, prop: str, content: str) -> str:
    pattern = re.compile(
        rf'<meta[^>]+property="{re.escape(prop)}"[^>]*>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    replacement = f'<meta property="{prop}" content="{content}">'
    if pattern.search(html):
        return pattern.sub(replacement, html, count=1)
    return html.replace("</head>", f"    {replacement}\n</head>", 1)


def upsert_link_canonical(html: str, href: str) -> str:
    pattern = re.compile(r'<link[^>]+rel="canonical"[^>]*>', flags=re.IGNORECASE | re.DOTALL)
    replacement = f'<link rel="canonical" href="{href}">'
    if pattern.search(html):
        return pattern.sub(replacement, html, count=1)
    return html.replace("</head>", f"    {replacement}\n</head>", 1)


def inject_jsonld(html: str, payload: list[dict]) -> str:
    jsonld_block = (
        '<script id="seo-geo-jsonld" type="application/ld+json">'
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )
    html = re.sub(
        r'<script id="seo-geo-jsonld" type="application/ld\+json">.*?</script>',
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    marker = "<!-- Start of headEnd -->"
    if marker in html:
        return html.replace(marker, f"{jsonld_block}\n{marker}", 1)
    return html.replace("</head>", f"    {jsonld_block}\n</head>", 1)


def page_url_for(path: str) -> str:
    if path == "/":
        return f"{SITE_URL}/"
    return f"{SITE_URL}{path}"


def build_home_ld(page_url: str, description: str) -> list[dict]:
    return [
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "@id": f"{SITE_URL}#person",
            "name": PERSON_NAME,
            "url": f"{SITE_URL}/",
            "image": PERSON_IMAGE,
            "jobTitle": "Service Design and AI Strategy Advisor",
            "description": description,
            "sameAs": [LINKEDIN_URL, X_URL],
            "knowsAbout": [
                "Service Design",
                "AI Strategy",
                "Digital Transformation",
                "Data Strategy",
                "Organizational Design",
            ],
            "worksFor": {"@type": "Organization", "name": PERSON_NAME},
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "business inquiries",
                "email": EMAIL,
                "url": f"mailto:{EMAIL}",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "@id": f"{SITE_URL}#service",
            "name": PERSON_NAME,
            "url": f"{SITE_URL}/",
            "description": description,
            "image": PERSON_IMAGE,
            "areaServed": "Worldwide",
            "founder": {"@id": f"{SITE_URL}#person"},
            "sameAs": [LINKEDIN_URL],
            "serviceType": [
                "Service Design",
                "AI Strategy",
                "Transformation Advisory",
                "Data Strategy",
            ],
        },
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{page_url}#webpage",
            "url": page_url,
            "name": "Tarek Fahmy | Service Design, AI Strategy and Transformation",
            "description": description,
            "isPartOf": {"@id": f"{SITE_URL}/#website"},
            "about": {"@id": f"{SITE_URL}#person"},
        },
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{SITE_URL}/#website",
            "url": f"{SITE_URL}/",
            "name": PERSON_NAME,
            "publisher": {"@id": f"{SITE_URL}#person"},
        },
    ]


def build_projects_index_ld(page_url: str, description: str) -> list[dict]:
    return [
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "@id": f"{page_url}#collection",
            "url": page_url,
            "name": "Projects and Case Studies | Tarek Fahmy",
            "description": description,
            "about": {"@id": f"{SITE_URL}#person"},
            "isPartOf": {"@id": f"{SITE_URL}/#website"},
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "@id": f"{page_url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Projects", "item": page_url},
            ],
        },
    ]


def build_project_ld(page_url: str, title: str, description: str, client: str, services: list[str]) -> list[dict]:
    return [
        {
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            "@id": f"{page_url}#case-study",
            "url": page_url,
            "name": title,
            "description": description,
            "creator": {"@id": f"{SITE_URL}#person"},
            "author": {"@id": f"{SITE_URL}#person"},
            "about": services if services else ["Service Design", "AI Strategy", "Transformation"],
            "keywords": ", ".join(services) if services else "Service Design, AI Strategy, Transformation",
            "publisher": {"@id": f"{SITE_URL}#person"},
            "isPartOf": {"@id": f"{SITE_URL}/#website"},
            "sourceOrganization": {"@type": "Organization", "name": client} if client else None,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "@id": f"{page_url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Projects", "item": f"{SITE_URL}/projects"},
                {"@type": "ListItem", "position": 3, "name": title, "item": page_url},
            ],
        },
    ]


def clean_none(payload: list[dict]) -> list[dict]:
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items() if v is not None}
        if isinstance(obj, list):
            return [_clean(v) for v in obj]
        return obj

    return [_clean(item) for item in payload]


def apply_head_updates(html: str, title: str, description: str, path: str) -> str:
    page_url = page_url_for(path)
    html = set_title(html, title)
    html = upsert_meta_name(html, "description", description)
    html = upsert_meta_name(html, "robots", "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1")
    html = upsert_link_canonical(html, page_url)
    html = upsert_meta_property(html, "og:type", "website")
    html = upsert_meta_property(html, "og:title", title)
    html = upsert_meta_property(html, "og:description", description)
    html = upsert_meta_property(html, "og:url", page_url)
    html = upsert_meta_name(html, "twitter:card", "summary_large_image")
    html = upsert_meta_name(html, "twitter:title", title)
    html = upsert_meta_name(html, "twitter:description", description)
    return html


def main() -> None:
    cms_path = ROOT / "content" / "cms.json"
    cms = json.loads(cms_path.read_text(encoding="utf-8"))
    projects = {p["slug"]: p for p in cms.get("projects", [])}

    pages = [ROOT / "index.html", ROOT / "projects" / "index.html"] + sorted((ROOT / "projects").glob("*/index.html"))
    changed = 0
    email_fixes = 0

    for page in pages:
        if not page.exists():
            continue
        rel = page.relative_to(ROOT).as_posix()
        if rel == "index.html":
            path = "/"
            title = "Tarek Fahmy | Service Design, AI Strategy and Transformation"
            desc = "Tarek Fahmy helps organizations deliver measurable outcomes through service design, AI strategy, digital transformation, and data-informed innovation."
            ld_payload = build_home_ld(page_url_for(path), desc)
        elif rel == "projects/index.html":
            path = "/projects"
            title = "Projects and Case Studies | Tarek Fahmy"
            desc = "Explore service design, AI strategy, and transformation case studies by Tarek Fahmy across public, private, and international development sectors."
            ld_payload = build_projects_index_ld(page_url_for(path), desc)
        else:
            slug = rel.split("/")[1]
            project = projects.get(slug, {})
            proj_title = project.get("title") or slug.replace("-", " ").title()
            path = f"/projects/{slug}"
            title = f"{proj_title} | Case Study by Tarek Fahmy"
            services = project.get("services") or []
            client = project.get("client", "")
            base_desc = project.get("overview") or "Service design and transformation case study."
            desc = collapse_ws(base_desc, limit=158)
            ld_payload = build_project_ld(page_url_for(path), proj_title, desc, client, services)

        original = page.read_text(encoding="utf-8", errors="ignore")
        updated = original
        updated = apply_head_updates(updated, title, desc, path)
        updated = inject_jsonld(updated, clean_none(ld_payload))

        bad_href_count = updated.count('href="https://hello@meettarek.com"')
        email_fixes += bad_href_count
        updated = updated.replace('href="https://hello@meettarek.com"', 'href="mailto:hello@meettarek.com"')

        if updated != original:
            page.write_text(updated, encoding="utf-8")
            changed += 1

    llms = (
        "# Tarek Fahmy\n\n"
        "Tarek Fahmy is a consultant focused on service design, AI strategy, digital transformation, and data-informed innovation.\n\n"
        "## Primary website\n"
        f"- {SITE_URL}/\n\n"
        "## Key pages\n"
        f"- {SITE_URL}/projects\n"
        f"- {SITE_URL}/projects/city-services\n"
        f"- {SITE_URL}/projects/digital-future\n"
        f"- {SITE_URL}/projects/india-digital-financial-inclusion\n\n"
        "## Contact\n"
        f"- Email: {EMAIL}\n"
        f"- LinkedIn: {LINKEDIN_URL}\n"
    )
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")

    print(f"Pages updated: {changed}")
    print(f"Broken email links fixed: {email_fixes}")
    print("Generated: llms.txt")


if __name__ == "__main__":
    main()
