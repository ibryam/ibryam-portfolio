# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

**Name:** ibryam-portfolio
**Purpose:** [One-line description of what this project does]
**Stack:** [Language · Framework · Database · Infrastructure]

## Quick Start

```bash
# Install dependencies
[install command]

# Run locally
[run command]

# Run tests
[test command]
```

## Architecture

[High-level description — how the main pieces fit together. Only what requires reading multiple files to understand. Standard structure can be explored.]

## Environment Variables

```
VAR_NAME   — what it does and where to get it
```

Copy `.env.example` → `.env` before running locally.

## Non-obvious Patterns

[Anything that would surprise a new developer: implicit invariants, framework quirks, cross-cutting concerns, workarounds for known issues.]

## Rules

- Code style → `.claude/rules/code-style.md`
- Testing → `.claude/rules/testing.md`
- API conventions → `.claude/rules/api-conventions.md`

## Commands

- `/review` — full review of staged changes (correctness, security, style)
- `/fix-issue <description>` — autonomous bug fix from a plain-language description

## Agents

- `code-reviewer` — correctness, performance, style (see `.claude/agents/code-reviewer.md`)
- `security-auditor` — OWASP, secrets, auth, injection (see `.claude/agents/security-auditor.md`)

