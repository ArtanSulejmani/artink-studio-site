# Art Ink Studio

Static multilingual product catalogue with a Git-backed Decap CMS. No WordPress, database, runtime API, paid flipbook or analytics. Default language: English. Macedonian: /mk/. Albanian: /sq/.

## Run

Node.js 22 or newer. No npm dependencies required for the generator.

```sh
npm run build
npm test
```

Serve `dist` with any static HTTP server. Do not open individual HTML files via file://, because root-relative routes require a website origin. Netlify build command: `npm run build`; publish directory: `dist`.

## Included

- Home, catalogue search/category filters, individual products, digital chapter lookbook, privacy pages in three languages.
- Six genuine supplier sample products; no copied prices or stock promises.
- Local optimised WebP images; no embedded social feeds or third-party fonts.
- Product-specific mailto quotes, optional details form and Gmail fallback. Nothing sends automatically.
- Telephone, WhatsApp and Instagram links supplied by the owner.
- First-visit privacy notice using localStorage (not a consent wall).
- Admin desk `/admin/` and Decap editor `/admin/cms/`.
- SEO metadata, hreflang, Product/Organization structured data, sitemap and robots. A final URL is required for indexable output.
- Batch release gate: content saves do not trigger a production rebuild; changing `content/release.json` does.

## Still requires owner setup

The GitHub account connection does not create an OAuth app or a Netlify website. See SETUP-MK.md. The configured repository is `ArtanSulejmani/artink-studio-site`. Netlify import and OAuth configuration remain separate owner setup steps.

Confirm legal business name/address, supplier-photo permission, actual products you sell, materials, available options, translated copy and retention practice before publication. Privacy copy is a draft reflecting this implementation, not a legal compliance certificate. The temporary typographic brand is not an extracted Instagram logo.

## Content and releases

`content/products/*.json` holds the three translations in one record. CMS Save/Publish commits a file to main. `scripts/ignore-build.cjs` compares the latest deployed commit with the candidate. Changes only under product content, image uploads and settings are skipped. Increase the release version to include all saved changes in one deployment. Code edits deliberately trigger a deployment. Netlify build hooks and manual deploys can bypass the gate: do not use them for every product save.

Turning a product's `published` flag off hides it on the NEXT release; it does not remove it immediately. Deleting a product similarly takes effect on the next release. Do not delete an image still used by a published product: validation intentionally stops that build to preserve the previous live site. Changing a product slug changes its URL; add a redirect for the old URL if already indexed.

The main public site has no runtime dependencies on GitHub. GitHub/CMS outages affect editing, not the already published catalogue. Netlify credit exhaustion can pause the site; batching saves reduces deployment credits but does not eliminate bandwidth/request usage.

## Security / privacy

Never put OAuth secrets, tokens, build-hook URLs, private client artwork or personal records into this repository or `public/`. All public folder assets are downloadable. The CMS login is protected by GitHub permissions; the admin landing page itself is intentionally public and noindex. No hidden URL is treated as authentication. Owner must confirm access scopes in OAuth screens.

Production origin comes from Netlify's `URL`, or `content/settings.json` siteUrl. When neither is set the package emits noindex and no sitemap URLs to avoid indexing an unconfigured preview.

## Technology

Bootstrap 5.3.8 (current stable on official docs at preparation) is loaded from jsDelivr with the official SRI hash. The local custom stylesheet includes the essential layout/form rules, so the catalogue remains usable if the CDN fails. Custom responsive CSS Grid, native scroll-snap lookbook, small vanilla JS, Node.js static generation, Decap CMS 3.8.3 pinned rather than an unstable `latest`. Decap loads only on the admin editor from unpkg; verify its CDN availability during setup. No React bundle on public pages. See SOURCES.md for upstream sources and limitations.
