# Contributing to Courier Skills

For anyone — human or agent — editing this repo.

## One skill, one internal boundary

Everything is the `skills/courier` skill. Inside it, `references/` splits along server vs client:

- **Server-side** (most of it) — sending on every channel, journeys, templates, preferences, routing, providers, delivery debugging. Lives in `references/channels/` and `references/guides/`.
- **Client-side** — rendering the in-app inbox (JWT auth, the frontend SDKs, read state, real-time). Lives in `references/inbox/`, entered via `references/inbox/rendering.md`.

Sending *to* the inbox is a channel (`references/channels/inbox.md`); *rendering* it is client work (`references/inbox/`). When unsure where something belongs, ask whether the code runs on a server or in the user's browser or device.

## Two rules that keep this honest

**Every SDK call must exist.** Any `client.X.Y(...)` you write in a reference is checked against the installed `@trycourier/courier` (Node) and `trycourier` (Python) packages:

```bash
python3 scripts/verify-sdk-claims.py path/to/node_modules/@trycourier/courier/resources
```

Don't reconstruct signatures from memory — read the SDK's own types, or use the docs MCP (`https://www.courier.com/docs/mcp`).

**A skill's `name:` equals its directory name**, and each `SKILL.md` stays lean (~5,000 tokens, ~500 lines). Depth lives in `references/`, pulled on demand; the entry point routes, it doesn't document everything.
