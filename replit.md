# Aura Chatbot

A Python chatbot website for friendly, human-like conversations in the browser.

## Run & Operate

- `python chatbot_app.py` — run the chatbot website (port 8000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- Python 3
- Standard library `http.server` backend
- Browser-native HTML, CSS, and JavaScript interface

## Where things live

- `chatbot_app.py` — Python server, chatbot reply engine, and web UI
- `artifacts/mira-chatbot/src/App.tsx` — polished Aura browser interface shown in the main preview
- `artifacts/api-server/src/routes/chat.ts` — preview API route used by the browser interface

## Architecture decisions

- The first version uses Python's standard library, so it runs without a package install or external API key.
- The standalone Python version and the preview API share the same rule-based conversation behavior.
- The browser sends the recent conversation history with each message so the response engine can stay contextual.
- The frontend uses a relative `/api/chat` path so it works in the Replit preview and when published.

## Product

- Chat with Aura in a responsive browser interface.
- `hi`, `hello`, and similar greetings receive the requested “Hello! How are you?” response.
- Includes quick prompts, typing feedback, timestamps, conversation history, and Enter-to-send behavior.

## User preferences

- The user asked for the chatbot website and its logic to be written in Python.

## Gotchas

- The app uses the `PORT` environment variable when present and defaults to port 8000.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
