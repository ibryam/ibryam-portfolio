Review the current staged changes (or the last commit if nothing is staged) as a senior engineer would before approving a PR.

Check in this order:
1. **Correctness** — does the logic do what it claims? Are there off-by-one errors, race conditions, or unhandled edge cases?
2. **Security** — any injection vectors, exposed secrets, missing auth checks, or OWASP Top 10 issues?
3. **Code style** — does it follow `.claude/rules/code-style.md`? Names, comments, function size, nesting.
4. **Tests** — are new behaviours covered? Does anything break existing tests?
5. **Performance** — any N+1 queries, unbounded loops, or unnecessary allocations?
6. **Reversibility** — are destructive operations guarded? Can this be rolled back safely?

Output format:
- Lead with a one-line verdict: APPROVE / REQUEST CHANGES / DISCUSS
- Group findings by severity: BLOCKER → CONCERN → SUGGESTION
- For each finding: file:line — what the issue is — why it matters — how to fix it
- End with a count: X blockers, Y concerns, Z suggestions

Be direct. Don't soften blockers. Don't invent issues that aren't there.
