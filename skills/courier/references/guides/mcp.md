# Courier MCP Servers

## Two servers. Pick by what you need

| | **API MCP** | **Docs MCP** |
|---|---|---|
| URL | `https://mcp.courier.com` | `https://www.courier.com/docs/mcp` |
| Auth | `api_key` header (required) | **None**, public docs |
| Purpose | **Do things**: send, manage templates, journeys, profiles, preferences | **Look things up**: search docs, read pages, read the OpenAPI specs |
| Tools | ~144 (see inventory below) | `search_courier`, `query_docs_filesystem_courier`, `submit_feedback` |
| Reach for it when | You're operating on a workspace | You need semantics, a parameter shape, or a page you can't name |

Most agent sessions want **both**: the docs MCP to learn the correct shape, the API MCP to execute it.

### Docs MCP

Auto-provisioned by Mintlify for the docs site, nothing to configure. Install:

```bash
claude mcp add --transport http courier-docs https://www.courier.com/docs/mcp
```

- **`search_courier`**: semantic search across every docs page and the OpenAPI specs. Returns titles, paths, and content. Costs ~20k tokens per call, so use it when you don't know where to look.
- **`query_docs_filesystem_courier`**. Read-only virtual filesystem of the whole docs site. Shell-style, `head -200 /platform/journeys/nodes/batch.mdx`, `grep`, `ls`, `tree`. **Prefer this once you know the path**, a single page read is ~2k tokens instead of ~20k.
- **`submit_feedback`**: report an incorrect, outdated, or confusing page back to Courier's docs team. Use it when you find a genuine documentation defect; it closes the loop rather than silently working around the error.

The server indexes from docs navigation, so newly shipped pages appear immediately. It is more current than any snapshot in this skill. When it disagrees with this file about a doc page, it wins.

Cheaper still, when you already know the exact page: append `.md` to any docs URL (`https://www.courier.com/docs/journeys/nodes/batch.md`), plain HTTP, ~1–2k tokens, no MCP connection needed. Bad paths return a real `404`.

---

## API MCP Server

> The tool inventory below is a snapshot. Tool names, coverage, installation UI paths, and JSON config shape all drift as Courier ships MCP updates and editors change their settings surface. **Always prefer the server's live tool list over this file**, and re-verify against https://www.courier.com/docs/resources/mcp before quoting specifics. A tool being advertised does not guarantee the endpoint behind it still exists.

## Quick Reference

### Rules
- MCP provides structured tool access; agents discover tools automatically and call them with typed parameters
- Auth via `api_key` header; use the same API key from [Settings > API Keys](https://app.courier.com/settings/api-keys)
- Tools cover most of the Courier API. Send, messages, profiles, lists, audiences, notifications (**including writes**), journeys (**including writes**), brands, tenants, preferences, tokens, translations, digests, inbound, audit. Coverage is not complete: newly shipped endpoints can lag behind the API (see [Known gaps](#known-gaps)). The exact count changes as Courier ships; **call the MCP server's tool-list endpoint for the current list** rather than trusting any number written down here
- Journey management and notification-template writes are both available via MCP
- Prefer MCP when your editor supports it (Cursor, Claude Code, Claude Desktop, Windsurf, VSCode); fall back to [CLI](./cli.md) for shell-only environments or CI/CD
- MCP tools return structured JSON responses; errors include HTTP status code and message
- **A tool being advertised does not guarantee the endpoint behind it is live.** If a tool returns a 404 or a route error, check the API reference before assuming you called it wrong
- When referring to these tools in prompts or docs, qualify them with the server name (e.g. `courier:list_messages`) so the agent can resolve them unambiguously

### Practical setup guardrails

- Treat tool count as informative, not absolute: if the number changed, proceed as long as the tools you need are present.
- If a tool you expect is missing, check the live tool list before routing around it. This guide's inventory is a snapshot, the server is the truth.
- For production or CI usage, prefer a dedicated API key per environment/workspace.
- Validate auth and basic tool calls immediately after setup before relying on the integration for larger tasks.

### Quick verification checklist

Run this once after setup:

1. Confirm the server connects in your editor (status is healthy/connected).
2. Run one read call (for example `list_notifications` or `list_messages`) to confirm auth.
3. Run one write-safe call in your expected workflow area (for example profile merge or tenant list) to confirm parameter shape expectations.
4. Verify your needed feature is in `tools/list`; if not, route to the SDK, CLI, or REST.
5. Save a short note in project docs or PR description indicating which path is used (`MCP` vs `CLI/REST`) for repeatability.

### MCP vs CLI

| Use MCP | Use CLI |
|---------|---------|
| Editor has MCP support (Cursor, Claude Code, Windsurf, VSCode) | Shell-only environments (Codex, CI/CD pipelines) |
| Typed parameters with auto-discovery | Ad-hoc debugging in a terminal |
| Structured JSON responses | Human-readable or piped output |
| No shell required | `--transform` for GJSON filtering |

Both authenticate with the same `COURIER_API_KEY` and now cover substantially the same surface, including the full template and journey lifecycles. Pick on ergonomics, not capability: MCP for agent-driven work inside an editor, CLI for terminals, shell pipelines, and CI/CD.

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

### Claude Desktop

In Claude Desktop, go to **Claude > Settings > Developer > Edit Config**, then add:

```json
{
  "mcpServers": {
    "courier": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.courier.com", "--header", "api_key: YOUR_COURIER_API_KEY"]
    }
  }
}
```

### Windsurf

In Windsurf, go to **Windsurf > Windsurf Settings > Manage MCP Servers > View Raw Config**, then add:

```json
{
  "mcpServers": {
    "courier": {
      "serverUrl": "https://mcp.courier.com",
      "headers": {
        "api_key": "YOUR_COURIER_API_KEY"
      },
      "disabled": false,
      "disabledTools": []
    }
  }
}
```

### VSCode

Create `.vscode/mcp.json` in your project:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "courier-api-key",
      "description": "API key for Courier service",
      "password": true
    }
  ],
  "servers": {
    "courier": {
      "url": "https://mcp.courier.com",
      "type": "http",
      "headers": {
        "api_key": "${input:courier-api-key}"
      }
    }
  }
}
```

Open the chat window, click the Gear icon, then MCP Servers, and start the "courier" server.

### Calling Courier MCP from your own agent

The editor configs above are the tested path. They let you set an arbitrary `api_key` header, which is what Courier's hosted server expects. If you are driving MCP from your own code instead, note the auth difference below.

**Claude Messages API** (`@anthropic-ai/sdk`). Two parameters are required together: `mcp_servers` declares the connection, and `tools` must contain a matching `mcp_toolset` entry, omitting the toolset is a validation error.

```typescript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

const response = await client.beta.messages.create({
  model: "claude-opus-4-8",
  max_tokens: 4096,
  betas: ["mcp-client-2025-11-20"],
  mcp_servers: [
    {
      type: "url",
      name: "courier",
      url: "https://mcp.courier.com",
      authorization_token: process.env.COURIER_API_KEY,
    },
  ],
  tools: [{ type: "mcp_toolset", mcp_server_name: "courier" }],
  messages: [
    { role: "user", content: "Look up the profile for user-123 and tell me their email" },
  ],
});
```

> **Auth caveat. Verify before relying on this.** The Messages API connector sends `authorization_token` as an HTTP **bearer** token, whereas Courier's hosted server documents an `api_key` header. If the connector returns an auth error, the server does not accept bearer auth, fall back to a local stdio bridge (`npx -y mcp-remote https://mcp.courier.com --header api_key:$COURIER_API_KEY`), which can set arbitrary headers, or use the [CLI](./cli.md) / SDK directly.

**Other agent frameworks.** Any MCP client that can set a custom request header works, point it at `https://mcp.courier.com` with `api_key: $COURIER_API_KEY`. Clients that only support bearer auth need the `mcp-remote` bridge above.

## Available Tools

Tools cover most of the Courier API, all backed by the official `@trycourier/courier` Node SDK with typed error handling. **Call the server's `tools/list` for exact names and parameters.** The map below is for orientation: one line per area, naming the tools you reach for first.

| Area | Main tools |
|------|-----------|
| Send | `send_message`, `send_message_template`, `send_message_to_list`, `send_message_to_list_template` |
| Messages and delivery debugging | `list_messages`, `get_message`, `get_message_history`, `get_message_content`, `cancel_message`, `resend_message`, `archive_request` |
| Templates | `list_notifications`, `get_notification`, `create_notification`, `replace_notification`, `put_notification_content`, `publish_notification` (the draft, or a past version), `list_notification_versions`, `get_notification_draft_content`, `archive_notification` |
| Template metrics | `get_notification_metrics` (same window rules as [metrics.md](./metrics.md)) |
| Journeys | `create_journey`, `replace_journey`, `publish_journey`, `invoke_journey`, `cancel_journey`, `get_journey`, `list_journeys`, `create_journey_template`, `put_journey_template_content`, `publish_journey_template`. Create makes a DRAFT with no send nodes; add them with `replace_journey` once the journey's templates exist. Prefer these over hand-rolled REST |
| Users and profiles | `get_user_profile_by_id`, `create_or_merge_user`, `patch_profile`, `replace_profile`, `delete_profile`, `generate_jwt_for_user` |
| Push tokens | `list_user_push_tokens`, `get_user_push_token`, `create_or_replace_user_push_token`, `patch_user_token`, `delete_user_token`, `bulk_add_user_tokens` |
| Preferences, per user | `get_user_preferences`, `get_user_preference_topic`, `update_user_preference_topic`, `delete_user_preference_topic`, `bulk_update_user_preferences`, `bulk_replace_user_preferences` |
| Preferences, workspace | `list_preference_sections`, `create_preference_section`, `list_preference_topics`, `get_preference_topic`, `create_preference_topic`, `replace_preference_topic`, `archive_preference_topic`, `publish_preferences` |
| Digests | `list_digest_instances`, `release_digest` (whole schedule) |
| Lists and audiences | `list_lists`, `get_list`, `create_list`, `subscribe_user_to_list`, `unsubscribe_user_from_list`, `get_list_subscribers`, `list_audiences`, `get_audience`, `update_audience`, `list_audience_members` |
| Bulk | `create_bulk_job` (`message.event` is required) → `add_bulk_users` → `run_bulk_job`, in that order, then `get_bulk_job`, `list_bulk_users`. See [bulk.md](./bulk.md) |
| Tenants | `get_tenant`, `create_or_update_tenant`, `list_tenants`, `list_tenant_users`, `add_user_to_tenant`, `list_user_tenants`, `list_tenant_templates`, `update_tenant_preference` |
| Brands, routing, providers | `list_brands`, `get_brand`, `create_brand`, `update_brand`, `list_routing_strategies`, `create_routing_strategy`, `replace_routing_strategy`, `list_providers`, `create_provider`, `list_provider_catalog` |
| Other | `get_translation`, `update_translation`, `track_inbound_event`, `list_audit_events`, `invoke_automation_template`, `courier_installation_guide` |

See [Journeys](./journeys.md) for the node types and the create-then-replace ordering constraint.

## Error Handling

All tools return structured error responses:

```json
{
  "error": true,
  "status": 404,
  "message": "Profile not found"
}
```

| Status | Meaning |
|--------|---------|
| `400` | Bad request (missing or invalid parameters) |
| `403` | Missing or invalid API key |
| `404` | Resource not found |
| `429` | Rate limited |


## Known gaps

Check `tools/list` first; coverage grows as Courier ships. When a tool or parameter you need is not
there, use the SDK, CLI, or REST. Areas that have lagged the API:

| Need | Use instead |
|---|---|
| A topic's digest configuration (the `digest` object on topic create or replace) | `client.workspacePreferences.topics.create`/`replace`, see [digests.md](./digests.md#configure-a-topics-digest) |
| A user's digest schedule (`digest_schedule_id`) | `client.users.preferences.updateOrCreateTopic`, see [digests.md](./digests.md#per-recipient-schedule) |
| Releasing one recipient's digest | `client.workspacePreferences.topics.releaseDigest` or `courier workspace-preferences:topics release-digest` |

An absent tool is a possible gap, not proof the endpoint doesn't exist. Check the [API reference](https://www.courier.com/docs/api-reference/).

## Related

- [CLI](./cli.md) - Shell-based alternative for environments without MCP support
- [Quickstart](./quickstart.md) - Send your first notification with SDK, CLI, or curl
- [Reliability](./reliability.md) - Idempotency keys and retry patterns
- [Patterns](./patterns.md) - Reusable code patterns for common notification tasks

Documentation: [courier.com/docs/resources/mcp](https://www.courier.com/docs/resources/mcp)
