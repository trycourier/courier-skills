# Courier CLI

## Quick Reference

### Rules
- CLI is for ad-hoc operations, debugging, and agent workflows; use SDKs for production app code
- Auth via `COURIER_API_KEY` env var; `--api-key` flag overrides per command
- All commands support `--format json` for machine-readable output
- Resource-based command structure: `courier [resource] <command> [flags]`
- Dot notation for nested args: `--message.to.user_id "abc"`
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
| Send a message | `courier send message --message.to.user_id "user-123" --message.template "TEMPLATE"` |
| List recent messages | `courier messages list` |
| Inspect a message | `courier messages retrieve --message-id "1-abc123"` |
| View delivery history | `courier messages history --message-id "1-abc123"` |
| Get a user profile | `courier profiles retrieve --user-id "user-123"` |
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

## Debugging Workflow

Trace why a notification failed in three steps:

**1. Find the message:**

```bash
courier messages list --format json --transform "results.#(status=UNDELIVERED)"
```

**2. Inspect the message:**

```bash
courier messages retrieve --message-id "1-abc123" --format json
```

**3. View delivery history:**

```bash
courier messages history --message-id "1-abc123" --format json
```

The history shows each routing step, provider attempt, and delivery status with timestamps.

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
  --message.to.user_id "user-123" \
  --message.template "ORDER_CONFIRMATION" \
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
  --message.to.user_id "smoke-test-user" \
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
