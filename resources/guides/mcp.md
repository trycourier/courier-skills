# Courier MCP Server

> **Last verified: 2026-04.** Tool count, installation UI paths, and JSON config shape can drift as Courier ships MCP updates or editors change their settings surface. If this file is older than **3 months**, spot-check the tool count and the Cursor/Claude Code installation snippets against https://www.courier.com/docs/tools/mcp (or fetch `https://www.courier.com/docs/llms.txt` and follow the MCP entry) before quoting specifics.

## Quick Reference

### Rules
- MCP provides structured tool access; agents discover tools automatically and call them with typed parameters
- Auth via `api_key` header; use the same API key from [Settings > API Keys](https://app.courier.com/settings/api-keys)
- Tools cover most of the Courier API (send, messages, profiles, lists, audiences, notifications, brands, automations, bulk, tenants, preferences, tokens, translations, inbound, audit). The exact count may change — call the MCP server's tool-list endpoint for the current list
- **Coverage gap vs. REST/CLI:** MCP currently exposes **read-only** access to notification templates (list/get content/get draft). Template **writes** (create, replace, publish, archive, versions, checks) are not in MCP yet — use the [CLI](./cli.md) or the REST API for those
- Prefer MCP when your editor supports it (Cursor, Claude Code, Claude Desktop, Windsurf, VSCode); fall back to [CLI](./cli.md) for shell-only environments or CI/CD
- MCP tools return structured JSON responses; errors include HTTP status code and message

### Practical setup guardrails

- Treat tool count as informative, not absolute: if the number changed, proceed as long as the tools you need are present.
- If a workflow requires template writes, switch to [CLI](./cli.md) or REST early instead of forcing MCP.
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

Both authenticate with the same `COURIER_API_KEY`. They overlap substantially but are not identical — MCP covers read operations on notification templates only, while the CLI (and REST) cover the full template lifecycle (create, publish, archive, versions, checks). Use CLI for template authoring and CI/CD; use MCP for agent-driven send, profile, list, tenant, preference, and audience workflows.

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

Or use the one-click install: [Install MCP Server](https://cursor.com/en/install-mcp?name=courier&config=eyJ1cmwiOiJodHRwczovL21jcC5jb3VyaWVyLmNvbSIsImhlYWRlcnMiOnsiYXBpX2tleSI6IlhYWFgifX0%3D) — after installing, open **Cursor Settings > MCP** and replace `XXXX` with your actual Courier API key.

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

### OpenAI Responses API

```javascript
import OpenAI from "openai";

const client = new OpenAI();

const response = await client.responses.create({
  model: "gpt-4o",
  input: "Look up the profile for user-123 and tell me their email",
  tools: [
    {
      type: "mcp",
      server_label: "courier",
      server_url: "https://mcp.courier.com",
      headers: { api_key: "YOUR_COURIER_API_KEY" },
      require_approval: "never",
    },
  ],
});
```

## Available Tools

Tools cover most of the Courier API, all backed by the official `@trycourier/courier` Node SDK with typed error handling. Notification template **writes** (create/replace/publish/archive/versions/checks) are not yet in MCP — use the [CLI](./cli.md) or REST. Call the MCP server's tool-list endpoint for the current count and names.

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

### Automations

| Tool | Description |
|------|-------------|
| `invoke_automation_template` | Invoke an automation from a template |
| `invoke_ad_hoc_automation` | Invoke an ad-hoc automation with inline steps |

### Bulk

| Tool | Description |
|------|-------------|
| `create_bulk_job` | Create a bulk job for multi-recipient sends |
| `add_bulk_users` | Add users to an existing bulk job |
| `run_bulk_job` | Trigger delivery for a bulk job |
| `get_bulk_job` | Get the status of a bulk job |
| `list_bulk_users` | List users in a bulk job |

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
| `track_inbound_event` | Track an inbound event that can trigger automations |

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
