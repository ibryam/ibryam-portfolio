# Design System — ibryam.com

Single source of truth for every visual decision on the site, including the chat widget.
**Audience:** any implementing agent or human. Written so it can be followed mechanically — every value is exact; nothing is left to taste.

## Trigger Keywords
design, CSS, color, colour, font, typography, spacing, layout, component, button, card, token, redesign, style, theme, icon.

## Non-negotiable rules

1. **Never write a raw color, size, shadow, duration, or radius in a CSS rule.** Always reference a token (`var(--…)`). If a needed token doesn't exist, add it to `:root` first, then use it.
2. **Never introduce a new font, color hue, or icon style.** The palette and fonts below are closed sets.
3. **Every interactive element** (link, button, pill, input, icon button) **must have all four states styled:** default, `:hover`, `:focus-visible`, `:active`. Disabled where applicable.
4. **All motion must respect `prefers-reduced-motion`** (the global guard in §7 handles this — do not remove it, do not add animations outside its reach).
5. **Animate only `opacity` and `transform`.** Never animate `width`, `height`, `top`, `left`, `margin`, or anything that triggers layout.
6. **No emoji as UI.** Icons are inline SVG from the set in §8 only.
7. Contrast: body-size text ≥ 4.5:1 against its background; text below 16px must use `--text-primary` or `--text-secondary`, never `--text-muted` (muted is reserved for ≥ 14px supporting text on `--bg-base`/`--bg-surface`).

---

## 1. Color tokens

Drop-in replacement for the current `:root`. Old names are kept as aliases during migration (delete the alias block once `grep -E '\-\-(navy|teal|gold|muted)\b'` finds no usages outside `:root`).

```css
:root {
  /* ── Backgrounds (darkest → lightest) ── */
  --bg-base:      #16233E;  /* page background (slightly deeper than old navy for layer contrast) */
  --bg-surface:   #1B2A4A;  /* alternating sections, stats bar          (old --navy) */
  --bg-raised:    #20315A;  /* cards, skill groups                      (≈ old --navy-light) */
  --bg-overlay:   #0F1E38;  /* chat panel, viz containers, nav scrim    */
  --bg-inset:     #243A66;  /* input fields, bot bubbles, highlights    (≈ old #1a2f52) */

  /* ── Text ── */
  --text-primary:   #F2F5FA;  /* headings, emphasized values            */
  --text-secondary: #C7D2E4;  /* body copy                              */
  --text-muted:     #8FA3C0;  /* labels, captions ≥14px only            */
  --text-inverse:   #16233E;  /* text on teal/gold fills                */

  /* ── Brand ── */
  --brand:        #2EC4A6;  /* teal — primary actions, links, accents   */
  --brand-strong: #4FE3C4;  /* hover/active teal, gradients             */
  --brand-dim:    #1E8A75;  /* pressed state                            */
  --accent-gold:  #E8A838;  /* user chat bubbles, secondary highlight   */
  --accent-purple:#9B72CF;  /* SMI project accent                       */
  --accent-blue:  #5B9BD5;  /* reserved third accent                    */

  /* ── Semantic ── */
  --success: #3DD68C;
  --warning: #E8A838;
  --danger:  #F0647A;

  /* ── Lines & tints ── */
  --border-subtle: rgba(143,163,192,0.14);  /* hairlines, dividers      */
  --border-brand:  rgba(46,196,166,0.28);   /* brand-tinted borders     (old --border, nudged up for contrast) */
  --tint-brand-08: rgba(46,196,166,0.08);
  --tint-brand-14: rgba(46,196,166,0.14);
  --tint-white-04: rgba(255,255,255,0.04);
  --tint-white-08: rgba(255,255,255,0.08);

  /* ── Migration aliases (TEMPORARY — delete after Phase 1.3) ── */
  --navy: var(--bg-surface); --navy-light: var(--bg-raised); --navy-card: var(--bg-raised);
  --teal: var(--brand); --gold: var(--accent-gold); --purple: var(--accent-purple);
  --blue: var(--accent-blue); --text: var(--text-secondary); --muted: var(--text-muted);
  --border: var(--border-brand);
}
```

**Usage map (memorize, don't improvise):**

| Surface | Background | Default text |
|---|---|---|
| Page / hero | `--bg-base` | `--text-secondary` |
| Alternating sections, stats | `--bg-surface` | `--text-secondary` |
| Cards, skill groups, about card | `--bg-raised` | `--text-secondary` |
| Chat panel, nav bar, viz frame | `--bg-overlay` | `--text-secondary` |
| Inputs, bot bubbles, highlight chips | `--bg-inset` | `--text-primary` |
| Primary button / user bubble | `--brand` / `--accent-gold` | `--text-inverse` |

## 2. Typography

```css
:root {
  --font-display: "Space Grotesk", "Segoe UI", sans-serif;  /* h1–h3, stat numbers, nav name */
  --font-body:    "Inter", -apple-system, "Segoe UI", sans-serif;  /* everything else */

  /* Fluid scale — ratio ≈1.25 desktop, compressed on mobile via clamp */
  --fs-display: clamp(2.4rem, 5.5vw, 3.6rem);   /* hero h1            */
  --fs-h2:      clamp(1.7rem, 3vw, 2.25rem);    /* section titles     */
  --fs-h3:      1.35rem;                         /* card titles        */
  --fs-lg:      1.125rem;                        /* hero sub, lead     */
  --fs-base:    1rem;                            /* body               */
  --fs-sm:      0.875rem;                        /* secondary body, chat text */
  --fs-xs:      0.8125rem;                       /* badges, labels — NEVER smaller with --text-muted */
  --fs-2xs:     0.75rem;                         /* uppercase eyebrows; pair with --text-secondary + letter-spacing */

  --lh-tight: 1.15;  /* display headings */
  --lh-snug:  1.4;   /* h2/h3, buttons   */
  --lh-body:  1.65;  /* paragraphs       */

  --ls-wide: 0.08em; /* uppercase labels */
}
```

Font loading (in `<head>`, before the `<style>` block):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
```

Rules: headings (`h1,h2,h3,.stat-num,.nav-name,.project-title`) use `--font-display` weight 700 (600 for h3). Body weight 400; emphasized inline text 600 (`<strong>`), never 700 in body. Uppercase eyebrow labels (`.section-label`, `.skill-group-title`, `.about-card-title`, `.stat-label`): `--fs-2xs` + `--ls-wide` + weight 600. Numbers in stats/highlights: `font-feature-settings: "tnum"` (tabular).

## 3. Spacing — 4px scale

```css
:root {
  --sp-1: 0.25rem; --sp-2: 0.5rem; --sp-3: 0.75rem; --sp-4: 1rem;
  --sp-5: 1.5rem;  --sp-6: 2rem;   --sp-7: 3rem;    --sp-8: 4rem;
  --sp-9: 6rem;
}
```
Layout constants: section vertical padding `--sp-9` desktop / `--sp-8` mobile; `.section-inner` max-width **1040px**, horizontal padding `--sp-6` desktop / `--sp-4` mobile; gap between section header block and content `--sp-7`; card internal padding `--sp-6`; grid gaps `--sp-5`. When a needed value falls between steps, pick the **smaller** step.

## 4. Radii

```css
:root { --r-sm: 6px; --r-md: 10px; --r-lg: 16px; --r-full: 999px; }
```
sm = badges-with-corners, small controls · md = buttons, inputs, chat bubbles, highlights · lg = cards, chat panel, viz frame · full = pills, toggle FAB, tags.

## 5. Elevation & effects

```css
:root {
  --shadow-1: 0 2px 8px rgba(8,15,30,0.35);
  --shadow-2: 0 8px 28px rgba(8,15,30,0.45);
  --shadow-3: 0 16px 48px rgba(8,15,30,0.55);
  --glow-brand: 0 4px 24px rgba(46,196,166,0.35);
}
```
Cards at rest: no shadow (border only). Card hover: `--shadow-2` + `translateY(-3px)` + border `--border-brand`. Chat panel & open mobile menu: `--shadow-3`. Chat FAB: `--glow-brand`. Never invent new shadows.

## 6. Motion

```css
:root {
  --ease: cubic-bezier(0.2, 0, 0, 1);
  --t-fast: 150ms;   /* hovers, color/opacity changes      */
  --t-med:  250ms;   /* panel open/close, menu, transforms */
  --t-slow: 400ms;   /* scroll reveals, hero entrance      */
}
```
Standard transition: `transition: <props> var(--t-fast) var(--ease);`. Scroll reveals: `opacity 0→1` + `translateY(16px)→0` over `--t-slow`, triggered once via IntersectionObserver at `threshold: 0.15`.

## 7. Global baseline (paste verbatim near the top of the stylesheet)

```css
:focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
  border-radius: var(--r-sm);
}
::selection { background: var(--tint-brand-14); color: var(--text-primary); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## 8. Iconography

Inline SVG only. Stroke style: `fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`, `viewBox="0 0 24 24"`, default size 20×20 (chat FAB icon 26×26). Color via `currentColor` — never hardcode stroke colors.

Closed set (Lucide outlines): `message-circle` (chat FAB/nav), `send` (chat send), `x` (close), `external-link`, `arrow-down` (scroll cue), `file-text` (CV / JD), `github`, `linkedin`, `mail`, `play` (viz facade), `menu` (hamburger), `thumbs-up`, `thumbs-down`, `rotate-ccw` (retry/clear).
Add `aria-hidden="true"` on every decorative SVG; the accessible name lives on the parent button (`aria-label`).

## 9. Component specs

### Buttons (`.btn`)
Base: `font-family: var(--font-body); font-weight: 600; font-size: var(--fs-sm); line-height: var(--lh-snug); padding: var(--sp-3) var(--sp-5); border-radius: var(--r-md); display: inline-flex; align-items: center; gap: var(--sp-2); cursor: pointer; transition: background var(--t-fast) var(--ease), border-color var(--t-fast) var(--ease), color var(--t-fast) var(--ease), transform var(--t-fast) var(--ease);`

| Variant | Default | Hover | Active |
|---|---|---|---|
| `.btn-primary` | bg `--brand`, text `--text-inverse` | bg `--brand-strong`, `translateY(-1px)` | bg `--brand-dim`, translateY(0) |
| `.btn-secondary` | transparent, border 1px `--border-brand`, text `--text-primary` | border `--brand`, text `--brand` | bg `--tint-brand-08` |
| `.btn-ghost` | transparent, text `--text-muted` | text `--brand` | text `--brand-dim` |

There is **no gold button**. The old `.btn-gold` becomes `.btn-primary` (gold is reserved for user chat bubbles and warning accents). Disabled: `opacity: 0.5; cursor: not-allowed;` no hover transform.

### Pills / tags (`.hero-pill`, `.tech-badge`, `.about-tag`, `.chat-suggestion`)
`border-radius: var(--r-full); font-size: var(--fs-xs); padding: var(--sp-1) var(--sp-3);`
Neutral: bg `--tint-white-04`, border 1px `--border-subtle`, text `--text-muted`.
Brand (active/clickable): bg `--tint-brand-08`, border `--border-brand`, text `--brand`; hover bg `--tint-brand-14`. Clickable pills must be `<button>` elements.

### Cards (`.project-card`, `.skill-group`, `.about-card`)
bg `--bg-raised`, border 1px `--border-subtle`, radius `--r-lg`, padding `--sp-6`. Project cards keep the 3px top accent bar (`--accent` custom prop per card). Hover (only cards that are wholly or partly interactive): border `--border-brand`, `--shadow-2`, `translateY(-3px)`.

### Inputs (`#chat-input`)
bg `--bg-inset`, border 1px `--border-subtle`, radius `--r-md`, padding `--sp-2` `--sp-3`, font `--font-body` `--fs-sm`, text `--text-primary`, placeholder `--text-muted`. Focus: border `--brand` (plus global focus ring suppressed via `outline: none` ONLY here because the border change provides the indicator — document any other exception).

### Chat widget
- FAB: 56px circle, bg `--brand`, icon `--text-inverse`, `--glow-brand`; hover scale 1.06.
- Panel: 380×min(560px, calc(100dvh - 7rem)); bg `--bg-overlay`; border `--border-subtle`; radius `--r-lg`; `--shadow-3`. Below 700px: full-screen sheet — `inset: 0; width: 100%; height: 100dvh; border-radius: 0;` with `padding-bottom: env(safe-area-inset-bottom)`.
- Header: bg `--bg-raised` (NOT teal fill — calmer, lets content lead), 1px bottom border `--border-subtle`; name `--text-primary` 600; status line `--fs-xs` `--text-muted` with a 6px `--success` dot.
- Bot bubble: bg `--bg-inset`, text `--text-primary`, radius `--r-md` with 4px bottom-left corner, max-width 88%.
- User bubble: bg `--accent-gold`, text `--text-inverse`, radius `--r-md` with 4px bottom-right corner.
- Typing indicator: three 6px dots `--text-muted`, bounce 1.2s.
- Feedback thumbs: 16px ghost icon buttons under each bot bubble, `--text-muted` → hover `--brand`/`--danger`; selected state filled.

### Nav
Height 64px; bg `rgba(15,30,56,0.85)` + `backdrop-filter: blur(12px)`; bottom border `--border-subtle`. Active section link: text `--brand` + 2px bottom underline offset 4px. Mobile (<700px): hamburger (`menu` icon, 44×44 tap target) toggles full-width dropdown panel under the bar — bg `--bg-overlay`, `--shadow-3`, links stacked with `--sp-4` padding, slides/fades in `--t-med`.

### Stats bar
bg `--bg-surface`, hairline top/bottom `--border-subtle`. Numbers: `--font-display` 700, `--fs-h3` size, `--brand`, tabular figures. Labels: eyebrow style (§2).

### Timeline
Line: 2px `--border-subtle`. Dots: 10px, `--brand` fill, 3px ring of `--bg-surface`; education dots `--text-muted`. Current-role dot gets a soft pulse halo (2.5s, `--tint-brand-14`), removed under reduced motion.

## 10. Breakpoints

```
≥ 1100px  desktop     (default styles)
700–1099  tablet      (about-grid stays 2-col until 800px)
< 700px   mobile      (hamburger nav, single-column grids, full-screen chat)
< 400px   small phone (hero CTAs stack vertically, full-width)
```
Use `max-width` queries at exactly `1099px`, `699px`, `399px`.

## 11. Definition of done for any visual change

1. No raw values — grep check from todo 1.1 passes.
2. All four interaction states present.
3. Keyboard: element reachable and operable; focus visible.
4. Reduced-motion verified in DevTools emulation.
5. Checked at 360px, 768px, 1280px widths.
6. No console errors; no layout shift introduced (CLS check in Lighthouse).
