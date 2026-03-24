#!/usr/bin/env python3
"""
field-notes HTML builder — generates a self-contained styled HTML report from a JSON config.

Usage:
    python3 build_html.py config.json output.html

The JSON config contains all variable data (metadata, sessions, photos, themes, actions).
This script contains all boilerplate (CSS, HTML shell, 4 style themes, email template, print styles).
"""
import base64, json, os, sys
from datetime import date

def b64_encode(photo_dir, fname):
    path = os.path.join(photo_dir, fname)
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

def build_photos_html(photos, photo_cache):
    if not photos:
        return ""
    cols = "cols-2" if len(photos) >= 2 else "cols-1"
    figs = ""
    for fname, cap in photos:
        src = photo_cache.get(fname, "")
        figs += f'<figure class="photo-figure"><img src="{src}" alt="{cap}" loading="lazy"><figcaption>{cap}</figcaption></figure>\n'
    return f'<div class="session-photos"><div class="photos-grid {cols}">{figs}</div></div>'

def build_research_html(items):
    if not items:
        return ""
    inner = ""
    for r in items:
        inner += f'<div class="research-item"><h5>{r["name"]}</h5><p>{r["desc"]}</p><a href="{r["url"]}" target="_blank">Source \u2197</a></div>\n'
    return f'<div class="research-panel"><div class="col-label">Further Reading</div><div class="research-items">{inner}</div></div>'

CSS = """
:root, html[data-style="warm-editorial"] { --bg:#FBF8F3;--surface:#F5EFE7;--accent:#C4765B;--text-dark:#2C1810;--text-mid:#6B5847;--text-muted:#8B6F47;--action-high-bg:#F9E5E1;--font-display:'Playfair Display',Georgia,serif;--font-body:'Inter',sans-serif;--badge-radius:50%;--card-radius:4px;--card-shadow:none;--bar-top:8px;--bar-bottom:8px;--wrap-max:820px; }
html[data-style="magazine-light"] { --bg:#FFFFFF;--surface:#F4F7FB;--accent:#2B4C7E;--text-dark:#0F1923;--text-mid:#4A5568;--text-muted:#718096;--action-high-bg:#E8EEF7;--font-display:'Cormorant Garamond',Georgia,serif;--font-body:'Jost',sans-serif;--badge-radius:50%;--card-radius:4px;--card-shadow:none;--bar-top:3px;--bar-bottom:0px;--wrap-max:820px; }
html[data-style="swiss-minimal"] { --bg:#FFFFFF;--surface:#F2F2F2;--accent:#000000;--text-dark:#000000;--text-mid:#444444;--text-muted:#888888;--action-high-bg:#E8E8E8;--font-display:'Inter',sans-serif;--font-body:'Inter',sans-serif;--badge-radius:0%;--card-radius:0px;--card-shadow:none;--bar-top:6px;--bar-bottom:0px;--wrap-max:760px; }
html[data-style="bold-modern"] { --bg:#F8F7FF;--surface:#EEECFC;--accent:#4F46E5;--text-dark:#0C0A1D;--text-mid:#4C4874;--text-muted:#7C7AA0;--action-high-bg:#E0DEFF;--font-display:'Syne',sans-serif;--font-body:'Inter',sans-serif;--badge-radius:50%;--card-radius:8px;--card-shadow:0 2px 8px rgba(79,70,229,0.08);--bar-top:10px;--bar-bottom:4px;--wrap-max:820px; }

html[data-style="swiss-minimal"] h2,html[data-style="swiss-minimal"] h3 { text-transform:uppercase;letter-spacing:0.04em; }
html[data-style="swiss-minimal"] em,html[data-style="swiss-minimal"] .event-intro { font-style:normal; }
html[data-style="magazine-light"] .session-badge { background:transparent;border:2px solid var(--accent);color:var(--accent); }
html[data-style="bold-modern"] .session-badge { width:40px;height:40px;font-size:18px; }
html[data-style="bold-modern"] .theme-card { border-left:none;border-top:4px solid var(--accent);box-shadow:var(--card-shadow);border-radius:var(--card-radius); }

* { margin:0;padding:0;box-sizing:border-box; }
body { background:var(--bg);font-family:var(--font-body);color:var(--text-dark);line-height:1.6; }
.bar { background:var(--accent); }.bar.top { height:var(--bar-top); }.bar.bottom { height:var(--bar-bottom); }
.wrap { max-width:var(--wrap-max);margin:0 auto;padding:0 24px 80px; }
h1,h2,h3 { font-family:var(--font-display);color:var(--text-dark); }
header { padding:48px 0 40px;border-bottom:1px solid rgba(196,118,91,0.15);margin-bottom:40px; }
.eyebrow { font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--text-muted);margin-bottom:14px; }
h1 { font-size:36px;line-height:1.2;margin-bottom:16px; }
.meta { font-size:13px;color:var(--text-muted);margin-bottom:20px;display:flex;gap:20px;flex-wrap:wrap; }
.event-intro { font-family:var(--font-display);font-style:italic;font-size:17px;color:var(--text-mid);line-height:1.65; }
.themes-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-bottom:48px; }
.theme-card { background:var(--surface);border-left:4px solid var(--accent);border-radius:var(--card-radius);padding:20px 22px; }
.theme-num { width:32px;height:32px;background:var(--accent);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;margin-bottom:10px; }
.theme-card p { font-size:14px;line-height:1.55; }
.day-heading { font-size:22px;margin:40px 0 20px;padding-bottom:12px;border-bottom:2px solid var(--accent);color:var(--accent); }
.session { position:relative;padding-left:52px;margin-bottom:16px; }
.session-badge { position:absolute;left:0;top:4px;width:36px;height:36px;background:var(--accent);color:#fff;border-radius:var(--badge-radius);display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700; }
.session-meta { margin-bottom:20px; }
.session-time { font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--text-muted);margin-bottom:6px; }
.session-title { font-size:24px;line-height:1.25;margin-bottom:6px; }
.session-speaker { font-size:14px;color:var(--text-mid);font-style:italic; }
.session-divider { border:none;border-top:1px solid rgba(196,118,91,0.15);margin:40px 0; }
.session-photos { margin-bottom:24px; }
.photos-grid { display:grid;gap:12px; }.photos-grid.cols-1 { grid-template-columns:1fr; }.photos-grid.cols-2 { grid-template-columns:repeat(2,1fr); }
.photo-figure { margin:0; }.photo-figure img { width:100%;height:auto;border-radius:4px;display:block; }
.photo-figure figcaption { font-family:var(--font-display);font-style:italic;font-size:12px;color:var(--text-muted);margin-top:6px;line-height:1.4; }
.session-body { display:grid;grid-template-columns:3fr 2fr;gap:32px; }.session-body.full { grid-template-columns:1fr; }
.col-label { font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--text-muted);margin-bottom:12px;font-weight:600; }
.notes-list { padding-left:18px; }.notes-list li { margin-bottom:14px;font-size:14px;line-height:1.65; }.notes-list li::marker { color:var(--accent); }
.session-note { margin-top:16px;padding:12px 16px;background:var(--action-high-bg);border-radius:var(--card-radius);font-size:13px;font-weight:600;color:var(--accent); }
.research-panel { background:var(--surface);border-radius:var(--card-radius);padding:20px; }
.research-item { margin-bottom:16px; }.research-item:last-child { margin-bottom:0; }
.research-item h5 { font-size:13px;font-weight:700;margin-bottom:4px; }
.research-item p { font-size:13px;line-height:1.55;color:var(--text-mid);margin-bottom:4px; }
.research-item a { font-size:12px;color:var(--accent);text-decoration:none;font-weight:500; }
#actions { margin-top:48px; }#actions h2 { margin-bottom:20px; }
.action-item { display:flex;align-items:flex-start;justify-content:space-between;padding:16px 20px;border-radius:var(--card-radius);margin-bottom:10px; }
.action-item.high { background:var(--action-high-bg); }.action-item.medium,.action-item.low { background:var(--surface); }.action-item.low { opacity:0.8; }
.action-left { display:flex;align-items:flex-start;gap:12px;flex:1; }.action-left input { margin-top:4px;accent-color:var(--accent); }
.action-text p { font-size:14px;font-weight:600;margin-bottom:2px; }
.action-context { font-family:var(--font-display);font-style:italic;font-size:13px;color:var(--text-mid);font-weight:400 !important; }
.priority-badge { font-size:10px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:20px;white-space:nowrap; }
.priority-badge.high { background:var(--accent);color:#fff; }.priority-badge.medium { background:var(--text-muted);color:#fff; }.priority-badge.low { background:var(--text-muted);color:#fff;opacity:0.6; }
.footer-text { text-align:center;font-size:12px;color:var(--text-muted);padding:32px 0; }
.style-switcher { position:fixed;top:16px;right:16px;z-index:200;display:flex;flex-direction:column;gap:4px;align-items:flex-end; }
.style-switcher button { background:rgba(255,255,255,0.92);color:var(--text-dark);border:1px solid rgba(0,0,0,0.12);padding:5px 12px;font-family:var(--font-body);font-size:11px;font-weight:600;letter-spacing:.04em;cursor:pointer;border-radius:20px;backdrop-filter:blur(4px);transition:background .15s,color .15s,border-color .15s;white-space:nowrap; }
.style-switcher button.active { background:var(--accent);color:#fff;border-color:var(--accent); }
.download-btn,.email-btn { position:fixed;right:28px;min-width:160px;text-align:center;font-family:'Inter',sans-serif;font-size:13px;font-weight:600;letter-spacing:.04em;padding:11px 22px;border-radius:4px;cursor:pointer;z-index:100; }
.download-btn { bottom:28px;background:#C4765B;color:#FBF8F3;border:none;box-shadow:0 2px 12px rgba(196,118,91,0.35); }.download-btn:hover { background:#B36548; }
.email-btn { bottom:80px;background:#FBF8F3;color:#C4765B;border:2px solid #C4765B;box-shadow:0 2px 10px rgba(196,118,91,0.2); }.email-btn:hover { background:#F5EFE7; }
@media (max-width:640px) { .session-body { grid-template-columns:1fr; }.themes-grid { grid-template-columns:1fr; }.session { padding-left:0; }.session-badge { position:static;margin-bottom:12px; } }
@media (max-width:500px) { .photos-grid.cols-2 { grid-template-columns:1fr; } }
@media print { .download-btn,.email-btn,.style-switcher { display:none; } body { font-size:13px; }.wrap { padding:0 0 40px; }.bar { -webkit-print-color-adjust:exact;print-color-adjust:exact; }.theme-card { -webkit-print-color-adjust:exact;print-color-adjust:exact;break-inside:avoid; }.session { break-inside:avoid; }.action-item { -webkit-print-color-adjust:exact;print-color-adjust:exact;break-inside:avoid; }.session-body { display:block; }.research-panel { -webkit-print-color-adjust:exact;print-color-adjust:exact;width:100%;margin-top:16px; }.notes-list li::marker { -webkit-print-color-adjust:exact;print-color-adjust:exact; } h2,h3,h4 { break-after:avoid; }.themes-grid { grid-template-columns:repeat(3,1fr);gap:10px; }.theme-card { padding:14px 16px; }.theme-card p { font-size:12px; } @page { size:A4 portrait;margin:18mm 16mm; } }
"""

def build_html(config, output_path):
    c = config
    photo_dir = c.get("photo_dir", "")

    # Encode photos
    photo_cache = {}
    if photo_dir and os.path.isdir(photo_dir):
        for s in c.get("sessions", []):
            for photo in s.get("photos", []):
                fname = photo[0]
                if fname not in photo_cache:
                    photo_cache[fname] = b64_encode(photo_dir, fname)
                    print(f"  Encoded {fname}")

    # Build themes
    themes_html = ""
    for i, t in enumerate(c.get("themes", []), 1):
        themes_html += f'<div class="theme-card"><div class="theme-num">{i}</div><p><strong>{t["title"]}</strong> {t["desc"]}</p></div>\n'

    # Build sessions
    session_articles = ""
    current_day = ""
    for i, s in enumerate(c.get("sessions", []), 1):
        day = s.get("day", "")
        if day and day != current_day:
            current_day = day
            session_articles += f'<h2 class="day-heading">{current_day}</h2>\n'

        bullets = "".join(f"<li>{b}</li>" for b in s.get("bullets", []))
        speaker = s.get("speaker", "")
        if s.get("company"):
            speaker += f', {s["company"]}'

        rp = build_research_html(s.get("research", []))
        body_class = "session-body" if rp else "session-body full"
        badge = s.get("badge", str(i))
        note = ""
        if s.get("note"):
            note = f'<div class="session-note">{s["note"]}</div>'

        session_articles += f'''
<article class="session" id="s{i}">
  <div class="session-badge">{badge}</div>
  <div class="session-meta">
    <div class="session-time">{s.get("label", f"Session {i}")}</div>
    <h3 class="session-title">{s["title"]}</h3>
    <p class="session-speaker">{speaker}</p>
  </div>
  {build_photos_html(s.get("photos", []), photo_cache)}
  <div class="{body_class}">
    <div>
      <div class="col-label">Key Takeaways</div>
      <ul class="notes-list">{bullets}</ul>
      {note}
    </div>
    {rp}
  </div>
</article>
<hr class="session-divider">
'''

    # Build actions
    actions_html = ""
    for a in c.get("actions", []):
        pri = a["priority"].lower()
        actions_html += f'''<div class="action-item {pri}"><div class="action-left"><input type="checkbox" aria-label="Mark as complete"><div class="action-text"><p>{a["text"]}</p><p class="action-context">{a["context"]}</p></div></div><span class="priority-badge {pri}">{a["priority"]}</span></div>\n'''

    # Build email
    email_chips = "".join(f'<span class="chip">{t["title"].rstrip(".")}</span>' for t in c.get("themes", []))
    email_units = ""
    for s in c.get("sessions", []):
        sub = s.get("speaker", "")
        if s.get("company"):
            sub += f", {s['company']}"
        summary = s["bullets"][0][:200] + "..." if s.get("bullets") and len(s["bullets"][0]) > 200 else (s["bullets"][0] if s.get("bullets") else "")
        email_units += f'<div class="unit"><p class="unit-title">{s["title"]}</p><p class="unit-sub">{sub}</p><p class="unit-summary">{summary}</p></div>\n'
    email_actions = "".join(f'<li>{a["text"]}</li>' for a in c.get("actions", []))

    # Meta
    meta_parts = []
    if c.get("date"):
        meta_parts.append(f'<span><em>Date:</em> {c["date"]}</span>')
    if c.get("location"):
        meta_parts.append(f'<span><em>Location:</em> {c["location"]}</span>')
    if c.get("organiser"):
        meta_parts.append(f'<span><em>Organised by:</em> {c["organiser"]}</span>')
    meta_html = "\n      ".join(meta_parts)

    title = c.get("title", "Event Report")
    eyebrow = c.get("eyebrow", "Conference Summary")
    intro = c.get("intro", "")
    footer_date = c.get("date", "")
    footer_location = c.get("location", "")
    prepared = date.today().strftime("%-d %B %Y")
    report_slug = title.replace(" ", "-").replace("\u2014", "").replace("\u2013", "")

    email_meta = f'{c.get("date", "")} &middot; {c.get("location", "")}'

    email_html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{title}</title></head><body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;"><div class="email-wrap" style="max-width:600px;margin:24px auto;background:#FBF8F3;"><div style="height:8px;background:#C4765B;"></div><div style="padding:40px 40px 32px;"><p style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#8B6F47;margin:0 0 14px;">{eyebrow}</p><h1 style="font-family:Georgia,serif;font-size:28px;color:#2C1810;line-height:1.25;margin:0 0 10px;">{title}</h1><p style="font-size:13px;color:#8B6F47;margin:0 0 20px;">{email_meta}</p><p style="font-family:Georgia,serif;font-style:italic;font-size:15px;color:#6B5847;line-height:1.65;margin:0 0 32px;border-bottom:1px solid rgba(196,118,91,0.2);padding-bottom:28px;">{intro}</p><h2 style="font-family:Georgia,serif;font-size:18px;color:#2C1810;margin:0 0 14px;">Key Themes</h2><div style="margin-bottom:32px;">{email_chips}</div><h2 style="font-family:Georgia,serif;font-size:18px;color:#2C1810;margin:0 0 14px;">Sessions</h2>{email_units}<h2 style="font-family:Georgia,serif;font-size:18px;color:#2C1810;margin:0 0 14px;">Next Steps</h2><ul style="padding-left:20px;margin:0 0 32px;">{email_actions}</ul><div style="text-align:center;margin:32px 0;"><a id="cta-download" href="#" style="display:inline-block;background:#C4765B;color:#FBF8F3;text-decoration:none;padding:14px 28px;font-size:14px;font-weight:bold;letter-spacing:.04em;cursor:pointer;">View full report \u2192</a></div></div><div style="padding:16px 40px;text-align:center;font-size:11px;color:#A0917E;border-top:1px solid rgba(196,118,91,0.15);">Generated with the field-notes skill</div></div></body></html>'''
    email_escaped = email_html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    html = f'''<!DOCTYPE html>
<html lang="en" data-style="warm-editorial">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} \u2014 {eyebrow}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Syne:wght@600;700;800&family=Jost:wght@300;400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<nav class="style-switcher" aria-label="Design style">
  <button onclick="setStyle('warm-editorial')" data-s="warm-editorial">Warm Editorial</button>
  <button onclick="setStyle('magazine-light')" data-s="magazine-light">Magazine Light</button>
  <button onclick="setStyle('swiss-minimal')" data-s="swiss-minimal">Swiss Minimal</button>
  <button onclick="setStyle('bold-modern')" data-s="bold-modern">Bold Modern</button>
</nav>
<div class="bar top"></div>
<div class="wrap">
  <header>
    <div class="eyebrow">{eyebrow}</div>
    <h1>{title}</h1>
    <div class="meta">
      {meta_html}
    </div>
    <p class="event-intro">{intro}</p>
  </header>
  <section id="themes"><h2>Key Themes</h2><div class="themes-grid">{themes_html}</div></section>
  <section id="sessions">{session_articles}</section>
  <section id="actions"><h2>Next Steps</h2>{actions_html}</section>
  <p class="footer-text">{title} &middot; {footer_date} &middot; {footer_location} &middot; Notes prepared {prepared}</p>
</div>
<div class="bar bottom"></div>
<button class="download-btn" onclick="window.print()">Download as PDF</button>
<button class="email-btn" onclick="openEmailPreview()">Preview email</button>
<script>
function setStyle(s) {{ document.documentElement.setAttribute('data-style',s);localStorage.setItem('fn-style',s);document.querySelectorAll('.style-switcher button').forEach(b=>b.classList.toggle('active',b.dataset.s===s)); }}
(function(){{ setStyle(localStorage.getItem('fn-style')||'warm-editorial'); }})();
const emailHTML=`{email_escaped}`;
function openEmailPreview() {{
  const fullReportHTML='<!DOCTYPE html>'+document.documentElement.outerHTML;
  const reportTitle='{report_slug}';
  const win=window.open('','_blank');win.document.write(emailHTML);win.document.close();
  setTimeout(()=>{{
    const bar=win.document.createElement('div');bar.style.cssText='position:fixed;top:0;left:0;right:0;background:#2C1810;color:#FBF8F3;padding:10px 20px;font-family:Arial,sans-serif;font-size:12px;display:flex;justify-content:space-between;align-items:center;z-index:9999;box-sizing:border-box;gap:16px;user-select:none;-webkit-user-select:none;';
    bar.innerHTML='<span style="flex:1"><strong>Gmail:</strong> Cmd+A &rarr; Cmd+C to select and copy, then paste into Gmail compose &nbsp;&middot;&nbsp; <em style="opacity:.75">For email platforms: use the button &rarr;</em></span>';
    const copyBtn=win.document.createElement('button');copyBtn.textContent='Copy HTML source';copyBtn.style.cssText='background:#C4765B;color:#FBF8F3;border:none;padding:6px 14px;cursor:pointer;font-size:12px;font-weight:600;letter-spacing:.04em;flex-shrink:0;';
    copyBtn.onclick=()=>{{navigator.clipboard.writeText(emailHTML).catch(()=>{{}});copyBtn.textContent='Copied!';setTimeout(()=>copyBtn.textContent='Copy HTML source',2000);}};
    bar.appendChild(copyBtn);win.document.body.insertBefore(bar,win.document.body.firstChild);win.document.body.style.paddingTop='44px';
    const cta=win.document.getElementById('cta-download');
    if(cta){{ cta.addEventListener('click',function(e){{ e.preventDefault();const blob=new Blob([fullReportHTML],{{type:'text/html'}});const url=URL.createObjectURL(blob);const a=win.document.createElement('a');a.href=url;a.download=reportTitle+'.html';a.click();URL.revokeObjectURL(url); }}); }}
  }},100);
}}
</script>
</body></html>'''

    with open(output_path, "w") as f:
        f.write(html)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\nHTML written to: {output_path}")
    print(f"File size: {size_mb:.1f} MB")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 build_html.py config.json output.html")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        config = json.load(f)

    build_html(config, sys.argv[2])
