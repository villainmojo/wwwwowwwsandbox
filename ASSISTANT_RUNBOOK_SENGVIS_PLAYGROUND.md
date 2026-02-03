# SENGVIS Playground — Assistant Runbook (update this file whenever user gives new instructions)

Last updated: 2026-02-03 (UTC)

## 0) Purpose
This file exists so the assistant doesn’t “forget” operational details.
Update it whenever the user gives instructions about:
- deployment
- project structure
- UI/UX directives
- conventions/decisions

## 1) Project locations (on this server)
- Working copy (edit here): `/root/wwwwowwwsandbox`
- Live deploy target (served by web server): `/var/www/sengvis-playground`

## 2) Deployment (current)
### 2.1 Deploy script
- Script: `/root/wwwwowwwsandbox/deploy.sh`
- Deploy method: `rsync -av --delete` from repo → live dir
- Destination: `/var/www/sengvis-playground`
- Excludes: `.git/`, `.github/`, `api/`

### 2.2 Standard deploy steps
1) Make changes in `/root/wwwwowwwsandbox`
2) Run:
   ```bash
   cd /root/wwwwowwwsandbox
   ./deploy.sh
   ```
3) Verify live files contain expected markers:
   ```bash
   rg -n "nav-blog|blog-feature|자유실험실 블로그" /var/www/sengvis-playground/v2home/index.html
   ```

### 2.3 If changes don’t appear in browser
Likely caching (Cloudflare or browser).
- Test with cache-buster: `?v=YYYYMMDDHHMM`
- If Cloudflare proxy/cache is enabled: Purge cache for `/v2home/*` or purge everything.

## 3) Routing / URLs
- Prefer path-style URLs over `.html` for V2 home.
- V2 Home route:
  - URL: `/v2home/`
  - File: `/var/www/sengvis-playground/v2home/index.html`

## 4) UI directives (user instructions)
### 4.1 Blog emphasis on V2 home
User directive (2026-02-03):
- Add blog button in **top nav** and **also** in the section (services grid).
- Blog should be **more emphasized** than other cards.

Implementation notes:
- Top nav: `.nav-blog` (gradient pill)
- Section: `.bento-item.blog-feature` (wide featured card)
- Blog link: `/blog/` (opens in new tab)

## 5) Recent changes log (short)
- 2026-02-03: Added `/v2home/` folder route + updated V1 links to point to `/v2home/`.
- 2026-02-03: Added emphasized Blog button in V2 top nav + featured Blog card in services grid.
- 2026-02-03: Deployed to `/var/www/sengvis-playground` via `deploy.sh`.
