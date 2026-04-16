# Quickstart

Send your first notification with Courier using the SDK, CLI, or curl.

## Quick Reference

### Rules
- You need a Courier API key from [Settings > API Keys](https://app.courier.com/settings/api-keys)
- Use a test environment key for development — copy the "Test" key from Settings
- Inbox works out of the box with no provider setup. Email works out of the box in **fresh** test workspaces (Courier provisions a built-in email provider), but if the workspace's email routing list references providers that aren't currently installed you'll see `status: UNROUTABLE` with `reason: PROVIDER_ERROR` — add or remove the referenced providers in [Integrations](https://app.courier.com/integrations). SMS, push, and other channels always require adding a provider first.
- All tools read `COURIER_API_KEY` from the environment (SDK, CLI, curl)
- Both `import Courier from "@trycourier/courier"` (default export) and `import { Courier } from "@trycourier/courier"` (named export) work — the named export is `Courier`, not `CourierClient`
- Always use idempotency keys for transactional sends in production
- Check delivery status via the Messages API or Courier dashboard

### Addressing Modes (the `to` field)
| Mode | Syntax | When to use |
|------|--------|-------------|
| Direct email | `to: { email: "jane@example.com" }` | Quick send, no profile needed |
| Direct phone | `to: { phone_number: "+15551234567" }` | SMS/WhatsApp, no profile needed |
| User profile | `to: { user_id: "user-123" }` | User exists in Courier with stored contact info |
| Multi-tenant | `to: { user_id: "user-123", tenant_id: "acme-corp" }` | B2B apps with per-tenant branding |
| List | `to: { list_id: "beta-testers" }` | Send to a group of users |
| List pattern | `to: { list_pattern: "eng.*" }` | Send to all lists matching a prefix |

If a `user_id` has no contact info for the target channel, the send is skipped for that channel (no error). With `method: "single"`, it falls through to the next channel in the array.

### Steps
1. Get an API key
2. Install SDK or CLI
3. Send a message
4. Check delivery status

---

## 1. Get an API Key

Create an API key in your [Courier Settings](https://app.courier.com/settings/api-keys). Use a test key for development.

## 2. Install and Authenticate

**TypeScript/Node.js:**

```bash
npm install @trycourier/courier
export COURIER_API_KEY="your-api-key"
```

**Python:**

```bash
pip install trycourier
export COURIER_API_KEY="your-api-key"
```

**CLI:**

```bash
npm install -g @trycourier/cli
export COURIER_API_KEY="your-api-key"
```

The SDK, CLI, and curl all read `COURIER_API_KEY` from the environment. The examples below use `$COURIER_API_KEY`.

You can also pass the key explicitly in code:

```typescript
const client = new Courier({ apiKey: "your-api-key" });
// `authorizationToken` is accepted as an alias in Node for legacy callers.
```

```python
client = Courier(api_key="your-api-key")
# Python's Stainless-generated client accepts `api_key=` only —
# `authorization_token=` raises TypeError.
```

## 3. Send a Message

### TypeScript

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

const response = await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    content: {
      title: "Hello from Courier",
      body: "This is your first notification!"
    }
  }
});

console.log(response.requestId);
```

### Python

```python
from courier import Courier

client = Courier()

response = client.send.message(
    message={
        "to": {"email": "jane@example.com"},
        "content": {
            "title": "Hello from Courier",
            "body": "This is your first notification!",
        },
    }
)

print(response.request_id)
```

### CLI

```bash
courier send message \
  --message.to '{"email":"jane@example.com"}' \
  --message.content '{"title":"Hello from Courier","body":"This is your first notification!"}'
```

### curl

```bash
curl -X POST https://api.courier.com/send \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "to": { "email": "jane@example.com" },
      "content": {
        "title": "Hello from Courier",
        "body": "This is your first notification!"
      }
    }
  }'
```

## 4. Check Delivery Status

Use the `requestId` from the send response to check delivery status.

The `requestId` returned by `send.message` doubles as the message ID for single sends, so you can pass it directly to `messages.retrieve` (and to the CLI's `--message-id` flag). For list and bulk sends this is not true — see the [CLI debugging note](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id).

Common values you'll see in `message.status`: `ENQUEUED` → `ROUTED` → `SENT` → `DELIVERED` on the happy path; `UNROUTABLE` (routing failed — no channel/provider), `UNDELIVERABLE` (every provider attempt failed), `FAILED` (platform error). Final states can take seconds after send.

### TypeScript

```typescript
// `response` is the result of `client.send.message(...)` from step 3.
const message = await client.messages.retrieve(response.requestId);
console.log(message.status); // ENQUEUED | ROUTED | SENT | DELIVERED | UNROUTABLE | UNDELIVERABLE | FAILED
```

### Python

```python
# `response` is the result of `client.send.message(...)` from step 3.
message = client.messages.retrieve(response.request_id)
print(message.status)
```

### CLI

For single sends, the `requestId` from `courier send message` is also the message ID — pass it to `--message-id`:

```bash
courier messages retrieve --message-id "REQUEST_ID" --format json
```

### curl

```bash
curl https://api.courier.com/messages/REQUEST_ID \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

## 5. Send with a Template

Templates are designed in the [Courier Designer](https://app.courier.com/designer). Reference them by template ID (`nt_...`).
Use your own workspace template IDs in production; IDs shown below are examples.

### TypeScript

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbq6ypf25tsge12qek41r0",
    data: { orderId: "12345", total: "$99.00" }
  }
});
```

### Python

```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbq6ypf25tsge12qek41r0",
        "data": {"orderId": "12345", "total": "$99.00"},
    }
)
```

### CLI

```bash
courier send message \
  --message.to '{"user_id":"user-123"}' \
  --message.template "nt_01kmrbq6ypf25tsge12qek41r0" \
  --message.data '{"orderId": "12345", "total": "$99.00"}'
```

## Common First-Run Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Missing or invalid API key | Check `COURIER_API_KEY` env var; verify key in [Settings](https://app.courier.com/settings/api-keys) |
| 400 Bad Request | Malformed message payload | Verify `to`, `content`/`template` structure; check required fields |
| 404 Not Found | Template ID doesn't exist | Use the correct `nt_...` template ID from the Designer/API; check environment (test vs production) |
| Message sent but not delivered | No provider configured for channel | Email works in fresh test workspaces without setup; otherwise, add a provider in [Integrations](https://app.courier.com/integrations) |
| Sent to `user_id` but nothing happened | User profile missing contact info | Create profile with `email`/`phone_number` first, or send directly with `to: { email: "..." }` |
| `status: UNROUTABLE`, `reason: PROVIDER_ERROR` | Routing list references a provider that isn't installed. Error string like `"No provider(s) resend in the list of message channel provider(s): postmark."` means the routing has `resend` listed but only `postmark` is installed (or vice versa). | Install the referenced provider in [Integrations](https://app.courier.com/integrations), or edit the channel's routing list to remove it. |
| `status: UNROUTABLE` with no provider error | No channel in `routing.channels` has a provider the user can reach (no contact info, no installed provider, or all opted out via preferences) | Verify `to`, `routing.channels`, installed providers, and user preferences. |
| `404` from `messages.retrieve` for a list/bulk send | You passed the job-level `requestId`, which isn't the per-recipient message ID | For list/bulk sends, look up per-recipient message IDs via `courier messages list --trace-id "<requestId>"`. See [CLI debugging](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id). |

## What's Next

| Goal | Guide |
|------|-------|
| Send via multiple channels (email, SMS, push) | [Multi-Channel](./multi-channel.md) |
| Add idempotency keys and retry logic | [Reliability](./reliability.md) |
| Manage user notification preferences | [Preferences](./preferences.md) |
| Use the CLI for debugging and agent workflows | [CLI](./cli.md) |
| Build a specific notification type | [Catalog](./catalog.md) |

## Related

- [Email](../channels/email.md) - Email deliverability and SPF/DKIM/DMARC
- [SMS](../channels/sms.md) - SMS setup and 10DLC
- [Push](../channels/push.md) - Push notification setup
- [Patterns](./patterns.md) - Reusable code patterns
