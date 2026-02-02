#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Static generator for /blog

- Reads blog/posts/*.md (YAML-like frontmatter)
- Produces:
  - blog/posts/index.json  (with stable numeric ids)
  - blog/rss.xml
  - sitemap.xml
  - per-post pages: blog/<id>/index.html (pretty URLs)

Design: Keep IDs stable by loading existing index.json mapping slug->id.
"""

from __future__ import annotations

import os
import re
import json
import html
import datetime as dt

ROOT = "/root/wwwwowwwsandbox"
BLOG_DIR = os.path.join(ROOT, "blog")
POSTS_DIR = os.path.join(BLOG_DIR, "posts")
INDEX_JSON = os.path.join(POSTS_DIR, "index.json")
RSS_XML = os.path.join(BLOG_DIR, "rss.xml")
SITEMAP_XML = os.path.join(ROOT, "sitemap.xml")
ROBOTS_TXT = os.path.join(ROOT, "robots.txt")
TEMPLATE = os.path.join(BLOG_DIR, "templates", "post-page.html")

SITE = "https://bimarchi-pg.com"
BLOG_TITLE = "자유 실험실 | 부업·AI·봇·자동화·취미"
BLOG_DESC = "자유 실험실 — 부업·AI·봇·자동화·취미를 기록하는 블로그"


def parse_frontmatter(md: str):
    if not md.startswith('---'):
        return {}, md
    end = md.find('\n---', 3)
    if end == -1:
        return {}, md
    fm = md[3:end].strip()
    body = md[end+4:].lstrip()
    meta = {}
    for line in fm.splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k = k.strip()
        v = v.strip()
        if v.startswith('[') and v.endswith(']'):
            meta[k] = [x.strip() for x in v[1:-1].split(',') if x.strip()]
        else:
            meta[k] = v
    return meta, body


def strip_md(s: str) -> str:
    s = re.sub(r"```[\s\S]*?```", "", s)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", s)
    s = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", s)
    s = re.sub(r"[#>*_~-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_existing_ids():
    if not os.path.exists(INDEX_JSON):
        return {}
    try:
        data = json.load(open(INDEX_JSON, "r", encoding="utf-8"))
        out = {}
        for p in data.get('posts', []):
            slug = p.get('slug')
            pid = p.get('id')
            if slug and isinstance(pid, int):
                out[slug] = pid
        return out
    except Exception:
        return {}


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def render_post_page(slug: str, title: str, pid: int):
    tpl = open(TEMPLATE, "r", encoding="utf-8").read()
    out = tpl.replace("{{SLUG}}", slug).replace("{{TITLE}}", html.escape(title))
    out_dir = os.path.join(BLOG_DIR, str(pid))
    ensure_dir(out_dir)
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(out)


def build_index(posts):
    open(INDEX_JSON, "w", encoding="utf-8").write(json.dumps({"posts": posts}, ensure_ascii=False, indent=2))


def rfc2822_date(date_str: str) -> str:
    # Accept YYYY-MM-DD
    try:
        d = dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc)
    except Exception:
        d = dt.datetime.now(dt.timezone.utc)
    return d.strftime("%a, %d %b %Y %H:%M:%S GMT")


def build_rss(posts):
    items = []
    for p in posts[:20]:
        link = f"{SITE}/blog/{p['id']}/"
        desc = html.escape(p.get('excerpt') or "")
        items.append(f"""
    <item>
      <title>{html.escape(p.get('title') or '')}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <pubDate>{rfc2822_date(p.get('date') or '')}</pubDate>
      <description><![CDATA[{desc}]]></description>
    </item>""")

    rss = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss version=\"2.0\">
  <channel>
    <title>{BLOG_TITLE}</title>
    <link>{SITE}/blog/</link>
    <description>{BLOG_DESC}</description>
    <language>ko</language>
    <lastBuildDate>{dt.datetime.now(dt.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
{''.join(items)}
  </channel>
</rss>
"""
    open(RSS_XML, "w", encoding="utf-8").write(rss)


def build_sitemap(posts):
    urls = [
        (f"{SITE}/", "daily", "1.0"),
        (f"{SITE}/blog/", "daily", "0.8"),
        (f"{SITE}/blog/about/", "monthly", "0.3"),
        (f"{SITE}/blog/privacy/", "monthly", "0.3"),
        (f"{SITE}/blog/contact/", "monthly", "0.3"),
        (f"{SITE}/blog/rss.xml", "daily", "0.2"),
    ]
    for p in posts:
        urls.append((f"{SITE}/blog/{p['id']}/", "monthly", "0.6"))

    parts = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"]
    for loc, freq, pr in urls:
        parts.append(f"  <url>\n    <loc>{loc}</loc>\n    <changefreq>{freq}</changefreq>\n    <priority>{pr}</priority>\n  </url>\n")
    parts.append("</urlset>\n")
    open(SITEMAP_XML, "w", encoding="utf-8").write(''.join(parts))


def build_robots():
    open(ROBOTS_TXT, "w", encoding="utf-8").write(
        "User-agent: *\nAllow: /\n\nSitemap: https://bimarchi-pg.com/sitemap.xml\n"
    )


def main():
    ensure_dir(os.path.join(BLOG_DIR, "templates"))
    if not os.path.exists(TEMPLATE):
        raise SystemExit(f"Missing template: {TEMPLATE}")

    existing = load_existing_ids()
    next_id = (max(existing.values()) + 1) if existing else 1

    posts = []
    for fn in sorted(os.listdir(POSTS_DIR)):
        if not fn.endswith('.md'):
            continue
        slug = fn[:-3]
        md = open(os.path.join(POSTS_DIR, fn), 'r', encoding='utf-8').read()
        meta, body = parse_frontmatter(md)

        title = meta.get('title') or slug
        date = meta.get('date') or dt.date.today().isoformat()
        tags = meta.get('tags') or []
        if isinstance(tags, str):
            tags = [x.strip() for x in tags.split(',') if x.strip()]

        excerpt = meta.get('excerpt')
        if not excerpt:
            excerpt = strip_md(body)[:140]

        thumb = meta.get('thumbnail') or f"/blog/posts/thumbs/{slug}.jpg"

        pid = existing.get(slug)
        if not pid:
            pid = next_id
            existing[slug] = pid
            next_id += 1

        posts.append({
            "id": pid,
            "slug": slug,
            "title": title,
            "date": date,
            "excerpt": excerpt,
            "thumbnail": thumb,
            "tags": tags,
        })

        render_post_page(slug, title, pid)

    # newest first
    posts.sort(key=lambda x: (x.get('date',''), x.get('id',0)), reverse=True)

    build_index(posts)
    build_rss(posts)
    build_sitemap(posts)
    build_robots()

    print(f"Generated {len(posts)} posts")


if __name__ == '__main__':
    main()
