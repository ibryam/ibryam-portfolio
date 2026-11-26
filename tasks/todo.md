# Tasks — ibryam.com 10/10 Overhaul

Master checklist. The why/sequencing is in `tasks/roadmap.md`; the exact how is in `.claude/skills/`.
Rule: a box may only be ticked when its **AC** (acceptance criteria) is verifiably true.

---

## Phase H — Hiring content for DACH *(top priority — see roadmap)*

Items marked 🧑 need facts only Ibryam can provide.

- [ ] **H.1 Answer the fact sheet** 🧑 — current title on payroll/LinkedIn, German level today (certificate?), French level, where you live now, earliest start date, target cities, salary range (CHF), 2–4 numbers from UKG work, CV PDF.
      **AC:** answers recorded in `backend/knowledge_base/profile.md`.
- [ ] **H.2 Fix trust-breakers** — German date, title, location story, `projects.md` chatbot tech (now Claude Sonnet 5 / Cloudflare Pages), "ata professional" typo in `profile.md`.
      **AC:** grep for "June 2026", "gpt-4o-mini", "Cloudflare Workers" across `frontend/` + `knowledge_base/` returns nothing stale.
- [ ] **H.3 Recruiter quick-facts strip** under the hero (authorisation · availability · locations · languages · work mode).
      **AC:** visible without scrolling at 1366×768; all five facts present.
- [ ] **H.4 Impact-led hero stats + UKG rewrite** (needs H.1 numbers).
      **AC:** every hero stat is a business outcome or credential; UKG entry has 3–4 bullets, ≥ 2 quantified.
- [ ] **H.5 AI Chatbot featured project card** (+ decision on ATS Skipper visibility/name).
      **AC:** card with architecture one-liner, stack, GitHub link, "try it" button opening the widget.
- [ ] **H.6 CV PDF (EN + DE)** in `frontend/assets/` + download buttons (merges with 2.8).
      **AC:** both PDFs download with proper filenames; facts match page.
- [ ] **H.7 German layer** — DE hero/summary or `/de/` page; chat widget hint "Fragen Sie auf Deutsch".
      **AC:** German text reviewed by a native speaker or tutor before publishing.
- [ ] **H.8 SEO + link preview** (merges with 2.1/2.2) with DACH keywords.
      **AC:** LinkedIn Post Inspector shows image, title, description.
- [ ] **H.9 Market-gap decision** — scan ~20 target job ads (jobs.ch, LinkedIn CH/DE), tally required tools, choose one gap to close.
      **AC:** tally table in Review Notes; chosen project/cert added to Phase 5.
- [ ] **H.10 Social proof + contact** — 1–2 real quotes (with permission), Swiss phone, booking link.
      **AC:** visible on page; quotes attributed by role.

## Phase 0 — Hygiene & bug fixes

- [ ] **0.1 Fix Tableau scaling heights** — in `frontend/index.html`, the `VIZZES` array (`h:867`, `h:967`) disagrees with the actual iframe heights (868, 1167). Refactor `scaleAll()` to read `data-w`/`data-h` attributes from each `.viz-scaler` (add the missing `data-w="900" data-h="1167"` to `#scaler-smi`) and delete the hardcoded `VIZZES` numbers.
      **AC:** at 1400px, 1024px, 768px and 375px viewport widths, both dashboards show their full height with no clipped bottom and no dead space below.
- [x] **0.2 Remove empty-RAG auto-flag (regression)** — `backend/agent.py:143` still has `if not unknown_recorded and (not rag_chunks or response_signals_unknown)`. Commit `6e60af2` intended to drop the `not rag_chunks` half. Change condition to `if not unknown_recorded and response_signals_unknown`.
      **AC:** a question the model answers confidently but with zero RAG hits (e.g. "hi") does NOT insert into `unknown_questions`.
- [ ] **0.3 Prune `_UNCERTAINTY` list** — remove the generic phrases `"that information"`, `"this information"`, `"no details"`, `"not share"` from `backend/agent.py:86-94`; keep only phrases that unambiguously signal "I don't know".
      **AC:** reply "Happy to share that information: he uses BigQuery daily" does not trigger auto-flag.
- [ ] **0.4 Order history by id** — `backend/memory.py:get_recent_history` → `ORDER BY id DESC` instead of `ts DESC`.
      **AC:** two messages saved in the same second return in insertion order.
- [ ] **0.5 Escape FTS5 queries** — in `backend/memory.py:search_faq`, wrap: `safe = '"' + query.replace('"', '""') + '"'` and MATCH on `safe`.
      **AC:** `search_faq('what is your "salary" (gross)?')` returns a list, raises nothing.
- [x] **0.6 Gitignore server logs** — add `backend/server.log` + `backend/server_err.log` (or `backend/*.log`) to `.gitignore`.
      **AC:** `git status` no longer lists them.
- [x] **0.7 Update CLAUDE.md to reality** — stack section: agent = OpenAI `gpt-4o-mini` (`AGENT_MODEL`), evaluator = Gemini 2.0 Flash → Groq fallback, async log-only (no retry), notifications = Telegram (`TELEGRAM_TOKEN`/`TELEGRAM_CHAT_ID`), env-var table refreshed (`OPENAI_API_KEY`, drop Pushover).
      **AC:** every model/env-var named in CLAUDE.md appears in the code; nothing in CLAUDE.md contradicts `agent.py`/`evaluator.py`/`tools.py`.
- [ ] **0.8 Commit pending nav-order change** — About before Experience (already in working tree).
      **AC:** clean `git status` on `frontend/index.html`.

## Phase 1 — Design system foundation
*(spec: `.claude/skills/design-system/SKILL.md`)*

- [ ] **1.1 Token block** — replace the current 11-variable `:root` with the full token set from the skill (colors, spacing, type, radii, shadows, motion).
      **AC:** `grep -coE '#[0-9a-fA-F]{3,8}' frontend/index.html` counts hex values only inside `:root` and the favicon data-URI.
- [ ] **1.2 Fonts** — Space Grotesk (600/700) + Inter (400/500/600/700) via Google Fonts, `preconnect` + `display=swap`; `--font-display` / `--font-body` tokens applied.
      **AC:** headings render Space Grotesk, body renders Inter; no FOIT (text visible during font load).
- [ ] **1.3 Migrate hardcoded values** — every `#26b395`, `#d4942e`, `#0f1e38`, `#1a2f52`, `#0d1b33`, ad-hoc `rgba(46,196,166,…)` replaced by tokens.
      **AC:** grep from 1.1 passes; visual diff vs before is "same design, crisper".
- [ ] **1.4 Focus & motion baseline** — global `:focus-visible` ring token, `::selection`, `prefers-reduced-motion: reduce` kill-switch for all transitions/animations.
      **AC:** Tab key shows a visible ring on every link/button/pill/input; with reduced motion enabled (DevTools emulation), nothing animates.
- [ ] **1.5 SVG icon set** — inline `<svg>` sprite (chat, send, close, external, arrow-down, document, github, linkedin, mail, play); all emoji removed.
      **AC:** `grep -c '💬\|➤\|✕\|📋' frontend/index.html` returns 0.

## Phase 2 — Page UX overhaul
*(playbook: `.claude/skills/ux-overhaul/SKILL.md`)*

- [ ] **2.1 SEO/meta head** — meta description, OG (title/description/image/url/type), Twitter card, canonical, theme-color, JSON-LD Person.
      **AC:** validator.schema.org parses the JSON-LD with zero errors; OG preview shows image + correct title.
- [ ] **2.2 robots.txt + sitemap.xml + OG image** in `frontend/`.
      **AC:** all three deploy and return 200 on the live domain.
- [ ] **2.3 A11y pass** — skip link, `<main>` landmark, chat `aria-expanded`/`role="log"`/`aria-live="polite"`, pills → `<button>`, Escape closes chat and returns focus to toggle, alt text audit, contrast fixes per skill (muted text ≥ 4.5:1 at body size).
      **AC:** Lighthouse Accessibility ≥ 95; full keyboard-only walkthrough (nav → chat open → send → close) works.
- [ ] **2.4 Mobile hamburger nav** — below 700px, hamburger button toggles a full-width dropdown panel; links close it on tap.
      **AC:** at 360px width all four section links + Ask AI are reachable; menu traps no focus and closes on Escape.
- [ ] **2.5 Hero refinement** — copy tightened per skill, single primary CTA ("Ask my AI" promoted to primary, "View Projects" secondary, LinkedIn ghost), scroll cue, entrance animation (opacity/translate, 400ms, reduced-motion-safe).
      **AC:** matches the skill's hero spec exactly; CLS = 0 from the animation.
- [ ] **2.6 Tableau click-to-load facades** — static preview (screenshot in `frontend/assets/`) + play overlay; iframe injected on click only.
      **AC:** network tab on fresh load shows zero requests to `public.tableau.com`; click loads the dashboard within the same container, correctly scaled.
- [ ] **2.7 Scroll-spy + reveal** — active nav link tracks section in view (IntersectionObserver); sections fade-up once on first reveal.
      **AC:** scrolling through the page highlights nav items in order; animations fire once, never on scroll-up, never with reduced motion.
- [ ] **2.8 CV download CTA** — `frontend/assets/Ibryam_Faik_CV.pdf` + download buttons (hero + footer). *(Ibryam supplies the PDF; wire a placeholder link if absent and note it here.)*
      **AC:** button downloads the PDF with a proper filename.
- [ ] **2.9 Privacy note in footer** — one sentence disclosing chat transcript storage + visit geolocation, linking `mailto:` for removal requests.
      **AC:** visible in footer at all widths.
- [ ] **2.10 Lighthouse gate** — run Lighthouse mobile on the deployed preview.
      **AC:** Performance ≥ 90, Accessibility ≥ 95, Best Practices ≥ 95, SEO ≥ 95. Record scores here.

## Phase 3 — Chatbot UX
*(playbook: `.claude/skills/chatbot-upgrade/SKILL.md`)*

- [ ] **3.1 Backend SSE endpoint** — `POST /chat/stream`, streams `data:` JSON events (delta / done / error), reuses the agent loop with `stream=True` on the final round.
      **AC:** `curl -N` against local server shows incremental deltas; tool-call rounds still work (ask a salary question → faq_lookup fires → streamed answer).
- [ ] **3.2 Frontend streaming render** — widget consumes the stream, renders tokens incrementally with a blinking caret; auto-fallback to `/chat` if stream errors before first delta.
      **AC:** first visible token < 1.5s warm; killing the connection mid-stream shows the retry UI, and retry works.
- [ ] **3.3 Safe markdown renderer** — headings (h3/h4 → styled `<strong>` blocks), bold, italic, `- `/`1. ` lists, links (https only, `rel="noopener nofollow"`, escaped), code spans. Escapes HTML first; no innerHTML of raw model text.
      **AC:** the JD-match response renders headings + bullets correctly; `<img src=x onerror=alert(1)>` in a bot reply renders as literal text.
- [ ] **3.4 Session persistence** — `session_id` + transcript in `localStorage` (cap 50 messages); restore on load; "Clear chat" control in header wipes both.
      **AC:** reload page → reopen widget → conversation intact; Clear chat → greeting state.
- [ ] **3.5 Feedback thumbs** — 👍/👎 SVG pair on each bot message; `POST /feedback {session_id, message_index, vote}` → SQLite `feedback` table; 👎 → Telegram.
      **AC:** votes persist in DB; thumb state survives reopen via localStorage.
- [ ] **3.6 Widget polish** — SVG icons, mobile full-screen sheet (`100dvh`, safe-area insets), char counter appears at >7,000 chars, unread dot on toggle when reply arrives while closed.
      **AC:** widget usable on a 360×740 phone with keyboard open; counter and unread dot behave per skill.
- [ ] **3.7 System prompt v2** — restructured per skill (identity → hard rules → tools → style → JD template + few-shots).
      **AC:** the 12-question regression script in the skill passes (correct tool calls, no invented facts, JD format followed).
- [ ] **3.8 Contextual suggestion pills** — pills survive after first message as horizontally scrollable row; JD-match completion swaps in follow-up pills.
      **AC:** pills clickable at any conversation depth; never overlap input bar.

## Phase 4 — Backend hardening
*(playbook: `.claude/skills/chatbot-upgrade/SKILL.md`, Part D)*

- [ ] **4.1 Rate limiting** — in-memory sliding window: 20 chat requests / 5 min / IP (honour `CF-Connecting-IP`); 429 with `Retry-After`; friendly client message.
      **AC:** 25 rapid curls → first 20 succeed, rest 429; widget shows "I'm getting a lot of messages — try again in a few minutes."
- [ ] **4.2 Input limits** — Pydantic: `message: str = Field(max_length=8000)`; server assembles ≤ 30 history turns.
      **AC:** 9,000-char POST → 422; widget pre-empts with counter (3.6).
- [ ] **4.3 Remove client history override** — drop `history` from `ChatRequest`; agent always reads SQLite.
      **AC:** posting a forged `history` array has no effect on the reply.
- [ ] **4.4 Admin auth** — `X-Admin-Token` (env `ADMIN_TOKEN`, compare via `secrets.compare_digest`) required on every `/admin/*`; delete the token-prefix leak in `/admin/test-telegram`.
      **AC:** no header → 401; correct header → 200; GitHub Action workflow updated with the secret.
- [ ] **4.5 Structured chat log** — one JSON line per `/chat`: ts, session, msg_len, reply_len, latency_ms, tool_calls, eval verdict.
      **AC:** logs parse with `jq`.
- [ ] **4.6 Evaluator REJECTED → Telegram + `eval_failures` table.**
      **AC:** forcing a rejection (temporary test prompt) produces a Telegram message and a DB row.
- [ ] **4.7 Persistence doc** — document HF Spaces ephemeral-disk implications for `ibryam_chat.db` + `vector_store/` in CLAUDE.md; add daily DB-snapshot step to the existing daily-report GitHub Action.
      **AC:** strategy written; snapshot artifact appears in Action run.

## Phase 5 — Growth (rank later, do not start before 0–4 ship)

- [ ] 5.1 Case-study page: Swiss Macro Monitor
- [ ] 5.2 Case-study page: SMI Risk Monitor
- [ ] 5.3 "How this chatbot works" page (architecture diagram of agent/RAG/evaluator)
- [ ] 5.4 Cloudflare Web Analytics
- [ ] 5.5 Unknown-questions → faq.md suggestion digest (extend daily-report action)
- [ ] 5.6 German UI toggle / advertise multilingual chat

## Done

<!-- Move completed items here with date + commit hash -->
- 2026-11-26 `ac0e441` Agent switched to Claude Sonnet 5 (`claude-sonnet-5`), prompt style fixes, 0.2 empty-RAG auto-flag removed
- 2026-11-26 `8b99099` Telegram: one summary per conversation; HTML-escape + 4096-char guard (fixed silently dropped messages)
- 2026-11-26 `621cc6a` 0.6 `*.log` gitignored; 0.7 CLAUDE.md rewritten for current stack

## Review Notes

<!-- Post-task observations. Lighthouse scores from 2.10 go here too. -->
