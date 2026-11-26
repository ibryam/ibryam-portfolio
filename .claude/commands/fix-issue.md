Fix the following issue autonomously: $ARGUMENTS

Process:
1. **Understand** — read the relevant files, reproduce the problem mentally, identify the root cause (not just the symptom)
2. **Plan** — write the fix to tasks/todo.md before touching any code; check in if the scope is larger than expected
3. **Fix** — make the minimal change that resolves the root cause; do not refactor surrounding code
4. **Verify** — run tests, check logs, confirm the fix works end-to-end
5. **Document** — if you learned something non-obvious, add it to tasks/lessons.md

Rules:
- Fix root causes, never symptoms
- If you find yourself touching more than 3 files, stop and re-plan
- Ask before making irreversible changes (deleting data, dropping columns, force-pushing)
- Never use --no-verify to bypass hooks
