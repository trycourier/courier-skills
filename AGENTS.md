# Contributing to Courier Skills

For anyone, human or agent, editing this repo.

## One skill, one internal boundary

Everything is the `skills/courier` skill. Inside it, `references/` splits along server vs client:

- **Server-side** (most of it): sending on every channel, journeys, templates, preferences, routing, providers, delivery debugging. Lives in `references/channels/` and `references/guides/`.
- **Client-side**: rendering the in-app inbox (JWT auth, the frontend SDKs, read state, real-time). Lives in `references/inbox/`, entered via `references/inbox/rendering.md`.

Sending *to* the inbox is a channel (`references/channels/inbox.md`); *rendering* it is client work (`references/inbox/`). When unsure where something belongs, ask whether the code runs on a server or in the user's browser or device.

## Two rules that keep this honest

**Every SDK call must exist.** Any `client.X.Y(...)` you write in a reference must exist in the installed `@trycourier/courier` (Node) and `trycourier` (Python) packages. Don't reconstruct signatures from memory. Read the SDK's own type definitions, or use the docs MCP (`https://www.courier.com/docs/mcp`).

**YAML frontmatter descriptions must be wrapped in double quotes**; an unquoted colon-space anywhere in the value makes the file unparseable and the skill silently uninstallable. Before committing a `SKILL.md`, validate the frontmatter with a strict YAML parser, not by eyeballing:

```bash
node -e 's=require("fs").readFileSync("skills/courier/SKILL.md","utf8");require("js-yaml").load(s.split(/^---$/m)[1])' && echo OK
```

**A skill's `name:` equals its directory name**, and each `SKILL.md` stays lean (~5,000 tokens, ~500 lines). Depth lives in `references/`, pulled on demand; the entry point routes, it doesn't document everything.

## When Courier ships an endpoint

Agents only learn what the skill routes them to. For every new public endpoint or SDK method, the same PR adds:

- a section in the reference file that owns the resource, or a new reference file
- a row in SKILL.md's **Where to Look**, in the words a user would ask with
- a row in `references/sdk-reference.md` (Node and Python)
- a row in `references/guides/cli.md` if the CLI has a command

Don't write that MCP lacks a tool. Tell the agent to check `tools/list` and fall back to the SDK or CLI.
