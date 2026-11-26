# UX Overhaul Playbook — frontend/index.html

Step-by-step execution guide for Phases 1–2 of `tasks/roadmap.md`.
**Written for a literal-minded executor.** Follow steps in order. After every step, run its **Verify** block. If Verify fails, fix before continuing — never proceed on a broken step. Never do anything not listed here; if a step looks wrong, stop and report instead of improvising.

**Prerequisites:** Phase 0 of `tasks/todo.md` is complete. You have read `.claude/skills/design-system/SKILL.md` (referred to below as **DS**) in full. All token names, component states, breakpoints and icon rules come from DS — this file never overrides DS.

**Global constraints:**
- The only file you edit is `frontend/index.html` unless a step names another file.
- The page must remain a single HTML file with inline CSS/JS. No build step, no npm, no frameworks.
- After each step, open the file in a browser (`start frontend/index.html` on Windows) and check the Verify items manually, plus: zero console errors.
- Commit after each completed step with message `feat(ui): <step title>` — one step, one commit.

---

## Step 1 — Install the token system (todo 1.1–1.3)

1. In `<head>`, add the three font `<link>` tags exactly as given in DS §2, ABOVE the `<style>` tag.
2. Replace the entire current `:root { … }` block with the DS §1 color tokens **plus** DS §2 typography tokens, DS §3 spacing, DS §4 radii, DS §5 shadows, DS §6 motion — one consolidated `:root`. Keep the migration aliases at the bottom of `:root`.
3. Set `body { font-family: var(--font-body); color: var(--text-secondary); background: var(--bg-base); }`. Add a `h1, h2, h3 { font-family: var(--font-display); color: var(--text-primary); }` rule.
4. Now migrate hardcoded values. Work through the stylesheet **top to bottom**; for each raw value, replace per this table (and the DS §1 usage map):
   - `#26b395` → `var(--brand-strong)` (it was a hover darken; DS hovers go lighter — this is intentional)
   - `#d4942e` → delete along with `.btn-gold` (Step 5 removes the gold button)
   - `#0f1e38` → `var(--bg-overlay)` · `#1a2f52` → `var(--bg-inset)` · `#0d1b33` → `var(--bg-overlay)`
   - `rgba(46,196,166,0.07|0.08|0.1|0.12)` → `var(--tint-brand-08)` · `(0.15|0.16|0.2)` → `var(--tint-brand-14)` · `(0.25|0.3|0.35|0.4)` → `var(--border-brand)`
   - `rgba(255,255,255,0.04|0.05|0.06)` → `var(--tint-white-04)` · `(0.1)` → `var(--tint-white-08)`
   - `rgba(27,42,74,0.95)` (nav) → handled in Step 6; leave for now
   - shadows on `#chat-toggle`, `#chat-panel` → `var(--glow-brand)`, `var(--shadow-3)`
   - transition durations `0.15s/0.2s/0.22s` → `var(--t-fast)` (0.15/0.2) and `var(--t-med)` (0.22), easing `var(--ease)`
5. Delete the migration alias block from `:root`, then fix every remaining `var(--navy…)`/`var(--teal)`/`var(--gold)`/`var(--muted)`/`var(--text)`/`var(--border)` reference to its new token name.
6. Paste the DS §7 global baseline (focus-visible, ::selection, reduced-motion) immediately after the `:root` block.

**Verify:**
- `grep -E '#[0-9a-fA-F]{3,8}' frontend/index.html` matches only: lines inside `:root`, the favicon data-URI line, and SVG `fill=` inside the favicon. Nothing else.
- `grep -cE 'var\(--(navy|teal|gold|muted|border)\)' frontend/index.html` → 0.
- Page loads: headings in Space Grotesk, body in Inter, layout intact, Tab shows teal focus rings.

## Step 2 — SEO head + structured data (todo 2.1)

Insert into `<head>` after `<title>`:

```html
<meta name="description" content="Ibryam Faik — Data & AI Engineer in Geneva. BigQuery, dbt, Tableau and Python pipelines, plus production LLM agents. Open to roles across the DACH region.">
<link rel="canonical" href="https://www.ibryam.com/">
<meta name="theme-color" content="#16233E">
<meta property="og:type" content="website">
<meta property="og:url" content="https://www.ibryam.com/">
<meta property="og:title" content="Ibryam Faik — Data & AI Engineer">
<meta property="og:description" content="5+ years turning data into decisions. Automated pipelines, live dashboards, and an AI agent that answers recruiter questions on this site.">
<meta property="og:image" content="https://www.ibryam.com/assets/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Ibryam Faik — Data & AI Engineer">
<meta name="twitter:description" content="BigQuery · dbt · Tableau · Python · LLM agents. Portfolio with live dashboards and an AI career assistant.">
<meta name="twitter:image" content="https://www.ibryam.com/assets/og-image.png">
```

Before `</head>`, add JSON-LD:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Ibryam Faik",
  "jobTitle": "Data & AI Engineer",
  "url": "https://www.ibryam.com",
  "email": "mailto:ibryamfibryam@gmail.com",
  "sameAs": [
    "https://www.linkedin.com/in/ibryam",
    "https://github.com/ibryam",
    "https://public.tableau.com/app/profile/ibryam"
  ],
  "knowsAbout": ["BigQuery", "dbt", "Tableau", "Python", "SQL", "Data Engineering", "LLM Agents", "RAG"],
  "worksFor": { "@type": "Organization", "name": "UKG" },
  "knowsLanguage": ["en", "bg", "tr", "de", "ru"]
}
</script>
```

⚠️ Before committing: confirm the LinkedIn/GitHub handles match the footer links already in the file. If they differ, use the footer's values everywhere.

**Verify:** paste the JSON-LD into https://validator.schema.org → zero errors. View source: exactly one canonical, one description.

## Step 3 — robots, sitemap, OG image (todo 2.2)

1. Create `frontend/robots.txt`:
   ```
   User-agent: *
   Allow: /
   Sitemap: https://www.ibryam.com/sitemap.xml
   ```
2. Create `frontend/sitemap.xml`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
     <url><loc>https://www.ibryam.com/</loc><changefreq>monthly</changefreq></url>
   </urlset>
   ```
3. Create `frontend/assets/` and generate `og-image.png` (1200×630): bg `#16233E`, name in Space Grotesk 700 white, "Data & AI Engineer" in teal `#2EC4A6`, the four bar shapes from the favicon bottom-right. If you cannot generate an image, create `frontend/assets/README.md` saying "TODO: og-image.png 1200×630 per ux-overhaul Step 3" and note it in tasks/todo.md — do NOT silently skip.

**Verify:** files exist; `og:image` URL path matches the actual filename.

## Step 4 — Accessibility pass (todo 2.3)

1. First element inside `<body>`: `<a class="skip-link" href="#main">Skip to content</a>`. CSS: visually hidden off-screen (`position:absolute; top:-48px; left:var(--sp-4); z-index:200; background:var(--brand); color:var(--text-inverse); padding:var(--sp-2) var(--sp-4); border-radius:var(--r-md);`) with `.skip-link:focus { top: var(--sp-2); }`.
2. Wrap everything between `</nav>` and `<footer>` in `<main id="main">`. Note: `section { padding … }` styles must keep applying — they target `section`, so wrapping is safe.
3. Chat toggle button: add `aria-expanded="false"` (JS must flip it in `toggleChat()`), `aria-controls="chat-panel"`, `aria-label="Ask AI about Ibryam"`.
4. Chat panel: `role="dialog"` `aria-label="AI chat about Ibryam"`. Messages container: `role="log"` `aria-live="polite"`.
5. Convert every `.chat-suggestion` from `<span>` to `<button type="button" class="chat-suggestion">` (CSS already restyled in Step 1; ensure `font-family: inherit; cursor: pointer;`).
6. Add to the script: `document.addEventListener('keydown', e => { if (e.key === 'Escape' && isOpen) { toggleChat(); document.getElementById('chat-toggle').focus(); } });` and in `toggleChat()` set `toggle.setAttribute('aria-expanded', String(isOpen))`.
7. Contrast: per DS rule 7, find every element styled `--text-muted` with font-size < 0.875rem (`.highlight-label` 0.78rem, `.chat-header-sub` 0.75rem, `.stat-label` 0.8rem, `.tl-years` 0.8rem, tech badges 0.78rem) and either raise the size to `var(--fs-xs)` or switch color to `--text-secondary`. Eyebrow labels (uppercase) switch to `--text-secondary`.
8. All `target="_blank"` links get `rel="noopener"`.

**Verify:** keyboard-only: Tab from page top → skip link appears first → can open chat, type, send, Escape closes and focus returns to the FAB. Lighthouse Accessibility ≥ 95.

## Step 5 — Hero + CTA hierarchy (todo 2.5)

1. CTA row becomes exactly three buttons in this order (DS §9 button specs):
   - `<button class="btn btn-primary" onclick="toggleChat()">` + chat SVG icon + `Ask my AI anything`
   - `<a href="#projects" class="btn btn-secondary">View projects</a>`
   - `<a class="btn btn-ghost" href="<existing CV link or assets/Ibryam_Faik_CV.pdf>" download>` + file-text icon + `Download CV` *(if the PDF doesn't exist yet, point at `#` with `title="CV coming soon"` and record in todo 2.8)*
2. Delete `.btn-gold` CSS and any remaining usage. Move the LinkedIn link out of the CTA row — it already lives in nav-less footer; instead add small ghost icon links (linkedin, github, mail SVGs, 20px, `--text-muted` → hover `--brand`) directly under the CTA row with `aria-label`s.
3. Hero sub-copy, replace verbatim with:
   > 5+ years turning complex data into decisions — automated pipelines, live dashboards, and LLM-powered tools. This site includes my AI assistant: ask it anything a recruiter would ask me.
4. Scroll cue: bottom-center of hero, `arrow-down` SVG inside a ghost link to `#projects`, `aria-label="Scroll to projects"`, gentle 2s float animation (translateY ±4px) — inside the reduced-motion guard's reach.
5. Entrance: hero children get `animation: heroIn var(--t-slow) var(--ease) both;` staggered `animation-delay` 0/60/120/180ms, where `heroIn` = `from { opacity: 0; transform: translateY(12px); }`. No delay on the logos row > 240ms.

**Verify:** exactly one visually dominant CTA; no gold button anywhere; reduced-motion emulation shows no animation; CLS in Lighthouse = 0.

## Step 6 — Mobile hamburger nav (todo 2.4)

1. Nav bar: update bg to `rgba(15,30,56,0.85)` + `backdrop-filter: blur(12px)`, height 64px, border-bottom `--border-subtle` (per DS §9 Nav).
2. Add inside `<nav>`, after the links: `<button id="nav-burger" aria-label="Open menu" aria-expanded="false" aria-controls="nav-menu">` containing the `menu` SVG. CSS: hidden ≥ 700px; below 700px shown as 44×44 flex-centered ghost button, and `.nav-links` stays `display:none`.
3. Add after `</nav>`: `<div id="nav-menu" hidden>` containing the same four links + an "Ask AI" button. CSS: `position: fixed; top: 64px; left: 0; right: 0; z-index: 99; background: var(--bg-overlay); box-shadow: var(--shadow-3); border-bottom: 1px solid var(--border-subtle); padding: var(--sp-4) var(--sp-6);` links stacked, `padding: var(--sp-3) 0`, font-size `--fs-base`. Open/close = toggle `hidden` + a `.open` class animating `opacity` and `translateY(-8px)→0` over `--t-med`.
4. JS: burger click toggles; every link inside closes the menu; Escape closes it; opening the chat closes it.

**Verify:** at 360px width — burger visible, opens menu, all 4 links navigate and close menu, Escape closes, `aria-expanded` flips. At 1280px — burger hidden, links row unchanged.

## Step 7 — Tableau click-to-load facades (todo 2.6)

For each viz (`swiss`, `smi`):

1. Capture a screenshot of the live dashboard at its native size; save as `frontend/assets/preview-swiss.png` and `preview-smi.png` (compress < 200KB each, use 1200px wide max). If you cannot capture, use a solid `--bg-overlay` block with the project title — but record it as a TODO like Step 3.
2. Replace the iframe inside each `.viz-scaler` with:
   ```html
   <button class="viz-facade" data-viz="swiss" aria-label="Load interactive Swiss Macro Monitor dashboard">
     <img src="assets/preview-swiss.png" alt="" width="1200" height="868" loading="lazy">
     <span class="viz-facade-btn"><svg ……play icon…></svg> Load interactive dashboard</span>
   </button>
   ```
   Keep the existing `data-w`/`data-h` on the scaler (added in todo 0.1).
3. CSS: `.viz-facade { position:relative; display:block; width:100%; padding:0; border:0; background:none; cursor:pointer; }` image full-width height auto; `.viz-facade-btn` = pill centered absolutely, `--bg-overlay` at 92% opacity, border `--border-brand`, text `--brand`, `--fs-sm` 600, play icon 18px; hover bg `--tint-brand-14`.
4. JS: store iframe URLs in one object keyed by viz id:
   ```js
   var VIZ_SRC = {
     swiss: 'https://public.tableau.com/views/SwissMacroMonitor/Overview?:showVizHome=no&:embed=true&:tabs=yes&:toolbar=bottom&:animate_transition=yes&:display_count=yes&:language=en-US',
     smi:   'https://public.tableau.com/views/SMIRiskMonitor/Performance?:showVizHome=no&:embed=true&:tabs=yes&:toolbar=bottom&:animate_transition=yes&:display_count=yes&:language=en-US'
   };
   ```
   On facade click: read the scaler's `data-w`/`data-h`, create `<iframe src=… width=data-w height=data-h frameborder="0" loading="lazy" allowfullscreen>`, replace the facade with it, call `scaleAll()`.
5. `scaleAll()` must already read `data-w`/`data-h` (todo 0.1) — confirm; if not, do todo 0.1 now.

**Verify:** fresh load with DevTools Network open → zero requests to `public.tableau.com`. Click each facade → dashboard loads, fills container width at 1280px and 375px, full height visible. Lighthouse mobile Performance ≥ 90.

## Step 8 — Scroll-spy + section reveal (todo 2.7)

1. Add `.nav-links a.active { color: var(--brand); }` plus the DS underline (2px, offset 4px — use `text-underline-offset` + `text-decoration`).
2. JS IntersectionObserver #1 (spy): observe the four sections with `rootMargin: '-40% 0px -55% 0px'`; on intersect, set `.active` on the matching nav link, remove from others.
3. JS IntersectionObserver #2 (reveal): add class `reveal` in markup to each `section .section-inner`, the stats bar inner, and each `.project-card`. CSS: `.reveal { opacity: 0; transform: translateY(16px); transition: opacity var(--t-slow) var(--ease), transform var(--t-slow) var(--ease); } .reveal.in { opacity: 1; transform: none; }`. Observer at `threshold: 0.15`, `observer.unobserve(el)` after adding `.in`.
   ⚠️ Guard: `if (matchMedia('(prefers-reduced-motion: reduce)').matches)` → add `.in` to everything immediately and skip the observer.
4. Hero is NOT a reveal target (it has its own entrance from Step 5).

**Verify:** scroll down — nav highlights Projects → Skills → About → Experience in order; sections fade up exactly once; scroll back up — nothing re-animates; reduced-motion emulation — everything visible instantly.

## Step 9 — Footer + privacy note (todo 2.9, 2.8 footer half)

1. Footer links become icon+text pairs (SVG set), add "Download CV" with `file-text` icon.
2. Below `.footer-copy`, add:
   ```html
   <p class="footer-privacy">Chat conversations and approximate visitor location (country/city) are stored to improve this site and follow up on questions. Email me to have yours removed.</p>
   ```
   Style: `--fs-xs`, `--text-muted`, max-width 560px, centered, margin-top `--sp-3`.

**Verify:** visible and readable at 360px and 1280px.

## Step 10 — Final gate (todo 2.10)

1. Run Lighthouse (mobile, simulated throttling) against the deployed preview URL.
2. Targets: Performance ≥ 90 · Accessibility ≥ 95 · Best Practices ≥ 95 · SEO ≥ 95.
3. Record all four scores + date in `tasks/todo.md` → Review Notes.
4. If any score misses: the top three Lighthouse opportunities, in order, are your fix list. Re-run. Do not declare Phase 2 done below targets without flagging it to Ibryam.

**Common misses and their one-line fixes:**
- Perf: preview PNGs too large → recompress ≤ 200KB; fonts blocking → confirm `display=swap`.
- A11y: contrast on muted small text → re-apply Step 4.7; missing button names → `aria-label` on icon-only buttons.
- SEO: missing description (Step 2 skipped?) or non-crawlable links.
