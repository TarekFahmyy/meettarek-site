#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://www.meettarek.com"
BRAND_NAME = "Meettarek"
PERSON_NAME = "Tarek Fahmy"
PERSON_IMAGE = "https://framerusercontent.com/images/Uku4Pg6AOrzsuF1EmwNym8jXKuI.png"
LINKEDIN_URL = "https://www.linkedin.com/in/meettarek/"
X_URL = "https://x.com/messagetarek"
CALMWORKS_URL = "https://www.calmworks.io/"
EMAIL = "hello@meettarek.com"
BING_VERIFICATION_CODE = "29A22E8B6B203ED542C41042F7C3E29A"
AREA_SERVED_COUNTRIES = [
    "Finland",
    "Sweden",
    "Norway",
    "Denmark",
    "United Arab Emirates",
    "Saudi Arabia",
    "Egypt",
    "Qatar",
    "Oman",
]
REGIONAL_PHRASES = [
    "Service Design consultant in Finland, Nordics, and MENA",
    "AI strategy and transformation across Nordics and MENA",
]
REGIONAL_ALIASES = ["UAE"]
HREFLANG_CODES = [
    "x-default",
    "en",
    "en-FI",
    "en-SE",
    "en-NO",
    "en-DK",
    "en-AE",
    "en-SA",
    "en-EG",
    "en-QA",
    "en-OM",
]
PRIMARY_TOPICS = [
    "Service Design",
    "Product and Service Design",
    "AI Strategy",
    "Digital Transformation",
    "Transformation Strategy",
    "Data Strategy",
    "Innovation Strategy",
    "Human-Centered Design",
]
ENTITY_ALIASES = [
    "Tarek",
    "Fahmy",
    "Service Design Consultant",
    "AI Strategy Consultant",
    "Transformation Advisor",
]


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


def upsert_hreflang_links(html: str, href: str) -> str:
    pattern = re.compile(
        r'<link[^>]+rel="alternate"[^>]+hreflang="[^"]+"[^>]*>\s*',
        flags=re.IGNORECASE | re.DOTALL,
    )
    html = pattern.sub("", html)
    block = "\n".join(
        f'    <link rel="alternate" href="{href}" hreflang="{code}">' for code in HREFLANG_CODES
    )
    return html.replace("</head>", f"{block}\n</head>", 1)


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
    area_served = [{"@type": "Country", "name": country} for country in AREA_SERVED_COUNTRIES]
    return [
        {
            "@context": "https://schema.org",
            "@type": "ImageObject",
            "@id": f"{SITE_URL}#logo",
            "url": PERSON_IMAGE,
            "contentUrl": PERSON_IMAGE,
            "caption": BRAND_NAME,
        },
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "@id": f"{SITE_URL}#person",
            "name": PERSON_NAME,
            "alternateName": ENTITY_ALIASES,
            "url": f"{SITE_URL}/",
            "image": PERSON_IMAGE,
            "jobTitle": "Service Design, AI Strategy and Transformation Advisor",
            "description": description,
            "sameAs": [LINKEDIN_URL, X_URL],
            "knowsAbout": PRIMARY_TOPICS,
            "mainEntityOfPage": {"@id": f"{page_url}#webpage"},
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
            "@type": "Organization",
            "@id": f"{SITE_URL}#organization",
            "name": BRAND_NAME,
            "url": f"{SITE_URL}/",
            "logo": {"@id": f"{SITE_URL}#logo"},
            "image": PERSON_IMAGE,
            "founder": {"@id": f"{SITE_URL}#person"},
            "sameAs": [LINKEDIN_URL, X_URL],
            "areaServed": area_served,
        },
        {
            "@context": "https://schema.org",
            "@type": "ProfessionalService",
            "@id": f"{SITE_URL}#service",
            "name": PERSON_NAME,
            "url": f"{SITE_URL}/",
            "description": description,
            "image": PERSON_IMAGE,
            "areaServed": area_served,
            "founder": {"@id": f"{SITE_URL}#person"},
            "parentOrganization": {"@id": f"{SITE_URL}#organization"},
            "logo": {"@id": f"{SITE_URL}#logo"},
            "sameAs": [LINKEDIN_URL],
            "serviceType": PRIMARY_TOPICS,
        },
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{page_url}#webpage",
            "url": page_url,
            "name": "Tarek Fahmy | Service Design, Product Strategy, AI Strategy and Transformation",
            "description": description,
            "isPartOf": {"@id": f"{SITE_URL}/#website"},
            "about": {"@id": f"{SITE_URL}#person"},
            "mentions": [{"@type": "WebSite", "name": "Calmworks", "url": CALMWORKS_URL}],
            "inLanguage": "en",
        },
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{SITE_URL}/#website",
            "url": f"{SITE_URL}/",
            "name": BRAND_NAME,
            "alternateName": [PERSON_NAME] + ENTITY_ALIASES,
            "publisher": {"@id": f"{SITE_URL}#organization"},
            "about": {"@id": f"{SITE_URL}#person"},
            "inLanguage": "en",
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
    regional_terms = ["Nordics", "MENA"] + AREA_SERVED_COUNTRIES + REGIONAL_ALIASES
    keywords = ", ".join(
        PRIMARY_TOPICS
        + ENTITY_ALIASES
        + REGIONAL_PHRASES
        + regional_terms
        + [
            "tarek service design",
            "tarek servcie design",
            "service design finland",
            "service design nordics",
            "ai strategy mena",
            "digital transformation consultant",
            "data strategy consultant",
        ]
    )
    html = set_title(html, title)
    html = upsert_meta_name(html, "description", description)
    html = upsert_meta_name(html, "keywords", keywords)
    html = upsert_meta_name(html, "author", PERSON_NAME)
    html = upsert_meta_name(html, "msvalidate.01", BING_VERIFICATION_CODE)
    html = upsert_meta_name(html, "robots", "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1")
    html = upsert_meta_name(html, "geo.region", "FI-UUS")
    html = upsert_meta_name(
        html,
        "geo.placename",
        "Finland; Sweden; Norway; Denmark; United Arab Emirates; Saudi Arabia; Egypt; Qatar; Oman",
    )
    html = upsert_link_canonical(html, page_url)
    html = upsert_hreflang_links(html, page_url)
    html = upsert_meta_property(html, "og:type", "website")
    html = upsert_meta_property(html, "og:site_name", PERSON_NAME)
    html = upsert_meta_property(html, "og:locale", "en_US")
    html = upsert_meta_property(html, "og:title", title)
    html = upsert_meta_property(html, "og:description", description)
    html = upsert_meta_property(html, "og:url", page_url)
    html = upsert_meta_property(html, "og:image", PERSON_IMAGE)
    html = upsert_meta_name(html, "twitter:card", "summary_large_image")
    html = upsert_meta_name(html, "twitter:site", "@messagetarek")
    html = upsert_meta_name(html, "twitter:creator", "@messagetarek")
    html = upsert_meta_name(html, "twitter:title", title)
    html = upsert_meta_name(html, "twitter:description", description)
    html = upsert_meta_name(html, "twitter:image", PERSON_IMAGE)
    return html


def main() -> None:
    pages = [ROOT / "index.html"]
    changed = 0
    email_fixes = 0

    for page in pages:
        if not page.exists():
            continue
        rel = page.relative_to(ROOT).as_posix()
        if rel != "index.html":
            continue

        path = "/"
        title = "Tarek Fahmy | Service Design, Product Strategy, AI Strategy and Transformation"
        desc = (
            "Tarek Fahmy is a Service Design consultant in Finland, Nordics, and MENA, helping "
            "organizations deliver AI strategy and transformation across Nordics and MENA through "
            "product and data innovation."
        )
        ld_payload = build_home_ld(page_url_for(path), desc)

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
        "Tarek Fahmy is a consultant focused on service design, product and service innovation, "
        "AI strategy, digital transformation, and data-informed innovation.\n\n"
        "## Priority regions\n"
        "- Finland\n"
        "- Sweden\n"
        "- Norway\n"
        "- Denmark\n"
        "- UAE (United Arab Emirates)\n"
        "- Saudi Arabia\n"
        "- Egypt\n"
        "- Qatar\n"
        "- Oman\n\n"
        "## Regional positioning phrases\n"
        "- Service Design consultant in Finland, Nordics, and MENA\n"
        "- AI strategy and transformation across Nordics and MENA\n\n"
        "## Preferred entity labels\n"
        "- Tarek Fahmy\n"
        "- Tarek\n"
        "- Fahmy\n"
        "- Service Design Consultant\n"
        "- AI Strategy Consultant\n"
        "- Transformation Advisor\n\n"
        "## Common query variants\n"
        "- tarek service design\n"
        "- tarek servcie design\n"
        "- tarek product design\n"
        "- tarek ai strategy\n"
        "- tarek transformation\n"
        "- fahmy service design\n\n"
        "## Canonical web presence (priority order)\n"
        "1. Website: https://www.meettarek.com/\n"
        "2. LinkedIn: https://www.linkedin.com/in/meettarek/\n"
        "3. X (Twitter): https://x.com/messagetarek\n"
        "4. Calmworks mention: https://www.calmworks.io/\n\n"
        "## Preferred search intent clusters\n"
        "- service design consultant\n"
        "- service design in Finland and Nordics\n"
        "- AI strategy consultant in MENA\n"
        "- transformation and data strategy advisor\n\n"
        "## Key pages\n"
        "- https://www.meettarek.com/\n"
        "- https://www.meettarek.com/projects\n"
        "- https://www.meettarek.com/projects/city-services\n"
        "- https://www.meettarek.com/projects/digital-future\n"
        "- https://www.meettarek.com/projects/india-digital-financial-inclusion\n\n"
        "## Contact\n"
        f"- Email: {EMAIL}\n"
        f"- LinkedIn: {LINKEDIN_URL}\n"
    )
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")

    robots = (
        "User-agent: *\n"
        "Allow: /\n\n"
        "Host: www.meettarek.com\n"
        "Sitemap: https://www.meettarek.com/sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    print(f"Pages updated: {changed}")
    print(f"Broken email links fixed: {email_fixes}")
    print("Generated: llms.txt")


if __name__ == "__main__":
    main()
