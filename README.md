# Tarek Website Mirror + Backend Data

This folder contains a full mirrored snapshot of [meettarek.framer.website](https://meettarek.framer.website) and structured backend-ready JSON extracted from the mirrored HTML.

## What is included

- Mirrored HTML routes:
  - `/index.html`
  - `/projects/index.html`
  - `/projects/<slug>/index.html` for all detected project pages
- Downloaded external assets in `assets/external/<host>/...`
- Structured content data:
  - `content/pages.json` (all pages: title, meta, headings, paragraphs, links, images)
  - `content/projects.json` (normalized project records)
  - `content/cms.json` (site-level + projects, easiest editing entry point)
  - `content/assets.json` (asset download manifest)
- Verification report:
  - `reports/integrity_report.json`
- Offline-ready HTML output:
  - `offline/index.html`
  - `offline/projects/<slug>/index.html`

## Regenerate everything

Run from this folder:

```bash
./scripts/sync_site.py
```

This will:
1. Crawl valid internal routes from the site.
2. Download external Framer/CDN assets.
3. Rebuild `content/*.json` files.
4. Rebuild `reports/integrity_report.json`.
5. Apply SEO/GEO metadata + JSON-LD + contact link fixes.

To rebuild offline-localized HTML (rewrites downloaded asset URLs to local paths):

```bash
./scripts/build_offline_html.py
```

To run only the SEO/GEO pass (without re-syncing):

```bash
./scripts/apply_seo_geo.py
```

## Current integrity status

Latest sync result:
- `page_count`: 12
- `project_count`: 10
- `external_assets_downloaded`: 178
- `external_assets_failed`: 0
- `internal_links_found`: 12 (all resolved locally)

## Editing model

For content updates through this conversation, the primary editable backend file is:
- `content/cms.json`

It is organized for direct updates per project (`title`, `year`, `services`, `client`, `team`, `overview`).

## Note on external dependencies

- Core pages and referenced assets are mirrored locally and validated.
- Some non-critical external references can still appear (for example, preconnect tags, analytics, outbound social/client links, and additional image variants not required for base rendering).
