---
name: field-notes
description: Transforms raw notes taken in the real world into polished, ready-to-share documents. Use this skill when the user was physically somewhere — a conference, trade show, workshop, site visit, client meeting, talk, or any other in-person event — and wants to turn their sparse, scribbly notes into a document others can read. This is a notes-from-presence problem: the user was there, they observed things, they took incomplete notes, and now they need those notes elevated into a shareable narrative enriched with research and photos.
tools:
  - WebSearch
  - WebFetch
  - Read
  - Write
  - Bash
triggers:
  - "conference notes"
  - "write up my notes"
  - "summarise my notes"
  - "turn these notes into"
  - "document from my notes"
  - "clean up my notes"
  - "notes from the conference"
  - "notes into a document"
  - "trade show notes"
  - "site visit notes"
  - "workshop notes"
  - "field notes"
  - "notes from today"
  - "write up what I saw"
---

# Field Notes Skill

You transform raw, incomplete notes taken while someone was physically present at an event or place into polished, ready-to-share documents. The notes are always sparse — speaker names, company logos, a keyword, a scribbled phrase. Your job is to fill in the gaps using external references, enrich with research, incorporate photos, and produce an elevated narrative that communicates clearly to someone who was not there.

This is a **notes-from-presence** problem. It is distinct from meeting transcription tools (Granola, Otter, Fireflies) which process audio in real time. This skill works from manual notes taken after or during physical presence.

---

## Event Type Reference

Detect the event type from the notes and context, then use this table to guide every subsequent step.

| Event Type | Unit of output | Reference to look up | Matching signals | Eyebrow label |
|---|---|---|---|---|
| **Conference / multi-session event** | Session | Official published agenda | Speaker name, company, topic keyword | Conference Summary |
| **Trade show / expo** | Company / booth | Company website, product pages | Company name, logo, booth number | Trade Show Report |
| **Workshop / training** | Module or exercise | Trainer's website, methodology page | Module title, exercise name, framework | Workshop Notes |
| **Site visit / client visit** | Observation area or topic | Company website, recent news | Location, project, stakeholder name | Site Visit Report |
| **Talk / lecture (single speaker)** | Talk segment or theme | Speaker bio, speaker's company | Topic keywords, speaker name | Talk Summary |

If the event type is ambiguous, make a best-guess from the notes and proceed — do not ask the user to categorise it.

---

## Workflow

### Step 1: Intake

If the user has not already pasted their notes, ask them to do so now. Accept notes in any format — bullet points, stream-of-consciousness, partial sentences, or structured text.

If a file path is mentioned, read the file.

Also ask if they have any photos taken during the event (slides on screen, speakers on stage, whiteboards, products, signage, site conditions). If yes, ask for the file paths. Read each image using the `Read` tool.

### Step 1b: Photo Curation

If the user provides a folder path, first count the photos:

```bash
ls /path/to/folder | wc -l
```

Read all photos in batches of 10–14 using the `Read` tool. For each photo, note:
- What is visible (slide, speaker, booth, product, whiteboard, crowd, signage, unclear)
- Which unit it likely belongs to (session, booth, module, area)
- Whether it adds **distinct information** not already captured by another photo

#### Inclusion rule: usefulness, not budget

Include every photo that contains **unique, useful content** — a different slide, a different data point, a different speaker, a different demo screen, a different product. There is no fixed cap per session or per unit; the only constraint is distinctness.

**Drop** a photo only if it meets one of these criteria:
1. **Near-duplicate** — substantially the same slide or subject already captured in another photo with equal or better clarity
2. **No identifiable content** — blurry, dark, or purely atmospheric (crowd shot, venue exterior) with no readable text or recognisable subject
3. **Pure recap** — a summary slide where every element on it is already captured individually in better detail in other photos

If any photos are dropped, present a brief list to the user:

```
Dropped N of M photos:

✗ [filename] — [reason: "near-duplicate of [other filename]", "recap slide — all elements captured individually", "blurry / no readable content"]
...

Proceeding with the remaining N photos. Reply "all" to include everything, or list filenames to restore.
```

If no photos are dropped, skip the list and proceed directly.

Use only the curated set in all subsequent steps.

### Step 1c: Photo Correction

After curation, run perspective correction and enhancement on all photos using Python with OpenCV. This step improves readability of slides and screens photographed from audience angles.

**Requires:** `opencv-python-headless` and `numpy`. If not installed, run `pip3 install opencv-python-headless` first.

**What it does for each photo:**

1. **Screen detection** — Uses brightness thresholding (projected slides are bright in dark venues) followed by contour detection to find the largest rectangular region. Tries multiple threshold values (120, 100, 80, 140) and falls back to edge detection (Canny) if needed.

2. **Perspective correction** — If a four-cornered screen region is found with a reasonable aspect ratio (between 1:1 and 3:1), applies a four-point perspective transform to produce a flat, rectangular crop of the slide content.

3. **Enhancement** — Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) on the L channel in LAB color space to improve contrast and readability, particularly for dim projected slides.

**Decision logic:**
- If a screen contour is found and the corrected output is at least 300px wide and 200px tall → **correct and enhance** (crop to slide, straighten, enhance)
- If no screen is detected → **enhance only** (keep original framing, apply CLAHE)

Save corrected photos to a `-Corrected` subfolder alongside the originals. Use the corrected versions in all subsequent steps (HTML output, base64 encoding).

```python
# Key functions (abbreviated — full implementation uses OpenCV):
# find_screen(image) → finds largest bright rectangle via threshold + contour
# four_point_transform(image, pts) → perspective warp to flat rectangle
# enhance_slide(image) → CLAHE on LAB L-channel
# correct_photo(filepath, out_path) → orchestrates detection → correction → enhancement
```

Report results to the user:
```
Photo correction: N corrected, M enhanced only, total T
```

---

### Step 2: Analyse and Tag Photos

For each photo, extract every identifying signal visible:
- Speaker or presenter name — badges, slide title cards, lower-thirds, signage
- Company or organisation name — logos, slide headers, booth branding
- Topic, session title, or product name — slide headings, banners, displays
- Visual content — charts, frameworks, key quotes, physical conditions (note as context, not elevated notes)

For each photo produce an internal tag (not shown to user):
```
Photo: [filename]
Signals: [names, companies, topics identified]
Likely unit: [best-guess session / booth / module / area]
Confidence: [high / medium / low]
```

Use these tags in Step 5 to place photos correctly.

If a photo cannot be matched with reasonable confidence, place it in an `## Unmatched Photos` section at the end of the document.

### Step 3: Clarify and Detect Event Type

Identify the event type using the Event Type Reference table above.

Then ask only what you cannot reasonably infer from the notes:
- Event name and date/year
- Intended audience (personal reference, team, public blog post, stakeholder report)
- Any sections the user wants to skip

Do not ask unnecessary questions. If the notes make the context clear, proceed directly.

### Step 4: Fetch Reference Material

Use the event type to determine what to look up. Use `WebSearch` first to find the right page, then `WebFetch` to retrieve and extract the structured data.

**Conference / multi-session event**
Search for the published agenda:
- `"[Event Name] [Year] agenda"`
- `"[Event Name] [Year] schedule speakers"`

Extract: official session titles (exactly as published), speaker names, company affiliations, track/time slot.

**Trade show / expo**
For each company or booth mentioned in the notes, search for their website and product pages. Extract: what the company does, key products or announcements relevant to the context.

**Workshop / training**
Search for the trainer or training organisation's website and the specific methodology or framework covered. Extract: official module/exercise names, framework name and origin, trainer's background.

**Site visit / client visit**
Search for the company or project being visited. Extract: what they do, recent news, relevant context for the observations.

**Talk / lecture**
Search for the speaker's name + organisation. Extract: speaker bio, role, company, the talk title if published.

If reference material cannot be found, proceed using the notes as-is and flag affected sections with `*(unverified)*`.

### Step 5: Match Notes and Photos to Units

For each block of notes, identify which unit (session, booth, module, observation area, or talk segment) it refers to. Use the matching signals from the Event Type Reference table.

For each photo, cross-reference the internal tags from Step 2 against the units identified from reference material. Assign each photo to its most likely unit.

**For conferences:** Use the exact official session title from the agenda as the heading. Match on speaker name, company name, topic keywords, or note order relative to the schedule. Many agendas do not publish all session titles — if a title is unavailable, use the confirmed speaker name and company as the heading and omit the `*(unmatched)*` marker, since the speaker attribution is already confirmed. Only use `*(unmatched)*` when neither the session title nor the speaker can be verified against the agenda.

**For trade shows:** Group notes by company/booth. Use the company name as the heading. If a booth was visited but the company name is unclear from the notes, use any logo, product, or keyword as a search signal.

**For workshops:** Use official module or exercise names from the trainer's materials. If not found, use the user's own description.

**For site visits:** Organise by observation area or topic (e.g. "Production Floor", "Logistics Process", "Team Structure"). Use the user's notes to determine groupings.

**For talks:** No multi-unit matching needed. Organise the notes into thematic segments within one continuous piece.

### Step 6: Research Entities

Scan all notes for named entities — companies, products, tools, frameworks, technologies, people, concepts, ideas — that are distinct from the reference material already gathered in Step 4.

For each entity worth expanding:
1. Use `WebSearch` to find a brief, authoritative description.
2. Capture a 1–3 sentence summary and source URL.
3. Prioritise entities that are novel, niche, or unfamiliar to the intended audience. Skip common knowledge unless context makes it relevant.

### Step 7: Generate Markdown Output

Produce a single Markdown document containing:
1. Header and overview
2. Key themes / takeaways (as a numbered list)
3. Main body — structured per the detected event type (see Output Structures below)
4. Next Steps (action items, if any)

Use the Output Structures and Writing Guidelines below.

### Step 8: Generate HTML Webpage

After saving the Markdown, generate a polished HTML version saved alongside it as `[Event Name].html`.

**Use the reusable builder** at `~/.claude/skills/field-notes/build_html.py`. Instead of writing a full HTML build script from scratch each time:

1. Write a JSON config file to `/tmp/[event-slug]-config.json` containing all variable data: metadata (title, eyebrow, date, location, organiser, intro), photo_dir, sessions (with photos, bullets, research), themes, and actions.
2. Run: `python3 ~/.claude/skills/field-notes/build_html.py /tmp/[event-slug]-config.json "[Event Name].html"`
3. The builder handles all boilerplate: CSS for 4 style themes, HTML shell, style switcher, email template with download CTA, print styles, and photo base64 encoding.

If photos are local file paths, the builder base64-encodes them for a self-contained file. Set `photo_dir` in the config to the corrected photos folder.

Confirm the file was written and report its size.

---

## Output Structures

Use the structure that matches the detected event type. All types share the same header, key themes, and next steps sections. Only the main body section changes.

### Shared: Header and Key Themes

```markdown
# [Event Name] — [Eyebrow label from Event Type Reference]
**Date:** [date]
**Prepared for:** [audience]

## Overview
[2–3 sentence high-level description of the event and its purpose.]

## Key Themes
1. **[Bold headline]** — [One sentence description of the insight or takeaway.]
2. **[Bold headline]** — [One sentence description.]
...
(Aim for 5–7 themes. These serve as the overall takeaways — no separate takeaways section is needed.)
```

---

### Conference / multi-session event — Session Notes

```markdown
## Session Notes

<table><tr>
<td width="60%" valign="top">

### [Official Session Title]
**[Speaker Name]** · [Company / Affiliation]

![Caption](path/to/photo.jpg)

- [Elevated insight]
- [Elevated insight]

</td>
<td width="40%" valign="top">

#### Further reading
**[Entity name]** — [1–3 sentence description].
Source: [URL]

</td>
</tr></table>

---
```

Sessions with no further reading use plain Markdown without the table wrapper.

---

### Trade show / expo — Company Roundup

```markdown
## Companies & Booths

<table><tr>
<td width="60%" valign="top">

### [Company Name]
**[Product / Category]**

![Caption](path/to/photo.jpg)

- [What they do / what stood out, elevated for someone not at the booth]
- [Key product, announcement, or differentiator observed]
- [Anything that surprised, challenged assumptions, or felt genuinely new]

**Follow-up interest:** [High / Medium / Low]
[One sentence explaining why — what would make this worth pursuing, or why it isn't.]

</td>
<td width="40%" valign="top">

#### About
**[Company Name]** — [1–3 sentence description from research].
Source: [URL]

</td>
</tr></table>

---
```

Extract follow-up interest signals from the notes (words like "intriguing", "impressive", "not sure", "worth a call", "already have a solution") and translate them into the High / Medium / Low rating with a single explanatory sentence.

---

### Workshop / training — Modules and Learnings

```markdown
## Modules

### [Module / Exercise Name]
**[Trainer Name]** · [Organisation / Methodology]

![Caption](path/to/photo.jpg)

- [Key concept or framework introduced, elevated for a non-attendee]
- [Key exercise or application]
- [How to apply this: practical implication]

#### Further reading
**[Framework / concept name]** — [description].
Source: [URL]

---
```

---

### Site visit / client visit — Observations and Implications

```markdown
## Observations

### [Observation Area or Topic]

![Caption](path/to/photo.jpg)

**What was seen:**
- [Observation, stated factually]
- [Observation]

**Implications:**
- [What this means for the project, client, or decision]

**Recommended actions:**
- [Specific next step or recommendation]

---
```

---

### Talk / lecture — Key Insights

```markdown
## Talk Notes
**[Speaker Name]** · [Role, Company]

![Caption](path/to/photo.jpg)

### [Theme or segment title]
- [Elevated insight]
- [Elevated insight]

### [Next theme]
...

#### Further reading
**[Entity name]** — [description].
Source: [URL]
```

---

## Writing Guidelines

### Elevating notes (most important)

Do not repeat the raw notes. Synthesise and rewrite for a reader who was not there. Every bullet should:

- **Lead with the core idea** as a clear principle or insight, not a task or observation.
- **Consolidate related raw points** into one meaningful bullet rather than listing them separately.
- **Add the "so what"** — the implication, reasoning, or relevance that makes it stand alone.
- **Use polished, accessible prose** — remove jargon, abbreviations, and event shorthand.
- **Aim for 2–3 bullets per unit** — this is a shareable summary, not a transcript. If a session generated 6 raw points, synthesise them into 2–3 strong ones. Prefer one sharp sentence over two vague ones.

Example transformation:

Raw:
```
- Build an experiment culture across the organisation — test everything, from YouTube thumbnails to messaging and channels.
- Maintain a log of all tests and learnings so the organisation builds institutional knowledge over time.
- Accept that 7 out of 10 tests will be inconclusive — the value is in the learning, not definitive results.
- De-risk by spending small budget on a smaller channel first, then roll out to bigger channels once validated.
```

Elevated:
```
- Embrace an organisation-wide culture of experimentation. This means testing everything from YouTube thumbnails to core messaging and channel mix, while diligently logging all results to build institutional knowledge.
- De-risk by testing small and learning cheap. Start with smaller budgets on less critical channels to gather data and insights before committing to larger-scale rollouts.
- Focus on the learning, not just the win. Accept that roughly 70% of experiments will be inconclusive; the true value lies in the directional learnings and accumulated wisdom, not just definitive victories.
```

### Other guidelines

- **Faithfulness**: Do not invent content. If something is unclear, reflect that uncertainty rather than guessing.
- **Official names**: Always use the exact published name (session title, company name, module name) over any paraphrase.
- **Unmatched content**: Mark with `*(unmatched)*` or `*(unverified)*` rather than silently guessing.
- **Photo placement**: Place photos directly after the unit heading and attribution line, before the bullets. Multiple photos for the same unit stack together. Unmatched photos go in `## Unmatched Photos` at the end.
- **Tone**: Match the intended audience. Default to professional but accessible.
- **Research quality**: Prefer primary sources (official docs, company sites, reputable press) over aggregator sites.
- **Omit gracefully**: Leave out any section that has no content rather than writing a placeholder.

---

## HTML Design Spec

### Design Styles

Every output includes **all four styles** in a single HTML file. A fixed style-switcher tab bar (top-right) lets the reader switch instantly — no reload. The active style is saved to `localStorage`. No need to ask the user which style they want.

| Style | `data-style` value | Fonts | Accent |
|---|---|---|---|
| **Warm Editorial** | `warm-editorial` | Playfair Display + Inter | Terracotta `#C4765B` |
| **Magazine Light** | `magazine-light` | Cormorant Garamond + Jost | Steel blue `#2B4C7E` |
| **Swiss Minimal** | `swiss-minimal` | Inter only | Black `#000000` |
| **Bold Modern** | `bold-modern` | Syne + Inter | Indigo `#4F46E5` |

Default on first load: `warm-editorial`.

---

### CSS Architecture

All colours, fonts, spacing, and radius tokens are CSS custom properties defined under `[data-style="..."]` selectors on `<html>`. Component styles reference `var(--token)` throughout. Structural overrides (badge shape, heading case, etc.) use `[data-style="..."] .component` selectors.

#### Token definitions

```css
:root, html[data-style="warm-editorial"] {
  --bg: #FBF8F3; --surface: #F5EFE7; --accent: #C4765B;
  --text-dark: #2C1810; --text-mid: #6B5847; --text-muted: #8B6F47;
  --action-high-bg: #F9E5E1;
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body: 'Inter', sans-serif;
  --badge-radius: 50%; --card-radius: 4px; --card-shadow: none;
  --bar-top: 8px; --bar-bottom: 8px; --wrap-max: 820px;
}
html[data-style="magazine-light"] {
  --bg: #FFFFFF; --surface: #F4F7FB; --accent: #2B4C7E;
  --text-dark: #0F1923; --text-mid: #4A5568; --text-muted: #718096;
  --action-high-bg: #E8EEF7;
  --font-display: 'Cormorant Garamond', Georgia, serif;
  --font-body: 'Jost', sans-serif;
  --badge-radius: 50%; --card-radius: 4px; --card-shadow: none;
  --bar-top: 3px; --bar-bottom: 0px; --wrap-max: 820px;
}
html[data-style="swiss-minimal"] {
  --bg: #FFFFFF; --surface: #F2F2F2; --accent: #000000;
  --text-dark: #000000; --text-mid: #444444; --text-muted: #888888;
  --action-high-bg: #E8E8E8;
  --font-display: 'Inter', sans-serif;
  --font-body: 'Inter', sans-serif;
  --badge-radius: 0%; --card-radius: 0px; --card-shadow: none;
  --bar-top: 6px; --bar-bottom: 0px; --wrap-max: 760px;
}
html[data-style="bold-modern"] {
  --bg: #F8F7FF; --surface: #EEECFC; --accent: #4F46E5;
  --text-dark: #0C0A1D; --text-mid: #4C4874; --text-muted: #7C7AA0;
  --action-high-bg: #E0DEFF;
  --font-display: 'Syne', sans-serif;
  --font-body: 'Inter', sans-serif;
  --badge-radius: 50%; --card-radius: 8px;
  --card-shadow: 0 2px 8px rgba(79,70,229,0.08);
  --bar-top: 10px; --bar-bottom: 4px; --wrap-max: 820px;
}
```

#### Structural overrides

```css
/* Swiss Minimal: uppercase headings, no italics */
html[data-style="swiss-minimal"] h2,
html[data-style="swiss-minimal"] h3 { text-transform: uppercase; letter-spacing: 0.04em; }
html[data-style="swiss-minimal"] em,
html[data-style="swiss-minimal"] .event-intro { font-style: normal; }

/* Magazine Light: outlined badges */
html[data-style="magazine-light"] .session-badge {
  background: transparent; border: 2px solid var(--accent); color: var(--accent);
}

/* Bold Modern: larger badges, top-border cards */
html[data-style="bold-modern"] .session-badge { width: 40px; height: 40px; font-size: 18px; }
html[data-style="bold-modern"] .theme-card {
  border-left: none; border-top: 4px solid var(--accent);
  box-shadow: var(--card-shadow); border-radius: var(--card-radius);
}
```

#### Component styles (use variables throughout)

```css
body { background: var(--bg); font-family: var(--font-body); color: var(--text-dark); }
.bar { background: var(--accent); }
.bar.top { height: var(--bar-top); }
.bar.bottom { height: var(--bar-bottom); }
.wrap { max-width: var(--wrap-max); }
h1, h2, h3 { font-family: var(--font-display); color: var(--text-dark); }
.eyebrow { color: var(--text-muted); }
.event-intro { color: var(--text-mid); font-family: var(--font-display); }
.session-badge { background: var(--accent); border-radius: var(--badge-radius); }
.theme-card { background: var(--surface); border-left: 4px solid var(--accent); border-radius: var(--card-radius); }
.research-panel, .implications-panel { background: var(--surface); border-radius: var(--card-radius); }
.action-item.high { background: var(--action-high-bg); }
/* etc. — all colour references use var() */
```

---

### Style switcher

Add this fixed panel to every output. Place the HTML just before the first `<div class="bar">`:

```html
<nav class="style-switcher" aria-label="Design style">
  <button onclick="setStyle('warm-editorial')" data-s="warm-editorial">Warm Editorial</button>
  <button onclick="setStyle('magazine-light')" data-s="magazine-light">Magazine Light</button>
  <button onclick="setStyle('swiss-minimal')" data-s="swiss-minimal">Swiss Minimal</button>
  <button onclick="setStyle('bold-modern')" data-s="bold-modern">Bold Modern</button>
</nav>
```

```css
.style-switcher {
  position: fixed; top: 16px; right: 16px; z-index: 200;
  display: flex; flex-direction: column; gap: 4px; align-items: flex-end;
}
.style-switcher button {
  background: rgba(255,255,255,0.92); color: var(--text-dark);
  border: 1px solid rgba(0,0,0,0.12); padding: 5px 12px;
  font-family: var(--font-body); font-size: 11px; font-weight: 600;
  letter-spacing: .04em; cursor: pointer; border-radius: 20px;
  backdrop-filter: blur(4px); transition: background .15s, color .15s, border-color .15s;
  white-space: nowrap;
}
.style-switcher button.active {
  background: var(--accent); color: #fff; border-color: var(--accent);
}
@media print { .style-switcher { display: none; } }
```

```js
function setStyle(s) {
  document.documentElement.setAttribute('data-style', s);
  localStorage.setItem('fn-style', s);
  document.querySelectorAll('.style-switcher button').forEach(b =>
    b.classList.toggle('active', b.dataset.s === s));
}
(function() {
  const saved = localStorage.getItem('fn-style') || 'warm-editorial';
  setStyle(saved);
})();
```

---

### Fonts

Load all four font families in a single Google Fonts import at the top of `<head>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Syne:wght@600;700;800&family=Jost:wght@300;400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Colour palette

### Global layout (Warm Editorial defaults — adapt per style)
- 8px accent bar at top and bottom (`<div class="bar">`) — see per-style notes for bar variations
- `.wrap`: `max-width: 820px`, centred, `padding: 0 24px 80px` (Swiss Minimal: 760px)
- Section headings: primary heading font at 28px
- No sticky nav

### Header
```html
<header>
  <div class="eyebrow">[Eyebrow label from Event Type Reference]</div>
  <h1>[Event Name]</h1>
  <div class="meta">
    <span><em>Date:</em> [date]</span>
    <span><em>Location:</em> [venue if known]</span>
    <span><em>Organised by:</em> [organiser if known]</span>
  </div>
  <p class="event-intro">[2–3 sentence event description in Playfair italic]</p>
</header>
```

Omit meta fields that are unknown rather than leaving them blank.

### Key Themes section (`id="themes"`)
Responsive card grid (`repeat(auto-fill, minmax(280px, 1fr))`). Aim for 5–7 cards. Each card:
```html
<div class="theme-card">
  <div class="theme-num">[n]</div>
  <p><strong>[Bold headline].</strong> [One sentence description.]</p>
</div>
```
`theme-num`: 32px terracotta circle. Cards: 4px left terracotta border, `#F5EFE7` background.

### Main body section (`id="sessions"` or `id="content"`)
Each unit is an `<article class="session" id="s[n]">` with a numbered terracotta circle badge (`.session-badge`) positioned absolutely to the left.

```html
<article class="session" id="s[n]">
  <div class="session-badge">[n]</div>
  <div class="session-meta">
    <div class="session-time">[type label — e.g. "Session 3" / "Booth" / "Module 2" / "Observation"]</div>
    <h3 class="session-title">[Unit Title]</h3>
    <p class="session-speaker">[Attribution line — speaker, company, category, etc.]</p>
  </div>

  <div class="session-photos">
    <div class="photos-grid cols-2">
      <figure class="photo-figure">
        <img src="[path]" alt="[alt]">
        <figcaption>[Caption in Playfair italic]</figcaption>
      </figure>
    </div>
  </div>

  <!-- 3fr / 2fr grid: notes left, research/about right -->
  <div class="session-body">
    <div>
      <div class="col-label">[Left column label — "Key Takeaways" / "Observations" / "Learnings"]</div>
      <ul class="notes-list">
        <li>[Elevated insight]</li>
      </ul>
    </div>
    <div class="research-panel">
      <div class="col-label">[Right column label — "Further Reading" / "About"]</div>
      <div class="research-items">
        <div class="research-item">
          <h5>[Entity name]</h5>
          <p>[1–3 sentence description.]</p>
          <a href="[url]" target="_blank">[label] ↗</a>
        </div>
      </div>
    </div>
  </div>
</article>
```

Units with no right-column content use `<div class="session-body full">` (single column, `grid-template-columns: 1fr`).

Speaker/attribution credits use Inter italic. Do not use em dashes (`—`) anywhere — use commas, colons, or rewrite the sentence.

### Inline data tables
```html
<div class="session-table-wrap">
  <table class="session-table">
    <thead><tr><th>Column A</th><th>Column B</th></tr></thead>
    <tbody><tr><td>Value</td><td>Value</td></tr></tbody>
  </table>
</div>
```

### Next Steps section (`id="actions"`)
```html
<div class="action-item high|medium|low">
  <div class="action-left">
    <input type="checkbox" aria-label="Mark as complete">
    <div class="action-text">
      <p>[Action description]</p>
      <p class="action-context">[Context in Playfair italic]</p>
    </div>
  </div>
  <span class="priority-badge high|medium|low">High|Medium|Low</span>
</div>
```
High: `#F9E5E1` background / terracotta badge. Medium: `#FBF8F3` / mid-brown badge. Low: `#F5EFE7` / muted badge.

### Footer
```html
<p class="footer-text">[Event Name] · [Date] · [Venue if known] · Notes prepared [date]</p>
```

### Download as PDF and Preview email buttons

Add two fixed floating buttons. "Download as PDF" triggers native browser print-to-PDF. "Preview email" opens the distilled email version (see Email Newsletter section below) in a new browser tab where it can be selected and copied into Gmail.

```html
<button class="download-btn" onclick="window.print()">Download as PDF</button>
<button class="email-btn" onclick="openEmailPreview()">Preview email</button>
```

CSS for the buttons:
```css
.download-btn, .email-btn {
  position: fixed; right: 28px;
  min-width: 160px; text-align: center;
  font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; letter-spacing: .04em;
  padding: 11px 22px; border-radius: 4px; cursor: pointer; z-index: 100;
}
.download-btn {
  bottom: 28px;
  background: #C4765B; color: #FBF8F3; border: none;
  box-shadow: 0 2px 12px rgba(196,118,91,0.35);
}
.download-btn:hover { background: #B36548; }
.email-btn {
  bottom: 80px;
  background: #FBF8F3; color: #C4765B; border: 2px solid #C4765B;
  box-shadow: 0 2px 10px rgba(196,118,91,0.2); transition: background .15s;
}
.email-btn:hover { background: #F5EFE7; }
```

### Email Newsletter Output

After generating the full HTML report, also embed a distilled email version as a JS template literal at the bottom of the file. This is a 600px-wide, system-font, Gmail-compatible HTML document that readers can paste directly into Gmail compose or any ESP (Mailchimp, Beehiiv, etc.).

**What to include in the email version:**

| Section | Content |
|---------|---------|
| Top bar | 8px terracotta bar |
| Header | Eyebrow · Title · Date/meta · 2-sentence overview (italic intro) |
| Key Themes | Theme **names only** as horizontal chips (no descriptions) |
| Units | Title + speaker/subtitle + **one key sentence** per unit |
| For trade show | Include follow-up interest badge (High/Medium/Low) inline before the sentence |
| Action Items | Bullet list of action text only (no owner/deadline/context) |
| CTA button | Terracotta "View full report →" that downloads the full report HTML file when clicked from the email preview |
| Footer | "Generated with the field-notes skill" |

**Omit from email:** session notes detail, research panels, implications panel, photos, further reading.

**Email CSS rules (all inline-compatible, no Grid):**
```css
body { margin: 0; padding: 0; background: #f4f4f4; font-family: Arial, Helvetica, sans-serif; }
.email-wrap { max-width: 600px; margin: 24px auto; background: #FBF8F3; }
.bar { height: 8px; background: #C4765B; }
.content { padding: 40px 40px 32px; }
.eyebrow { font-size: 10px; letter-spacing: .2em; text-transform: uppercase; color: #8B6F47; margin-bottom: 14px; }
h1 { font-family: Georgia, 'Times New Roman', serif; font-size: 28px; color: #2C1810; line-height: 1.25; margin: 0 0 10px; }
.meta { font-size: 13px; color: #8B6F47; margin-bottom: 20px; }
.intro { font-family: Georgia, serif; font-style: italic; font-size: 15px; color: #6B5847; line-height: 1.65; margin-bottom: 32px; border-bottom: 1px solid rgba(196,118,91,0.2); padding-bottom: 28px; }
h2 { font-family: Georgia, serif; font-size: 18px; color: #2C1810; margin: 0 0 14px; }
.chips { margin-bottom: 32px; }
.chip { display: inline-block; background: #F5EFE7; border-left: 3px solid #C4765B; padding: 6px 12px; font-size: 12px; color: #3D2E1F; margin: 0 6px 6px 0; }
.unit { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid rgba(196,118,91,0.15); }
.unit:last-child { border-bottom: none; }
.unit-title { font-family: Georgia, serif; font-size: 16px; color: #2C1810; margin: 0 0 4px; }
.unit-sub { font-size: 12px; color: #8B6F47; margin: 0 0 8px; }
.unit-summary { font-size: 14px; color: #3D2E1F; line-height: 1.6; margin: 0; }
/* Trade show only: */
.interest { display: inline-block; font-size: 10px; font-weight: bold; letter-spacing: .1em; text-transform: uppercase; padding: 2px 8px; color: #FBF8F3; margin-right: 6px; }
.interest.high { background: #C4765B; } .interest.medium { background: #A67C52; } .interest.low { background: #8B6F47; }
.actions-list { padding-left: 20px; margin: 0 0 32px; }
.actions-list li { font-size: 14px; color: #3D2E1F; line-height: 1.6; margin-bottom: 6px; }
.cta-wrap { text-align: center; margin: 32px 0; }
.cta { display: inline-block; background: #C4765B; color: #FBF8F3; text-decoration: none; padding: 14px 28px; font-size: 14px; font-weight: bold; letter-spacing: .04em; }
.footer-note { padding: 16px 40px; text-align: center; font-size: 11px; color: #A0917E; border-top: 1px solid rgba(196,118,91,0.15); }
```

**Embed the email HTML and wire the preview button** (place at the bottom of the main HTML file, before `</body>`):

The email template's CTA button ("View full report →") must work as a **self-contained download link** when clicked from the email preview. When the reader clicks it, the full report HTML is saved as a local file they can open in their browser. This is done by:

1. Storing the full report HTML (the entire `document.documentElement.outerHTML`) in a variable when the email preview opens.
2. The CTA button in the email template uses `href="#"` with `id="cta-download"`.
3. After writing the email preview, inject a script that wires the CTA button to create a Blob from the full report HTML and trigger a download via a temporary `<a>` element.

```html
<script>
const emailHTML = `[full email HTML here as a template literal]`;

function openEmailPreview() {
  // Capture the full report HTML before opening the preview
  const fullReportHTML = '<!DOCTYPE html>' + document.documentElement.outerHTML;
  const reportTitle = document.title.replace(/[^a-zA-Z0-9 ]/g, '').trim().replace(/\s+/g, '-');

  const win = window.open('', '_blank');
  win.document.write(emailHTML);
  win.document.close();
  setTimeout(() => {
    // Instruction bar
    const bar = win.document.createElement('div');
    bar.style.cssText = 'position:fixed;top:0;left:0;right:0;background:#2C1810;color:#FBF8F3;padding:10px 20px;font-family:Arial,sans-serif;font-size:12px;display:flex;justify-content:space-between;align-items:center;z-index:9999;box-sizing:border-box;gap:16px;user-select:none;-webkit-user-select:none;';
    bar.innerHTML = '<span style="flex:1"><strong>Gmail:</strong> Cmd+A &rarr; Cmd+C to select and copy, then paste into Gmail compose &nbsp;&middot;&nbsp; <em style="opacity:.75">For email platforms: use the button &rarr;</em></span>';
    const copyBtn = win.document.createElement('button');
    copyBtn.textContent = 'Copy HTML source';
    copyBtn.style.cssText = 'background:#C4765B;color:#FBF8F3;border:none;padding:6px 14px;cursor:pointer;font-size:12px;font-weight:600;letter-spacing:.04em;flex-shrink:0;';
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(emailHTML).catch(() => {});
      copyBtn.textContent = 'Copied!';
      setTimeout(() => copyBtn.textContent = 'Copy HTML source', 2000);
    };
    bar.appendChild(copyBtn);
    win.document.body.insertBefore(bar, win.document.body.firstChild);
    win.document.body.style.paddingTop = '44px';

    // Wire the CTA button to download the full report
    const cta = win.document.getElementById('cta-download');
    if (cta) {
      cta.addEventListener('click', function(e) {
        e.preventDefault();
        const blob = new Blob([fullReportHTML], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = win.document.createElement('a');
        a.href = url;
        a.download = reportTitle + '.html';
        a.click();
        URL.revokeObjectURL(url);
      });
    }
  }, 100);
}
</script>
```

In the email template, the CTA button should use:
```html
<a id="cta-download" href="#" style="display:inline-block;background:#C4765B;color:#FBF8F3;text-decoration:none;padding:14px 28px;font-size:14px;font-weight:bold;letter-spacing:.04em;cursor:pointer;">View full report →</a>
```

**Gmail workflow:** Click "Preview email" → new tab opens with rendered email → Cmd+A → Cmd+C → paste into Gmail compose. Gmail preserves the rendered HTML formatting when you paste selected content (not raw code). Note: the download button only works in the preview; in actual Gmail it will be a no-op link.

**ESP workflow:** Click "Preview email" → click "Copy HTML source" in the instruction bar → paste into Mailchimp/Beehiiv/etc. HTML editor. For ESP use, replace the `#` href in the CTA with your hosted report URL.

**Standalone sharing:** When someone receives the email and clicks "View full report →" from the preview, the full self-contained HTML report downloads to their machine. They open it in any browser to view the complete report with all photos and styles.

---

### Print / PDF styles

Add `@media print` rules so the PDF matches the screen design exactly — colors preserved, no mid-article page breaks, correct margins.

```css
@media print {
  .download-btn { display: none; }
  .email-btn { display: none; }
  body { font-size: 13px; }
  .wrap { padding: 0 0 40px; }
  .bar { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .theme-card { -webkit-print-color-adjust: exact; print-color-adjust: exact; break-inside: avoid; }
  .session { break-inside: avoid; }
  .talk-section { break-inside: avoid; }
  .action-item { -webkit-print-color-adjust: exact; print-color-adjust: exact; break-inside: avoid; }
  .speaker-card { -webkit-print-color-adjust: exact; print-color-adjust: exact; break-inside: avoid; }
  /* Collapse grid containers to block — Chrome ignores break-inside on grid children */
  .session-body, .booth-body, .section-body { display: block; }
  .research-panel { -webkit-print-color-adjust: exact; print-color-adjust: exact; width: 100%; margin-top: 16px; }
  .implications-panel { -webkit-print-color-adjust: exact; print-color-adjust: exact; width: 100%; margin-top: 16px; }
  .notes-list li::marker { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  /* Prevent orphaned headings */
  h2, h3, h4 { break-after: avoid; }
  /* Compact themes grid to 3 columns so it fits on one page */
  .themes-grid { grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .theme-card { padding: 14px 16px; }
  .theme-card p { font-size: 12px; }
  @page { size: A4 portrait; margin: 18mm 16mm; }
}
```

### Responsive
At `max-width: 640px`: session body and themes grid collapse to single column. At `max-width: 500px`: photo grids collapse to single column.

---

## Follow-ups to Offer

After generating both outputs (Markdown + HTML), offer:
- Expand any unit with more detail
- Deep-dive on a specific further reading entry
- Add photos to specific units
- Adjust tone (more formal / more casual)
- Add or remove sections

---

## Example Invocations

- "Here are my notes from the AI Summit yesterday, can you write them up?"
- "I walked around a trade show today, here are my notes on the companies I visited"
- "Write up my notes from the UX workshop this afternoon"
- "I visited a client site today, turn these observations into a report"
- "I attended a talk by [Speaker] — here are my notes, make them shareable"
- "Clean up these field notes and add context on everything mentioned"
