# Code Style Rules

## Naming
- Names must reveal intention — if you need a comment to explain a name, rename it
- Functions named for what they do, not how (get_user not fetch_user_from_db_by_id)
- Booleans prefixed: is_, has_, can_, should_

## Functions
- Single responsibility — if you need "and" to describe it, split it
- Keep under ~30 lines; if scrolling is required, extract
- No side effects in functions named as queries (getX should never mutate)

## Comments
- Write no comments by default
- Only add one when the WHY is non-obvious: a hidden constraint, a subtle invariant, a workaround for a specific bug
- Never describe WHAT the code does — well-named identifiers do that

## Structure
- Flat over nested — max 3 levels of indentation before extracting
- No dead code — remove it, git history exists for a reason
- No feature flags or backwards-compat shims unless explicitly required
- Three similar lines is better than a premature abstraction

## Error Handling
- Only validate at system boundaries (user input, external APIs, environment)
- Trust internal code and framework guarantees — don't defensively re-validate them
- Fail fast and loud — silence errors only when you have a concrete fallback

## Dependencies
- Prefer standard library over third-party for simple tasks
- Every new dependency is a liability — justify it
