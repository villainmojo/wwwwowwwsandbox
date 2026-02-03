// Minimal static blog engine (index + post)
// - posts index: /blog/posts/index.json
// - posts content: /blog/posts/<slug>.md (with YAML frontmatter)

function qs(sel){return document.querySelector(sel)}
function qsa(sel){return [...document.querySelectorAll(sel)]}

function parseFrontmatter(md){
  if(!md.startsWith('---')) return {meta:{}, body: md}
  const end = md.indexOf('\n---', 3)
  if(end === -1) return {meta:{}, body: md}
  const fm = md.slice(3, end).trim()
  const body = md.slice(end + 4).trimStart()
  const meta = {}
  fm.split('\n').forEach(line=>{
    const idx=line.indexOf(':')
    if(idx===-1) return
    const k=line.slice(0,idx).trim()
    const v=line.slice(idx+1).trim()
    // arrays like [a,b]
    if(v.startsWith('[') && v.endsWith(']')){
      meta[k]=v.slice(1,-1).split(',').map(s=>s.trim()).filter(Boolean)
    } else {
      meta[k]=v
    }
  })
  return {meta, body}
}

function fmtDate(iso){
  try{
    const d = new Date(iso)
    return d.toLocaleDateString('ko-KR', {year:'numeric', month:'2-digit', day:'2-digit'})
  }catch{ return iso }
}

async function loadIndex(){
  const res = await fetch('/blog/posts/index.json')
  if(!res.ok) throw new Error('index load failed')
  return res.json()
}

function normalizeTags(tags){
  if(!tags) return []
  if(Array.isArray(tags)) return tags
  return String(tags).split(',').map(s=>s.trim()).filter(Boolean)
}

function renderCard(post){
  const tags = normalizeTags(post.tags)
  const el = document.createElement('article')
  el.className = 'card'
  const idOrSlug = (post.id ?? post.slug)
  const url = `/blog/${encodeURIComponent(String(idOrSlug))}/`
  const thumb = post.thumbnail ? `<a class="thumb" href="${url}"><img alt="" src="${post.thumbnail}" loading="lazy" decoding="async"></a>` : `<a class="thumb" href="${url}"></a>`
  el.innerHTML = `
    ${thumb}
    <div class="card-body">
      <h3 class="title"><a href="${url}">${post.title}</a></h3>
      <div class="meta">
        <span>${fmtDate(post.date)}</span>
        ${post.readingMinutes ? `<span>${post.readingMinutes}분</span>` : ''}
      </div>
      <div class="tags">${tags.map(t=>`<span class="tag">#${t}</span>`).join('')}</div>
    </div>
  `
  return el
}

function buildTagCounts(posts){
  const counts = new Map()
  posts.forEach(p=>{
    normalizeTags(p.tags).forEach(t=>{
      const key = String(t)
      counts.set(key, (counts.get(key) || 0) + 1)
    })
  })
  return [...counts.entries()].sort((a,b)=>b[1]-a[1]).map(([tag,count])=>({tag,count}))
}

function renderTagbar(allPosts, activeTag){
  const el = qs('#tagbar')
  if(!el) return
  const top = buildTagCounts(allPosts).slice(0, 12)
  el.innerHTML = ''

  const mk = (href, text, active=false) => {
    const a=document.createElement('a')
    a.className = 'chip' + (active ? ' active' : '')
    a.href = href
    a.textContent = text
    return a
  }

  el.appendChild(mk('/blog/', '전체', !activeTag))
  top.forEach(({tag,count})=>{
    el.appendChild(mk(`/blog/?tag=${encodeURIComponent(tag)}`, `#${tag} (${count})`, activeTag && tag.toLowerCase()===activeTag.toLowerCase()))
  })
}

function trackPage(){
  try{
    const p = location.pathname
    // avoid blocking render
    fetch(`/api/track?p=${encodeURIComponent(p)}`, {method:'GET', keepalive:true}).catch(()=>{})
  }catch{}
}

async function pageIndex(){
  document.title = `자유 실험실 | 부업·AI·봇·자동화·취미`;
  const grid = qs('#grid')
  const search = qs('#search')
  const tag = new URLSearchParams(location.search).get('tag')

  const index = await loadIndex()
  let posts = index.posts || []

  // render tag chips based on full set (before filtering)
  renderTagbar(posts, tag)

  if(tag){
    posts = posts.filter(p => normalizeTags(p.tags).map(x=>x.toLowerCase()).includes(tag.toLowerCase()))
    qs('#heroSubtitle').textContent = `#${tag} 태그 글 목록 (${posts.length})`
  }

  function applyFilter(){
    const q = (search.value||'').trim().toLowerCase()
    const filtered = !q ? posts : posts.filter(p => {
      const hay = [p.title, p.excerpt, normalizeTags(p.tags).join(' ')].join(' ').toLowerCase()
      return hay.includes(q)
    })
    grid.innerHTML=''
    filtered.forEach(p=>grid.appendChild(renderCard(p)))
    qs('#count').textContent = `${filtered.length}개 글`
  }

  search.addEventListener('input', applyFilter)
  applyFilter()
  trackPage()
}

async function pagePost(){
  const slug = new URLSearchParams(location.search).get('slug')
  if(!slug){
    qs('#post').innerHTML = '<div class="notice">글이 지정되지 않았습니다.</div>'
    return
  }

  const res = await fetch(`/blog/posts/${encodeURIComponent(slug)}.md`)
  if(!res.ok){
    qs('#post').innerHTML = '<div class="notice">글을 불러오지 못했습니다.</div>'
    return
  }
  const md = await res.text()
  const {meta, body} = parseFrontmatter(md)

  const title = meta.title || slug
  const date = meta.date ? fmtDate(meta.date) : ''
  const tags = normalizeTags(meta.tags)

  qs('#title').textContent = title
  qs('#date').textContent = date
  document.title = `${title} · 자유 실험실 | 부업·AI·봇·자동화·취미`;
  const tagsEl = qs('#tags')
  tagsEl.innerHTML = tags.map(t=>`<a class="tag" href="/blog/?tag=${encodeURIComponent(t)}">#${t}</a>`).join('')

  // markdown render via marked
  const html = window.marked.parse(body, {mangle:false, headerIds:false})
  qs('#content').innerHTML = html
  // performance: lazy-load images in rendered markdown
  qsa('#content img').forEach(img=>{ img.loading = 'lazy'; img.decoding = 'async' })
}

window.Blog = {pageIndex, pagePost}
