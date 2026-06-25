# Next Long-Running API Proxy

## Problem
When frontend calls backend through Next rewrite proxy (`/api -> localhost:4000`), long-running requests (such as AI check) may fail with `socket hang up` / `ECONNRESET`. In this state, Next may also emit `Failed to load static file for page: /500 ... 500.html` in local runs.

## Rule
For local development, prefer direct browser-to-backend API calls via `NEXT_PUBLIC_API_URL` instead of relying on Next rewrite proxy for long-running endpoints.

## Fix Pattern
- Configure frontend env in local dev:
```bash
NEXT_PUBLIC_API_URL=http://localhost:4000/api
```
- Keep `/api` rewrite only as fallback.
- Add a lightweight `pages/500.tsx` to provide stable error fallback if proxy/server failures occur.

## Anti-pattern
- Sending long-running API requests exclusively through Next rewrite proxy in local development.
- Relying on missing default 500 static page behavior when proxy failures happen.
