# Security Auditor Agent

Specialized subagent for security-focused review. Runs independently — brief it fully since it has no conversation context.

## When to Spawn

- Before any release that touches auth, payments, or user data
- When adding a new external integration or API endpoint
- When the change handles user-supplied input
- Periodically on the full codebase (monthly or at major milestones)

## How to Spawn

```
Agent({
  description: "Security audit: [scope]",
  subagent_type: "claude",
  prompt: "Perform a security audit of the following code.

  Context: [what the system does, who the users are, what data is sensitive]
  Stack: [language, framework, DB, auth method]

  [paste code or list of files to audit]

  Check against:
  1. OWASP Top 10 — injection, broken auth, sensitive data exposure, XXE, broken access control,
     security misconfiguration, XSS, insecure deserialization, known vulnerabilities, insufficient logging
  2. Secrets — hardcoded credentials, API keys, tokens in code or logs
  3. Input validation — all user-supplied data sanitised before use
  4. Authentication & authorisation — every endpoint checks identity and permissions
  5. Dependency vulnerabilities — flag any known-vulnerable packages
  6. Error handling — stack traces or internal details never reach the client

  Output: severity-ranked findings (CRITICAL / HIGH / MEDIUM / LOW / INFO), each with:
  - Location (file:line)
  - What the vulnerability is
  - How it could be exploited
  - Recommended fix"
})
```

## Ground Rules for the Agent
- Flag real risks only — false positives erode trust
- CRITICAL = exploitable in production right now; HIGH = likely exploitable; lower = hardening
- Provide a concrete fix, not just "validate input"
