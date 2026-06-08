# pillayarnonbu2026.com

Pillayar Nonbu 2026 official hosting repository.

## Static Site

This repository is set up as a Hugo static site for GitHub Pages. The site uses the archived ENCNA/Weebly theme files from `team-ncna-locked/encna/www.encna.org`, local images copied from the existing ENCNA archive, crawler-friendly metadata, `robots.txt`, and Hugo-generated `sitemap.xml`.

Pages:

| Page | Purpose |
| --- | --- |
| Source | URL | Purpose |
| --- | --- | --- |
| `content/_index.md` | `/` | Home page for Pillayar Nonbu 2026 |
| `content/thirukarthigai-thirukalyanam.md` | `/thirukarthigai-thirukalyanam.html` | Thirukarthigai and Thirukalyanam event page |
| `content/pillayar-nonbu-2026.md` | `/pillayar-nonbu-2026.html` | Pillayar Nonbu event page |
| `content/faq.md` | `/faq.html` | Empty FAQ page ready for final content |

## Local Development

Run:

```bash
hugo server
```

Build:

```bash
hugo --gc --minify
```

The GitHub Actions workflow in `.github/workflows/pages.yml` builds the Hugo site and deploys the generated `public/` folder to GitHub Pages.
