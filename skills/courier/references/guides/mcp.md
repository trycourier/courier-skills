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

Cheaper still, when you already know the exact page: append `.md` to any docs URL (`https://www.courier.com/docs/platform/journeys/nodes/batch.md`), plain HTTP, ~1–2k tokens, no MCP connection needed. Bad paths return a real `404`.

---

## API MCP Server

> **Last verified: 2026-07.** The tool inventory below is a snapshot. Tool names, coverage, installation UI paths, and JSON config shape all drift as Courier ships MCP updates and editors change their settings surface. **Always prefer the server's live tool list over this file.** If this file is older than **3 months**, re-verify against https://www.courier.com/docs/tools/mcp before quoting specifics, and note that a tool being advertised does not guarantee the endpoint behind it still exists.

## Quick Reference

### Rules
- MCP provides structured tool access; agents discover tools automatically and call them with typed parameters
- Auth via `api_key` header; use the same API key from [Settings > API Keys](https://app.courier.com/settings/api-keys)
- Tools cover essentially the whole Courier API. Send, messages, profiles, lists, audiences, notifications (**including writes**), journeys (**including writes**), brands, tenants, preferences, tokens, translations, digests, inbound, audit. The exact count changes as Courier ships; **call the MCP server's tool-list endpoint for the current list** rather than trusting any number written down here
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
4. Verify your needed feature is in MCP; if not (for example template publish/create), route to CLI/REST.
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

Tools cover essentially the whole Courier API, all backed by the official `@trycourier/courier` Node SDK with typed error handling, including notification template writes (create/replace/publish/archive/versions/checks) and the full journey lifecycle.

> The inventory below is a **snapshot for orientation, not a contract.** Call the MCP server's tool-list endpoint for the authoritative names and coverage. Where this file and the live server disagree, the server is right.

### Send

| Tool | Description |
|------|-------------|
| `send_message` | Send a message using inline title and body content |
| `send_message_template` | Send a message using a notification template |
| `send_message_to_list` | Send inline content to all subscribers of a list |
| `send_message_to_list_template` | Send a template to all subscribers of a list |

### Messages

| Tool | Description |
|------|-------------|
| `list_messages` | List sent messages with filters (status, recipient, provider, tags) |
| `get_message` | Get full details and delivery status of a message |
| `get_message_content` | Get the rendered HTML, text, and subject of a sent message |
| `get_message_history` | Get the event history for a message (enqueued, sent, delivered, etc.) |
| `cancel_message` | Cancel a message currently being delivered |

### Profiles

| Tool | Description |
|------|-------------|
| `get_user_profile_by_id` | Get a user profile by ID |
| `create_or_merge_user` | Create or merge values into an existing profile |
| `replace_profile` | Fully replace a user profile (PUT) |
| `delete_profile` | Delete a user profile |
| `get_user_list_subscriptions` | Get all list subscriptions for a user |
| `subscribe_user_to_lists` | Subscribe a user to one or more lists |
| `delete_user_list_subscriptions` | Remove all list subscriptions for a user |

### Lists

| Tool | Description |
|------|-------------|
| `list_lists` | Get all lists, optionally filtered by pattern |
| `get_list` | Get a list by ID |
| `get_list_subscribers` | Get all subscribers of a list |
| `create_list` | Create or update a list |
| `subscribe_user_to_list` | Subscribe a user to a list |
| `unsubscribe_user_from_list` | Unsubscribe a user from a list |

### Audiences

| Tool | Description |
|------|-------------|
| `get_audience` | Get an audience by ID |
| `list_audiences` | List all audiences |
| `list_audience_members` | List members of an audience |
| `update_audience` | Create or update an audience with a filter definition |
| `delete_audience` | Delete an audience |

### Bulk

| Tool | Description |
|------|-------------|
| `create_bulk_job` | Create a bulk job (`message.event` is required) |
| `add_bulk_users` | Ingest users into an existing bulk job |
| `run_bulk_job` | Trigger delivery for a bulk job |
| `get_bulk_job` | Get a job's status and counts |
| `list_bulk_users` | List the users ingested into a job, with their per-recipient status |

Workflow order matters: `create_bulk_job` → `add_bulk_users` → `run_bulk_job`. See
[bulk.md](./bulk.md) for the payload shapes and gotchas.

### Notifications

| Tool | Description |
|------|-------------|
| `list_notifications` | List notification templates |
| `get_notification_content` | Get published content blocks of a template |
| `get_notification_draft_content` | Get draft content blocks of a template |

### Brands

| Tool | Description |
|------|-------------|
| `create_brand` | Create a new brand |
| `get_brand` | Get a brand by ID |
| `list_brands` | List all brands |

### Auth & Tokens

| Tool | Description |
|------|-------------|
| `generate_jwt_for_user` | Generate a JWT token for client-side SDK auth |
| `list_user_push_tokens` | List all push/device tokens for a user |
| `get_user_push_token` | Get a specific push token |
| `create_or_replace_user_push_token` | Create or replace a push token |

### Journeys

MCP has full journey coverage, including writes. Prefer these over hand-rolled REST.

| Tool | Description |
|------|-------------|
| `create_journey` | Create a journey (DRAFT by default; send nodes are not allowed on create) |
| `replace_journey` | Replace a journey, this is how you add send nodes after templates exist |
| `publish_journey` | Publish a draft journey, making it live |
| `invoke_journey` | Start a journey run for a user |
| `cancel_journey` | Cancel an in-flight run |
| `archive_journey` / `get_journey` / `list_journeys` / `list_journey_versions` | Journey lifecycle and inspection |
| `create_journey_template` / `replace_journey_template` / `publish_journey_template` / `archive_journey_template` | Journey-scoped template writes |
| `get_journey_template` / `get_journey_template_content` / `put_journey_template_content` / `put_journey_template_locale` | Journey-scoped template content and locales |

See [Journeys](./journeys.md) for the node types, the create-then-replace ordering constraint, and the full DAG shape.

### Digests

| Tool | Description |
|------|-------------|
| `list_digest_instances` | Inspect events accumulated for a user against a digest schedule (`sch/{uuid}`) |
| `release_digest` | Release an accumulated digest early |

### Tenants

| Tool | Description |
|------|-------------|
| `get_tenant` | Get a tenant by ID |
| `create_or_update_tenant` | Create or replace a tenant |
| `list_tenants` | List all tenants |
| `delete_tenant` | Delete a tenant |

### Users

| Tool | Description |
|------|-------------|
| `get_user_preferences` | Get a user's notification preferences |
| `update_user_preference_topic` | Update a user's preference for a subscription topic |
| `list_user_tenants` | List all tenants a user belongs to |
| `add_user_to_tenant` | Add a user to a tenant |
| `remove_user_from_tenant` | Remove a user from a tenant |

### Translations

| Tool | Description |
|------|-------------|
| `get_translation` | Get a translation for a locale |
| `update_translation` | Create or update a translation |

### Inbound

| Tool | Description |
|------|-------------|
| `track_inbound_event` | Track an inbound event that can trigger a journey |

### Audit Events

| Tool | Description |
|------|-------------|
| `get_audit_event` | Get a specific audit event |
| `list_audit_events` | List audit events |

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
| `401` | Invalid API key |
| `404` | Resource not found |
| `429` | Rate limited |

## Related

- [CLI](./cli.md) - Shell-based alternative for environments without MCP support
- [Quickstart](./quickstart.md) - Send your first notification with SDK, CLI, or curl
- [Reliability](./reliability.md) - Idempotency keys and retry patterns
- [Patterns](./patterns.md) - Reusable code patterns for common notification tasks

Documentation: [courier.com/docs/tools/mcp](https://www.courier.com/docs/tools/mcp)
