# How to Update the Chatbot Knowledge Base

The chatbot learns from two sources. Each has a different purpose and update process.

---

## Which file to edit

| What you want to add | File to edit |
|---|---|
| Personal facts (hobbies, team, family, interests) | `profile.md` |
| Work experience, job duties, certifications | `experience.md` |
| Project details | `projects.md` |
| HR / recruiter questions (notice period, salary, etc.) | `faq.md` |

**Rule of thumb:** if a recruiter might ask it, put it in `faq.md`. If it's a fact about who you are, put it in `profile.md`.

---

## Updating `faq.md` (HR questions)

### Format

Every Q&A pair must follow this exact format — two stars, `Q:`, question text, two stars, newline, `A:`, answer:

```
**Q: What is your notice period?**
A: Ibryam's notice period is 4 weeks.
```

**Do not:**
- Put quotes around the question: ~~`**Q: "What is your notice period?"**`~~
- Leave a blank line between the `**Q:**` line and the `A:` line
- Use any other bold marker or header format

### After editing `faq.md`

**Restart the backend.** The FAQ table is wiped and rebuilt from scratch on every startup, so your changes take effect immediately after a restart.

To restart locally:
1. Stop the running server (Ctrl+C in the terminal, or kill the process)
2. Run: `uvicorn main:app --port 8000` from the `backend/` folder

---

## Updating `profile.md` (personal facts, relocation, skills summary)

Edit the file directly. After saving:

1. **Delete the `vector_store/` folder** — this forces a full rebuild
2. **Restart the backend**

The chatbot will re-index your updated profile on the next startup (takes ~30 seconds the first time, faster on subsequent runs).

```
# Delete the vector store (Windows)
rmdir /s /q D:\00.Projects\ibryam-portfolio\backend\vector_store

# Then restart
cd D:\00.Projects\ibryam-portfolio\backend
uvicorn main:app --port 8000
```

---

## Reviewing unanswered questions

When a visitor asks something the bot cannot answer, it is stored automatically. To review:

```
GET http://localhost:8000/admin/unknown-questions
```

Each entry has:
- `question` — what was asked
- `ts` — when it was asked
- `answered` — 0 (pending) or 1 (done)

**Workflow:**
1. Check the list periodically
2. If a question is work-related and worth answering permanently, add a `**Q:**/A:` pair to `faq.md` and restart
3. Mark it answered:
   ```
   POST http://localhost:8000/admin/unknown-questions/{id}/answered
   ```

---

## Quick reference — restart commands

**Windows (PowerShell):**
```powershell
# Kill existing server
Get-Process uvicorn | Stop-Process -Force

# Start fresh
cd D:\00.Projects\ibryam-portfolio\backend
& ..\venv\Scripts\uvicorn.exe main:app --port 8000
```

**HuggingFace Spaces (production):** push a commit to the Space repo — it redeploys automatically.
