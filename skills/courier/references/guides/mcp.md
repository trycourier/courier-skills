# Courier MCP Servers

**Contents:** [Two servers. Pick by what you need](#two-servers-pick-by-what-you-need) · [API MCP Server](#api-mcp-server) · [Quick Reference](#quick-reference) · [Installation](#installation) · [Available Tools](#available-tools) · [Error Handling](#error-handling) · [Known gaps](#known-gaps) · [Related](#related)

## Two servers. Pick by what you need

| | **API MCP** | **Docs MCP** |
|---|---|---|
| URL | `https://mcp.courier.com` | `https://www.courier.com/docs/mcp` |
| Auth | `api_key` header (required) | **None**, public docs |
| Purpose | **Do things**: send, manage templates, journeys, profiles, preferences | **Look things up**: search docs, read pages, read the OpenAPI specs |
| Tools | ~170 (see inventory below) | `search_courier`, `query_docs_filesystem_courier`, `submit_feedback` |
| Reach for it when | You're operating on a workspace | You need semantics, a parameter shape, or a page you can't name |

Most agent sessions want **both**: the docs MCP to learn the correct shape, the API MCP to execute it.

### Docs MCP

Auto-provisioned by Mintlify for the docs site, nothing to configure. Install:

```bash
claude mcp add --transport http courier-docs https://www.courier.com/docs/mcp
```

- **`search_courier`**: semantic search over every docs page and the OpenAPI specs (~20k tokens a call). Use it when you don't know where to look.
- **`query_docs_filesystem_courier`**: shell-style `head`/`grep`/`ls`/`tree` over the whole docs site (~2k tokens a page). Prefer it once you know the path.
- **`submit_feedback`**: report a wrong or outdated docs page to Courier's docs team.

When to use which source, including the cheaper `.md` page fetch: [Verifying Against Live Sources](../../SKILL.md#verifying-against-live-sources).

---

## API MCP Server

> The tool inventory below is a snapshot. Tool names and coverage drift as Courier ships, so **the server's live `tools/list` wins over this file**. An advertised tool doesn't prove its endpoint still exists: if a tool returns a `404` or route error, check the [API reference](https://www.courier.com/docs/api-reference/) before assuming you called it wrong.

## Quick Reference

### Rules
- Auth via the `api_key` header, with a key from [Settings > API Keys](https://app.courier.com/settings/api-keys). Use a dedicated key per environment for production or CI
- Coverage is most of the API, including template and journey writes, but newly shipped endpoints can lag (see [Known gaps](#known-gaps)). If a tool you need isn't in `tools/list`, use the SDK, CLI, or REST
- After setup, confirm with one read call (`list_notifications` or `list_messages`). Don't write to a workspace only to verify setup
- Qualify tool names with the server name (e.g. `courier:list_messages`) in prompts and docs
- MCP and the [CLI](./cli.md) cover substantially the same surface with the same key. Pick MCP inside an MCP-capable editor or agent, the CLI for shell-only environments, pipelines, and CI/CD

---

## Installation

### Cursor

In Cursor, go to **Cursor > Cursor Settings > Tools & Integrations > MCP Tools > New MCP Server**, then add:

```json
{
  "mcpServers": {
    "courier": {
      "url": "https://mcp.courier.com",
      "headers": {
        "api_key": "YOUR_COURIER_API_KEY"
      }
    }
  }
}
```

Or use the one-click install: [Install MCP Server](https://cursor.com/en/install-mcp?name=courier&config=eyJ1cmwiOiJodHRwczovL21jcC5jb3VyaWVyLmNvbSIsImhlYWRlcnMiOnsiYXBpX2tleSI6IlhYWFgifX0%3D), after installing, open **Cursor Settings > MCP** and replace `XXXX` with your actual Courier API key.

Works best with Agent mode enabled (in the Cursor chat input, select "Agent" instead of "Ask" or "Edit").

### Claude Code

```bash
claude mcp add --transport http courier https://mcp.courier.com --header api_key:YOUR_COURIER_API_KEY
```

### Codex

Add this to `~/.codex/config.toml`, then restart Codex. `codex mcp add` can't set custom headers, so edit the file directly.

```toml
[mcp_servers.courier]
url = "https://mcp.courier.com"
http_headers = { "api_key" = "YOUR_COURIER_API_KEY" }
```

### Claude Desktop, Windsurf, VSCode

Each takes the same URL and `api_key` header in its MCP config. Claude Desktop sends the header through the `mcp-remote` bridge: `"command": "npx", "args": ["-y", "mcp-remote", "https://mcp.courier.com", "--header", "api_key: YOUR_COURIER_API_KEY"]`. Exact config for each editor: [courier.com/docs/resources/mcp](https://www.courier.com/docs/resources/mcp).

### Calling Courier MCP from your own agent

Any MCP client that can set a custom request header works: point it at `https://mcp.courier.com` with `api_key: $COURIER_API_KEY`. Clients that only send bearer auth (the Claude Messages API connector sends `authorization_token` as a bearer token) may be rejected; bridge them with `npx -y mcp-remote https://mcp.courier.com --header api_key:$COURIER_API_KEY`, or use the [CLI](./cli.md) or SDK directly.

## Available Tools

Call the server's `tools/list` for exact names and parameters. Tools follow the API's resources (`send_message`, `get_message_history`, `create_notification`, `invoke_journey`, `create_or_merge_user`, …). What the names don't tell you:

| Area | Know this |
|------|-----------|
| Delivery debugging | `list_messages`, `get_message_history`, `get_message_content`, `trace_message`: the same ladder as the [CLI](./cli.md#debugging-workflow) |
| Templates | `publish_notification` publishes the draft or a past version. `put_notification_locale` writes one locale and merges ([localization.md](./localization.md)). `get_notification_metrics` follows [metrics.md](./metrics.md)'s window rules |
| Device Preview | `create_preview_run` is billed per device ([device-preview.md](./device-preview.md)) |
| Journeys | `create_journey` takes a trigger and an exit only and makes a DRAFT; add send nodes with `replace_journey` once the journey's templates exist. Publish each template with `publish_journey_template` (or create it published) before `publish_journey`, which doesn't publish them ([journeys.md](./journeys.md)) |
| Preferences and digests | `list_preference_logs` lists preference changes. Set a topic's digest with `digest` on `create_preference_topic` / `replace_preference_topic`; move a user onto a schedule with `digest_schedule_id` on `update_user_preference_topic`. `release_digest` releases a whole schedule, `release_user_digest` one recipient and topic |
| Bulk | `create_bulk_job` (`message.event` required) → `add_bulk_users` → `run_bulk_job`, in that order ([bulk.md](./bulk.md)) |
| Translations | `get_translation` / `update_translation` are workspace `.po` strings for `{{t}}`, not template translations |

## Error Handling

Tool errors come back as `{ "error": true, "status": 404, "message": "Profile not found" }`, carrying the API's HTTP status. A `403` is a valid key without access to the resource: check the key's environment and scope.


## Known gaps

Check `tools/list` first; coverage grows as Courier ships. When a tool or parameter you need is not
there, use the SDK, CLI, or REST. Areas that have lagged the API:

| Need | Use instead |
|---|---|
| Changing part of a provider config (`PATCH /providers/{id}`). `update_provider` is a full replacement, so don't use it to change one setting | `client.providers.patch` or `courier providers patch`, see [providers.md](./providers.md#update-part-of-a-config-patch) |

An absent tool is a possible gap, not proof the endpoint doesn't exist. Check the [API reference](https://www.courier.com/docs/api-reference/).

## Related

- [CLI](./cli.md) - Shell-based alternative for environments without MCP support
- [Quickstart](./quickstart.md) - Send your first notification with SDK, CLI, or curl
- [Reliability](./reliability.md) - Idempotency keys and retry patterns
- [Patterns](./patterns.md) - Reusable code patterns for common notification tasks

Documentation: [courier.com/docs/resources/mcp](https://www.courier.com/docs/resources/mcp)
