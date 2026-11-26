# ibryam.com — Product Roadmap

**Last updated:** 2026-06-12
**Owner:** Ibryam Faik
**Goal:** A 10/10 recruiter-facing portfolio — visually distinctive, fast, accessible, and an AI chatbot that feels like a premium product, not a demo.

How to read this document:
- Phases are ordered by dependency, not just priority. Phase 1 (design tokens) must land before Phase 2 (UI overhaul) because every Phase 2 step references token names.
- Each phase lists its **exit criteria** — the phase is not done until every criterion is verifiably true.
- Detailed step-by-step execution instructions live in `.claude/skills/` (see "Execution playbooks" at the bottom). This file is the *what and why*; the skills are the *how*.
- The master checklist with per-task acceptance criteria is `tasks/todo.md`.

---

## Guiding decisions (already made — do not re-litigate)

These decisions were made deliberately. An implementing agent must follow them, not revisit them.

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Keep the dark navy + teal identity; refine it, don't replace it | It is distinctive, recruiter-appropriate, and matches the existing Tableau dashboards embedded on the page |
| D2 | Stay single-file `frontend/index.html` (inline CSS/JS, no build step) | Cloudflare Pages deploys it as-is; a bundler adds maintenance cost with no user-visible benefit at this size |
| D3 | Typography: Space Grotesk (headings) + Inter (body), loaded from Google Fonts with `font-display: swap` | System fonts have no identity; these two are free, fast, and read "modern data/tech" |
| D4 | Replace all emoji icons (💬 ➤ ✕ 📋) with inline SVG | Emoji render differently per OS and look unpolished next to a refined design |
| D5 | Tableau embeds become click-to-load facades (static preview + play button) | Two eager Tableau iframes are the single biggest performance problem on the page |
| D6 | Chatbot gets SSE streaming; non-streaming `/chat` stays as fallback | Perceived latency is the #1 chat UX complaint; streaming fixes it without changing the agent |
| D7 | Keep `gpt-4o-mini` as the agent model for now | It's cheap, supports streaming + tools; model upgrades are a config change (`AGENT_MODEL`), not a roadmap item |
| D8 | Evaluator stays async/log-only, but REJECTED verdicts now notify via Telegram | Blocking the user on a second LLM round-trip is worse UX than occasionally shipping an imperfect answer |
| D9 | Personal branding: hero/page title says "Data & AI Engineer"; factual employment says "Senior Data Analyst at UKG" | Branding describes the target role; facts must stay accurate for recruiters who verify |
| D10 | Admin endpoints get a shared-secret header (`X-Admin-Token`), not full auth | Single-user admin surface; a token is proportionate |
| D11 | No light mode | One excellent theme beats two mediocre ones; the brand is dark |

---

## Phase 0 — Hygiene & bug fixes  *(smallest effort, do first)*

Fix what is broken or wrong before building anything new. No visual changes in this phase.

**Scope:**
1. Fix SMI viz scaling mismatch — JS `VIZZES` uses `h:967` but the iframe/scaler is 1167px tall, so the container clips ~200px of the dashboard.
2. Fix Swiss viz height off-by-one (`867` vs `868`) — read heights from `data-w`/`data-h` attributes instead of duplicating numbers in JS.
3. Re-remove the empty-RAG auto-flag: `agent.py:143` still contains `not rag_chunks or …` although commit `6e60af2` claimed to remove it — every question with no RAG hits silently files an "unknown question".
4. Trim the `_UNCERTAINTY` phrase list — `"that information"` / `"this information"` false-positive on normal sentences ("happy to share that information!").
5. `get_recent_history` orders by `ts` (second granularity) — same-second messages can reorder. Order by `id`.
6. Escape FTS5 queries in `search_faq` — special characters (`"`, `-`, `(`) currently raise `sqlite3.OperationalError`.
7. Add `backend/server.log`, `backend/server_err.log` to `.gitignore`.
8. Update `CLAUDE.md` to match reality: agent = OpenAI `gpt-4o-mini`, evaluator = Gemini 2.0 Flash with Groq fallback (async, log-only), notifications = Telegram (not Pushover), env vars list.
9. Decide fate of the uncommitted nav-order change in `frontend/index.html` (About before Experience) — commit it.

**Exit criteria:** both Tableau embeds render full-height at every viewport width; asking an off-profile question logs exactly one unknown-question only when the model actually can't answer; `search_faq('what is your "salary"?')` returns instead of raising; CLAUDE.md matches the code.

---

## Phase 1 — Design system foundation

Establish tokens and primitives so every later change references a single source of truth. Spec: `.claude/skills/design-system/SKILL.md`.

**Scope:**
1. Full CSS custom-property token set: color scale (bg/surface/raised + text hierarchy + brand + semantic), 4px spacing scale, fluid type scale, radii, shadows/elevations, motion durations + easing.
2. Load Space Grotesk + Inter (preconnect + swap).
3. Replace every hardcoded color/size in existing CSS with tokens (notably hover colors `#26b395`, `#d4942e`, ad-hoc rgba values).
4. Global focus-visible style, `::selection` style, `prefers-reduced-motion` guard.
5. Inline SVG icon set (chat, send, close, external-link, arrow, document, github, linkedin, mail, play).

**Exit criteria:** zero raw hex colors outside the `:root` block (verify with grep); page is visually near-identical to before except typography; keyboard Tab shows a visible focus ring on every interactive element.

---

## Phase 2 — Page UX overhaul

The visible redesign. Playbook: `.claude/skills/ux-overhaul/SKILL.md`.

**Scope:**
1. **SEO/meta:** description, Open Graph, Twitter card, canonical, JSON-LD `Person` schema, `robots.txt`, `sitemap.xml`, real OG image.
2. **Accessibility:** skip link, landmark roles, aria on chat widget (`aria-expanded`, `role="log"`, `aria-live="polite"`), suggestion pills become `<button>`, Escape closes chat, focus management, WCAG AA contrast audit of muted text sizes.
3. **Mobile nav:** hamburger menu below 700px (links currently just vanish).
4. **Hero:** tighter copy, primary CTA hierarchy (one primary action), scroll cue, refined pill/logo rows, subtle entrance animation (reduced-motion-safe).
5. **Tableau facades:** static preview image + "Load interactive dashboard" play button; iframe injected only on click (`loading="lazy"` as a safety net).
6. **Section polish:** scroll-spy active nav state, consistent section rhythm via spacing tokens, scroll-reveal (IntersectionObserver, opacity/translate only), card hover refinement.
7. **Recruiter CTAs:** "Download CV (PDF)" button in hero + footer; email copy-to-clipboard.
8. **Footer:** privacy note disclosing chat conversations + visit geolocation storage.

**Exit criteria:** Lighthouse (mobile, throttled): Performance ≥ 90, Accessibility ≥ 95, SEO ≥ 95; page is fully navigable with keyboard only; mobile nav works at 360px; Tableau iframes do not load before user interaction.

---

## Phase 3 — Chatbot UX upgrade

Make the chat feel like a product. Playbook: `.claude/skills/chatbot-upgrade/SKILL.md`.

**Scope:**
1. **SSE streaming:** new `POST /chat/stream` (FastAPI `StreamingResponse`), token-by-token render in the widget; fall back to `/chat` on stream failure.
2. **Markdown rendering:** safe mini-renderer supporting headings, bold/italic, bullet/numbered lists, links (`rel="noopener nofollow"`, https only) — the JD-match analysis already outputs structured markdown that currently renders as flat text.
3. **Session persistence:** `session_id` + transcript in `localStorage`; restore on reopen; "Clear conversation" action.
4. **Contextual suggestions:** initial pills persist as a re-suggestible row; after a JD match, offer follow-ups ("What about his German level?", "Contact Ibryam").
5. **Feedback:** 👍/👎 per bot message → `POST /feedback` → SQLite + Telegram on 👎.
6. **Widget polish:** SVG icons, unread badge when closed mid-stream, full-screen sheet layout on mobile (`100dvh`), input char counter near limit, graceful error + retry button.
7. **Prompt upgrade:** restructured system prompt (identity → hard rules → tool policy → style → JD-match template), few-shot tone examples, explicit instruction never to invent employers/dates/numbers.

**Exit criteria:** first token visible < 1.5s on a warm backend; JD-match answer renders with real headings and bullets; closing and reopening the widget restores the conversation; a 👎 lands in Telegram.

---

## Phase 4 — Backend hardening

**Scope:**
1. Rate limiting on `/chat` + `/chat/stream` (sliding window per IP, e.g. 20 req / 5 min) → 429 with friendly client message.
2. Input limits: `message` max 8,000 chars (Pydantic), max 50 history turns assembled server-side.
3. Remove the client-supplied `history` override in `ChatRequest` — it lets any caller forge conversation context.
4. `X-Admin-Token` check on all `/admin/*` routes; remove token-prefix leak in `/admin/test-telegram`.
5. Structured logging (one JSON line per chat: session, latency, tokens, eval verdict) replacing scattered prints.
6. Evaluator: REJECTED verdicts → Telegram notification + `eval_failures` table for review.
7. Nightly SQLite backup of `ibryam_chat.db` (HF Spaces storage is ephemeral across rebuilds — document persistence strategy).

**Exit criteria:** unauthenticated `/admin/daily-report` returns 401; 25 rapid requests from one IP get 429; a forged-history request is ignored server-side.

---

## Phase 5 — Growth & differentiation  *(after everything above ships)*

Ideas ranked, not committed:
1. **Per-project case-study pages** (`/projects/swiss-macro-monitor.html`) — architecture diagram, problem→solution narrative, key SQL/dbt snippets. Recruiters who click deserve depth.
2. **"How this chatbot works" page** — the chatbot is itself the best AI-engineering work sample; diagram the agent/RAG/evaluator loop publicly.
3. Privacy-friendly analytics (Cloudflare Web Analytics — free, no cookie banner needed).
4. Auto-generated weekly digest: unknown questions → suggested `faq.md` additions (GitHub Action exists at `.github/workflows/daily-report.yml`; extend it).
5. German-language toggle for DACH recruiters (chatbot already answers in the visitor's language — advertise it).
6. CV tailoring endpoint: paste a JD → downloadable role-tailored one-pager (stretch).

---

## Execution playbooks

| Skill | Path | Use it when |
|-------|------|-------------|
| Design System | `.claude/skills/design-system/SKILL.md` | Any change that touches CSS, colors, spacing, typography, or components |
| UX Overhaul | `.claude/skills/ux-overhaul/SKILL.md` | Implementing Phase 2 (and Phase 1 steps embedded in it) |
| Chatbot Upgrade | `.claude/skills/chatbot-upgrade/SKILL.md` | Implementing Phase 3 + Phase 4 |
| Deploy | `.claude/skills/deploy/SKILL.md` | Shipping to HF Spaces / Cloudflare Pages |

Rules for any implementing agent, regardless of capability:
1. Work one phase at a time, in order. Within a phase, follow the numbered steps in the skill exactly.
2. After each step, run the **Verify** block in the skill before moving on. If verification fails, stop and fix; do not stack changes on a broken step.
3. Never change scope mid-step. If a step seems wrong, stop and ask — do not improvise.
4. Update `tasks/todo.md` checkboxes as steps complete.
