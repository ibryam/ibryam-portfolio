# API Conventions

## Resource Design
- URLs are nouns, not verbs: /users not /getUsers
- Plural resource names: /users/{id}, /orders/{id}/items
- Nest only one level deep: /users/{id}/orders — avoid /users/{id}/orders/{id}/items/{id}
- Use query params for filtering, sorting, pagination — not path segments

## HTTP Verbs
- GET — read, always idempotent, never mutates
- POST — create a new resource or trigger an action
- PUT — full replace of a resource
- PATCH — partial update
- DELETE — remove; return 204 No Content on success

## Response Shape
Success:
```json
{ "data": { ... } }
```
Error:
```json
{ "error": { "code": "VALIDATION_FAILED", "message": "Human-readable message", "details": [...] } }
```
- Always consistent shape — never mix bare objects with wrapped ones

## Status Codes
- 200 OK, 201 Created, 204 No Content
- 400 Bad Request (client error), 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict
- 422 Unprocessable Entity (validation), 429 Too Many Requests
- 500 Internal Server Error — never leak stack traces

## Versioning
- Version in the URL path: /api/v1/
- Never break existing endpoints without a new version
- Deprecate with a Deprecation response header before removing

## Authentication
- Bearer token in Authorization header: `Authorization: Bearer <token>`
- Never in query params or cookies (unless explicitly required by the client type)

## Pagination
- Cursor-based preferred over offset for large datasets
- Response includes: data[], next_cursor, has_more
