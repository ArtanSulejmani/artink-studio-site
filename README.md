# ArtInk Studio catalogue

Static, database-free site for Netlify. English is the default at `/`; Macedonian is `/mk/`; Albanian is `/sq/`. **Products** at `/products/` lists all articles with search and category filters. **Catalogue** at `/catalog/` is a separate digital lookbook organised by category with an optional uploaded PDF. Each product has its own page in each language. Product records live in `content/products/*.json`, catalogue settings in `content/catalog.json`, images in `static/images/`, and the editor is at `/admin/`.

## Preview and build

For Windows without Node, extract the companion **ArtInk-Studio-Lokalno-Preview-Bez-Node.zip** and double-click `start-artink.bat`. It previews generated HTML using built-in Windows PowerShell; updating source JSON or templates requires a new Netlify or Node build. The contact form can be filled locally but actually sends only after a Netlify deploy. If you have Node.js 20.11+ (or a newer supported version), open this extracted folder in a terminal and run `npm run dev`. The command generates `dist/index.html` and starts a local preview at `http://localhost:4173/`. `dist/mk/index.html`, `dist/sq/index.html` and the other pages are generated the same way. Press Ctrl+C to stop. If you edit JSON, stop and run `npm run dev` again to rebuild. You can also run `npm run build` and `npm run preview` separately. The admin screen can be viewed locally at `/admin/`, but its GitHub sign-in and publishing work only after the site is connected to Netlify and OAuth is configured.

Netlify uses the included `netlify.toml`: build command `node scripts/build.mjs`, publish directory `dist`. There are no runtime functions, database queries, npm dependencies or third-party paid CMS services. One Netlify Forms contact form uses the hosting provider’s form service and its applicable usage limits. Every publish runs one short static build. Netlify usage and plan limits still apply.

The build checks unique URL slugs, supported categories, required translations, at least one image, colour values and stock variants for each visible product. Hidden products (`active: false`) remain in the editor and do not get public pages. Changing a slug changes the URL; add a redirect if a published slug is changed.

`SITE_URL` can override the canonical site URL. Netlify's `URL` build environment variable is used automatically when `SITE_URL` is absent. Set `SITE_URL=https://your-custom-domain` when attaching a custom domain. Without either value, local output uses an example `.netlify.app` URL in canonical, Open Graph, robots and sitemap metadata; do not publish that local output as final production metadata.

## GitHub and Netlify setup

1. Create a GitHub repository named `artink-studio-site` under `ArtanSulejmani`. Upload this project's **contents** to the repository root, including `netlify.toml`, `scripts`, `content` and `static`. Keep `dist` out of Git. If you choose another repo name, update `static/admin/config.yml` → `backend.repo`.
2. In Netlify, add a new project from this GitHub repository and deploy its `main` branch. The build/publish settings are already in `netlify.toml`.
3. In GitHub **Settings → Developer settings → OAuth Apps → New OAuth App**, create an app named `ArtInk Studio Editor`. Use the site's Netlify URL as Homepage URL and `https://api.netlify.com/auth/done` as Authorization callback URL. Copy its Client ID; generate a Client Secret.
4. In Netlify, open **Project configuration → Access & security → OAuth → Install Provider**, choose **GitHub**, and enter the Client ID and Client Secret **there**. Keep the secret in Netlify; never put it in Git, a product record, or a chat message.
5. Visit `https://YOUR-SITE.netlify.app/admin/`, sign in with a GitHub user who has write access to that repository, then create, edit, unpublish or delete a product. Publishing in the editor commits JSON/images to GitHub and triggers the next Netlify deploy. Check one new product URL after the deploy finishes.

6. Enable **Forms → Form detection** in Netlify if it is off, then redeploy. In **Project configuration → Notifications**, add an email notification for the `artink-inquiry` form addressed to `artinkstudio.2026@gmail.com`. Submit one real test from the live `/contact/` page, then check **Forms → submissions** and the inbox/spam folder. EN/MK/AL share the same form name and each has its own translated success page. The notification recipient must be set in Netlify; static HTML alone cannot configure it.

This uses Decap CMS's GitHub backend and Netlify's OAuth provider token service. It does **not** use Git Gateway. OAuth cannot be completed before a real repo, Netlify project, site URL and OAuth app exist.

## Editing products

In `/admin/` open **Products**. Fill in a unique lowercase URL slug, category, English/Macedonian/Albanian names and descriptions, and one or more images. Optional fields hold code, model, brand, material, weight, packaging, collection, colours and sizes XS–2XL. The category tag opens the filtered list of articles in the same group. The collection name puts family products first under Similar products; other articles from the same category follow.

For manual stock, add one row per colour and size in **Stock by colour and size**, matching the canonical colour name exactly. Enter a whole-number quantity; `0` displays currently unavailable. An omitted variant asks the visitor to confirm availability. For a product without sizes, leave the stock row size blank. Static stock is a snapshot: publishing the edited product triggers a new Netlify deploy before the public number changes. It is not connected to the ERP or real-time inventory.

Use `Visible in catalogue` to hide an item while keeping its data. Use `Featured` to show it on the homepage. A deleted product disappears from the public product pages on the next deploy. Images uploaded from the editor are saved under `static/images/uploads` in GitHub. The separate **Digital catalogue** editor controls its three translated cover texts, cover image and optional PDF upload. A PDF button and embedded viewer appear only after a PDF is added.

On the product page the visitor can set the quantity (minimum 1), and optionally choose colour and size. The main inquiry button prefills the separate `/contact/` form; email and WhatsApp links prefill the product, model code and selected options as alternatives. These are inquiry requests, not orders: price and availability are confirmed for the specific quantity and personalisation. Email links require an email app on the visitor’s device.

The homepage rotates three temporary example slides with dots, arrows and pause on hover/focus. Replace `static/images/hero.webp`, `static/images/tshirt.webp` and `static/images/invitation.webp` with your own final artwork, or edit the paths in `scripts/experience.mjs`. A 43 px logo space is reserved in header/footer via `logo-slot`; put the final logo in `static/images/` and replace the placeholder markup in `scripts/build.mjs` later.

The seven starter entries describe **types of work** and show visual examples, not supplier inventory. The apparel/invitation/cap example image is original ArtInk site artwork generated for this project; the example white mug photograph is [NordWood Themes on Unsplash](https://unsplash.com/photos/white-ceramic-mug-nDd3dIkkOLo). Replace example media with photographs of ArtInk's real work or supplier photos after obtaining their reuse permission and confirming each model. Avoid storing customers' personal details in product entries because these are public.

## SEO and privacy

The build produces individual HTML pages, page titles/descriptions, canonical/hreflang links, sitemap and robots file. Before launch, review product wording, attach the real domain using `SITE_URL`, add real imagery, and submit the sitemap to the search engine account you control. The privacy notice records only whether the visitor dismissed it in localStorage. The policy is a working draft tied to the current features; review it against your actual business data practices before public launch. No analytics scripts are installed. The live contact form uses Netlify Forms and the privacy text mentions this processing.
