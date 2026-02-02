# blog/tools

## generate.py

Generates:
- `blog/posts/index.json`
- `blog/rss.xml`
- `/sitemap.xml`
- `/robots.txt`
- per-post pages: `blog/<id>/index.html`

Run:

```bash
cd /root/wwwwowwwsandbox
python3 blog/tools/generate.py
```

Notes:
- IDs are kept stable by reading existing `blog/posts/index.json` and preserving `slug -> id` mapping.
- New posts get the next numeric id.
