# DPP Madera website

A static website for the DPP Madera proof of concept. Plain HTML and CSS with relative links,
so it works on any static host and offline (download the folder, open `index.html`).
All data is invented (building ESM-01, seed 4411).

| Path | What it is |
|---|---|
| `index.html` | Landing page: the idea, the four records (DPP, EPM, DBL, DTw), routes per audience |
| `poc.html` | Proof of concept results: architecture, tests T1–T11, assembly state, example questions |
| `mockups/` | Five standalone mockups (A walkthrough, B scan app, C poster, D twin replay, E BPMN) |
| `twin/` | Static snapshot of the PoC's live assembly-state view, with each part's joined record as JSON |
| `figures/` | Figures from `docs/figures/` |

## Rebuild the parts generated from the PoC

```bash
make site      # regenerates twin/ and copies the figures
```

The mockups are built outside this repository; replace the files in `mockups/` to update them,
then re-add the fixed "DPP Madera home" link (`class="dppm-home"`) right after `<body>`.

## Publish

GitHub Pages serves this folder through `.github/workflows/pages.yml` on every push to `main`
that touches `site/`. One-time setup: **Settings → Pages → Build and deployment → Source: GitHub Actions**,
then run the `pages` workflow once (Actions tab → pages → Run workflow).
The address is then `https://<user>.github.io/dppmadera-poc/`.

## Connect a custom domain (for example dppcl.com)

Do this after buying the domain. Replace `dppcl.com` and `<user>` as needed.

1. In the repo: **Settings → Pages → Custom domain**, enter `dppcl.com`, save.
   (With the GitHub Actions source no `CNAME` file is needed; the setting is enough.) (Optional but recommended first: verify the domain under
   your GitHub account **Settings → Pages → Add a domain**, so nobody else can claim it.)
2. At the domain registrar's DNS settings, add:

   | Type | Name | Value |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |
   | CNAME | `www` | `<user>.github.io` |

   Remove any other A, AAAA or CNAME records on `@` and `www` (registrars often add a parking page).
3. Wait for DNS (minutes to a few hours), then tick **Enforce HTTPS** in Settings → Pages.
4. Check: `dig dppcl.com +short` should list the four `185.199.x.153` addresses.

Other static hosts (Netlify, Vercel, Cloudflare Pages) also work: upload this folder as is.
