# Code Reviewer Agent

Specialized subagent for focused code review. Operates independently with isolated context — it cannot see the main conversation, so the prompt must be fully self-contained.

## When to Spawn

Spawn this agent when:
- You want an independent second opinion before merging
- The change is large enough that reviewing it inline would pollute the main context
- You need a focused review of a specific file or function, not the whole diff

## How to Spawn

```
Agent({
  description: "Code review: [what changed]",
  subagent_type: "claude",
  prompt: "Review the following code for correctness, style, and security.
  
  Context: [what the code is supposed to do, relevant constraints]
  
  File: [file path]
  [paste the relevant code or diff]
  
  Check:
  1. Correctness — does the logic match the intent?
  2. Edge cases — what inputs would break this?
  3. Security — any injection, auth, or data exposure issues?
  4. Style — naming, function size, unnecessary complexity
  
  Output: APPROVE or REQUEST CHANGES, then findings grouped by severity (BLOCKER / CONCERN / SUGGESTION)."
})
```

## Ground Rules for the Agent
- Report findings, do not fix them — the main agent decides what to act on
- Be specific: file:line, what the issue is, why it matters
- Do not invent issues to seem thorough
- A clean review with no findings is a valid and useful output
