# Vercel + Cloudflare SEO/GEO Operations

This checklist is backend-only and does not change website layout/UI.

## Goal
- Consolidate all ranking authority to one canonical host: `https://www.meettarek.com`.
- Ensure branded search ordering is stable:
  1) Website `www.meettarek.com`
  2) LinkedIn `/in/meettarek`
  3) X `@messagetarek`
  4) Other mentions/articles.

## 1) Vercel Domain Setup
- Add both domains to the same Vercel project:
  - `www.meettarek.com`
  - `meettarek.com`
- Set `www.meettarek.com` as primary domain.
- Keep HTTPS enabled and valid certificates for both domains.
- Keep redirect policy:
  - `meettarek.com/*` -> `https://www.meettarek.com/$1` (301).

Notes:
- `vercel.json` already includes host redirect logic for apex -> www.
- DNS must still point correctly for Vercel to receive traffic.

## 2) Cloudflare DNS (authoritative)
- Keep Cloudflare as nameserver.
- Configure records:
  - `A @` -> `76.76.21.21` (DNS only recommended for debugging, Proxy can be re-enabled after validation)
  - `CNAME www` -> `cname.vercel-dns.com` (or Vercel target shown in dashboard)
- Remove Namecheap URL forwarding records/rules for this domain.
- Verify no conflicting redirect rules at Cloudflare level.

## 3) Cloudflare SSL/TLS
- SSL mode: `Full` (or `Full (strict)` if cert chain is confirmed end-to-end).
- Always Use HTTPS: ON.
- Automatic HTTPS Rewrites: ON.

## 4) Redirect Validation
Run and confirm:
- `http://meettarek.com` -> `https://www.meettarek.com/` (301/308)
- `https://meettarek.com` -> `https://www.meettarek.com/` (301/308)
- `http://www.meettarek.com` -> `https://www.meettarek.com/` (301/308)
- `https://www.meettarek.com` -> 200

Any `522` on apex indicates DNS/proxy mismatch between Cloudflare and Vercel.

## 5) Search Console / Bing
- Verify both properties in Google Search Console:
  - `https://www.meettarek.com`
  - `https://meettarek.com`
- Submit sitemap: `https://www.meettarek.com/sitemap.xml`.
- Request indexing for:
  - `/`
  - `/projects`
  - 3-5 highest authority case-study pages.
- Repeat in Bing Webmaster Tools.

## 6) Entity Consistency (GEO support)
- Keep exactly matching identity fields on website, LinkedIn, X:
  - Name: `Tarek Fahmy`
  - Primary keywords: `Service Design`, `AI Strategy`, `Digital Transformation`, `Data Strategy`
  - Same profile links everywhere.
- Keep `llms.txt` current after major profile/content changes.

## 7) Weekly Maintenance
- Check live headers and canonical weekly.
- Check GSC:
  - Coverage issues
  - Query impressions for `tarek`, `tarek fahmy`, `tarek service design`.
- Add one evidence page/post per week (project insight, framework, or case takeaway).
