# Courier CLI

## Quick Reference

### Rules
- CLI is for ad-hoc operations, debugging, and agent workflows; use SDKs for production app code
- Auth via `COURIER_API_KEY` env var; `--api-key` flag overrides per command
- All commands support `--format json` for machine-readable output
- Resource-based command structure: `courier [resource] <command> [flags]`
- One level of dot-notation for top-level nested args with inline JSON values: `--message.to '{"user_id":"abc"}'`. Two-level dots like `--message.to.user_id "abc"` are **not** supported; pass the full sub-object as a JSON string instead.
- Native binary (Go); no runtime dependencies

### When to Use CLI vs SDK

| Use CLI | Use SDK |
|---------|---------|
| Ad-hoc sends and testing | Production application code |
| Debugging delivery issues | Automated workflows in your app |
| Inspecting messages, profiles, logs | Sending from your backend |
| CI/CD smoke tests | Anything that needs error handling, retries, types |
| Agent workflows (Cursor, Claude Code) | Scheduled or event-driven sends |

### Common Commands

| Task | Command |
|------|---------|
| Send with a template | `courier send message --message.to '{"user_id":"user-123"}' --message.template "nt_01kmrbq6ypf25tsge12qek41r0"` |
| Send inline (no template) | `courier send message --message.to '{"email":"a@b.com"}' --message.content '{"title":"Title","body":"Body"}'` |
| Send to a list | `courier send message --message.to '{"list_id":"beta-testers"}' --message.template "nt_01kmrbq6ypf25tsge12qek41r0"` |
| List recent messages | `courier messages list` |
| Inspect a message | `courier messages retrieve --message-id "1-abc123"` |
| View delivery history | `courier messages history --message-id "1-abc123"` |
| View rendered content | `courier messages content --message-id "1-abc123"` |
| Create a user profile | `courier profiles create --user-id "user-123" --profile '{"email": "a@b.com"}'` |
| Get a user profile | `courier profiles retrieve --user-id "user-123"` |
| Check user preferences | `courier users:preferences retrieve --user-id "user-123"` |
| Trigger an automation | `courier automations:invoke invoke-by-template --template-id "onboarding-sequence" --recipient "user-123" --data '{}'` |
| Create a bulk job | `courier bulk create-job --message '{"event":"monthly-digest","template":"monthly-digest"}'` (`event` is required) |
| List templates | `courier notifications list` |

### Output Formats

| Format | Description |
|--------|-------------|
| `auto` | Human-readable for terminals, JSON for pipes |
| `json` | JSON output |
| `yaml` | YAML output |
| `pretty` | Colorized, indented JSON |
| `raw` | Raw response body |
| `jsonl` | Newline-delimited JSON (streaming) |

Filter with GJSON: `--transform "results.#.id"`

---

## Installation

**npm** (recommended):

```bash
npm install -g @trycourier/cli
```

Downloads a platform-specific binary via postinstall. No Node.js runtime needed after installation.

**Direct download**:

Download from [GitHub Releases](https://github.com/trycourier/courier-cli/releases) and add to your `PATH`.

Verify:

```bash
courier --version
```

## Authentication

Set the `COURIER_API_KEY` environment variable:

```bash
export COURIER_API_KEY="your-api-key"
```

Override per command with `--api-key`:

```bash
courier messages list --api-key "different-key"
```

## Inline Sends

Send without a pre-built template by passing content directly:

```bash
courier send message \
  --message.to '{"email":"alex@example.com"}' \
  --message.content '{"title":"New comment on your design file","body":"Sara left a comment on Homepage Redesign: '\''Love the new hero section.'\''"}'
```

Route across multiple channels with fallback:

```bash
courier send message \
  --message.to '{"email":"alex@example.com","phone_number":"+15551234567"}' \
  --message.content '{"title":"New login detected","body":"New login from {{city}}, {{country}}. If this wasn'\''t you, reset your password."}' \
  --message.data '{"city": "San Francisco", "country": "US"}' \
  --message.routing '{"method":"single","channels":["email","sms"]}'
```

`method: "single"` tries channels in order and stops at the first successful delivery. Use `"all"` only for critical notifications that must reach every channel.

## User Profiles

Create a profile so you can send by `user_id` instead of passing contact info every time:

```bash
courier profiles create \
  --user-id "user-123" \
  --profile '{"email": "alex@example.com", "phone_number": "+15551234567", "name": "Alex Chen"}'
```

Add custom attributes (merges with existing profile, won't overwrite contact info):

```bash
courier profiles create \
  --user-id "user-123" \
  --profile '{"custom": {"plan": "pro", "company": "Acme Corp", "locale": "en-US"}}'
```

Look up a profile:

```bash
courier profiles retrieve --user-id "user-123" --format json
```

## Lists and Bulk

**Send to a group via lists:**

```bash
courier lists update --list-id "beta-testers" --name "Beta Testers"
courier lists:subscriptions subscribe-user --list-id "beta-testers" --user-id "user-123"

courier send message \
  --message.to '{"list_id":"beta-testers"}' \
  --message.template "feature-announcement" \
  --message.data '{"feature": "Design Studio"}'
```

Target multiple lists with a pattern (e.g., all `eng.*` lists):

```bash
courier send message \
  --message.to '{"list_pattern":"eng.*"}' \
  --message.template "engineering-update"
```

**Bulk sends** for large audiences (product launches, digests):

```bash
courier bulk create-job \
  --message '{"event":"monthly-digest","template":"monthly-digest"}'

courier bulk add-users --job-id "job-abc" \
  --user '{"to":{"user_id":"user-1"},"data":{"highlights":12}}' \
  --user '{"to":{"user_id":"user-2"},"data":{"highlights":7}}'

courier bulk run-job --job-id "job-abc"
courier bulk retrieve-job --job-id "job-abc"
```

> The `event` field is **required** when creating a bulk job (same as the `event` field on `client.bulk.createJob`). Omitting it returns a 400. `event` can be a template alias/slug that also matches your `template`, or any string you use to identify the job. The `--user` flag is singular and repeatable; each value is a full `InboundBulkMessageUser` object (`{"to": { "user_id": ... }, "data": ...}`), not a bare `{"user_id": ...}`.

## Tenants, Automations, and Preferences

**Tenants** scope branding and preferences per customer organization (B2B):

```bash
courier tenants update \
  --tenant-id "acme-corp" \
  --name "Acme Corp" \
  --properties '{"brandId": "brand-acme"}'

courier users:tenants add-single --user-id "user-123" --tenant-id "acme-corp"

courier send message \
  --message.to '{"user_id":"user-123","tenant_id":"acme-corp"}' \
  --message.template "welcome-email"
```

> `courier tenants update` is an **upsert** — use it to both create and update a tenant. There is no separate `courier tenants create` command.

**Automations** trigger multi-step notification sequences (delays, conditions, batching):

```bash
courier automations:invoke invoke-by-template \
  --template-id "onboarding-sequence" \
  --recipient "user-123" \
  --data '{"userId": "user-123", "plan": "pro"}'

courier automations list
```

**Preferences** — check what a user has opted into or out of:

```bash
courier users:preferences retrieve --user-id "user-123" --format pretty

courier users:preferences retrieve-topic \
  --user-id "user-123" \
  --topic-id "marketing-updates"
```

## Debugging Workflow

Trace why a notification failed in four steps:

**1. Find the message:**

```bash
courier messages list --format json --transform "results.#(status=UNDELIVERABLE)"
```

`messages list` accepts the filter flags `--status`, `--recipient`, `--notification`, `--event`, `--tag`, `--tenant-id`, `--enqueued-after`, `--cursor`, and `--trace-id`. Note: the flag for looking up messages by a send's `requestId` is `--trace-id`, not `--request-id`. See the [next section](#debugging-list-bulk-sends-requestid-vs-message-id).

**2. Inspect the message:**

```bash
courier messages retrieve --message-id "1-abc123" --format json
```

**3. View delivery history:**

```bash
courier messages history --message-id "1-abc123" --format json
```

The history shows each routing step, provider attempt, and delivery status with timestamps.

**4. View rendered content:**

```bash
courier messages content --message-id "1-abc123" --format json
```

Shows the final content sent to the provider, after template variables and routing logic were applied. Useful for verifying what the recipient actually received.

> There is no `courier messages output` command; the rendered-content command is `courier messages content` (which maps to `client.messages.content(id)` in the SDK).

### Debugging list / bulk sends (requestId vs message_id)

For a single send (`to: { email }` / `to: { user_id }`), the `requestId` returned by `client.send.message` *is* the message ID — pass it straight to `courier messages retrieve --message-id "<requestId>"` and `client.messages.retrieve(requestId)`.

For **list**, **list-pattern**, **audience**, or **bulk** sends, the `requestId` is the *job* ID, which fans out to one message per recipient. Passing the job's requestId to `messages retrieve` returns `404 Message not found`. Instead:

```bash
# 1. From a list/bulk send, you have the job requestId (e.g. 1-69e16217-36dbd96d7abbe2ccc14cb989).
# 2. Find every per-recipient message the job generated:
courier messages list --trace-id "1-69e16217-36dbd96d7abbe2ccc14cb989" --format json

# 3. For each row, the `id` is the per-channel message ID:
courier messages list --trace-id "1-69e16217-36dbd96d7abbe2ccc14cb989" \
  --format json --transform "results.#.id"

# 4. Use those IDs with retrieve / history / content:
courier messages retrieve --message-id "1-abc123" --format json
courier messages history  --message-id "1-abc123" --format json
courier messages content  --message-id "1-abc123" --format json
```

In the SDKs the same distinction applies: `client.messages.list({ traceId: "<requestId>" })` (Node) / `client.messages.list(trace_id="<requestId>")` (Python) returns the per-recipient messages; each has an `id` you can pass to `client.messages.retrieve`.

For bulk jobs specifically, the job-level aggregates (`enqueued`, `received`, `failures`, `status`) are on `GET /bulk/{jobId}` (`client.bulk.retrieveJob` / `retrieve_job`), not on `messages.retrieve`.

## Machine-Readable Output

Every command supports `--format json`. Combine with `--transform` (GJSON syntax) to extract specific fields:

```bash
# Get just message IDs
courier messages list --format json --transform "results.#.id"

# Get the status of a specific message
courier messages retrieve --message-id "1-abc123" --format json --transform "status"

# List template names
courier notifications list --format json --transform "results.#.title"
```

## Zero-Config Agent Pattern

AI agents in Cursor, Claude Code, Codex, and similar environments can invoke the CLI directly via shell. No MCP server, API keys in code, or SDK setup required.

**Setup** (once per machine):

```bash
npm install -g @trycourier/cli
export COURIER_API_KEY="your-api-key"
```

**Then agents can run:**

```bash
courier send message \
  --message.to '{"user_id":"user-123"}' \
  --message.template "nt_01kmrbq6ypf25tsge12qek41r0" \
  --message.data '{"orderId": "12345"}'

courier messages list --format json
courier profiles retrieve --user-id "user-123" --format json
```

The `--format json` flag makes output parseable by agents without additional processing.

## CI/CD Integration

Use the CLI in automated pipelines for smoke tests during deployment:

```bash
export COURIER_API_KEY="$COURIER_TEST_KEY"

courier send message \
  --message.to '{"user_id":"smoke-test-user"}' \
  --message.template "welcome"
```

Store API keys as secrets in your CI provider (GitHub Actions secrets, GitLab CI variables, etc.).

## Global Flags

| Flag | Description |
|------|-------------|
| `--api-key` | Override `COURIER_API_KEY` for this command |
| `--base-url` | Use a custom API URL |
| `--format` | Output format (`auto`, `json`, `yaml`, `pretty`, `raw`, `jsonl`) |
| `--transform` | Filter output with GJSON syntax |
| `--debug` | Show HTTP request/response details |
| `--version`, `-v` | Print CLI version |
| `--help` | Show command usage |

## Related

- [Quickstart](./quickstart.md) - Send your first notification
- [Patterns](./patterns.md) - Reusable code patterns (includes CLI examples)
- [Reliability](./reliability.md) - Idempotency and retry logic
- [Multi-Channel](./multi-channel.md) - Routing strategies

Source code: [trycourier/courier-cli](https://github.com/trycourier/courier-cli)
Documentation: [courier.com/docs/tools/cli](https://www.courier.com/docs/tools/cli)
