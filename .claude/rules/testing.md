# Testing Rules

## What to Test
- Test behaviour at the boundary closest to real usage
- Test the contract, not the implementation — internals can be refactored freely
- Prioritise: critical paths > edge cases > happy paths

## What Not to Test
- Private implementation details
- Framework or library code
- Things that are already typed / validated at compile time

## Test Structure
- Arrange / Act / Assert — one clear block each, no interleaving
- One logical assertion per test (multiple assert calls are fine if they test the same thing)
- Test names describe the scenario: test_returns_error_when_token_expired not test_auth_1

## Reliability
- Tests must be deterministic — no sleep(), no relying on external services without a stub
- No shared mutable state between tests
- If a test is flaky: fix or delete it; never skip and forget

## Mocking
- Mock at the system boundary (HTTP, DB, filesystem), not internal functions
- Prefer real implementations in fast tests — fake only what's slow or non-deterministic
- If the mock is more complex than the thing it replaces, reconsider

## CI
- All tests must pass before a task is marked done
- A passing test suite is a necessary condition, not sufficient — verify behaviour end-to-end when possible
