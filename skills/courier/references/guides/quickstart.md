# Quickstart

Send your first notification with Courier using the SDK, CLI, or curl.

**Contents:** [Quick Reference](#quick-reference) · [1. Get an API Key](#1-get-an-api-key) · [2. Install and Authenticate](#2-install-and-authenticate) · [3. Send a Message](#3-send-a-message) · [4. Check Delivery Status](#4-check-delivery-status) · [5. Send with a Template](#5-send-with-a-template) · [Common First-Run Errors](#common-first-run-errors) · [Environments](#environments) · [What's Next](#whats-next) · [Related](#related)

## Quick Reference

### Rules
- You need a Courier API key from [Platform → API Keys](https://app.courier.com/settings/api-keys)
- Use a test environment key for development: copy the Test key from [Platform → API Keys](https://app.courier.com/~/test/platform/api-keys)
- Inbox works without setup: the `courier` provider is preinstalled in Production and Test (a custom environment, or a deleted provider, needs it added, see [inbox.md](../channels/inbox.md#setup)). Email works without setup only with a Test key and only to your sign-up address (the Courier Test Email Provider); any other address, or a Production key, needs your own provider. SMS, push, and other channels always need a provider first.
- All tools read `COURIER_API_KEY` from the environment (SDK, CLI, curl)
- Both `import Courier from "@trycourier/courier"` (default export) and `import { Courier } from "@trycourier/courier"` (named export) work, the named export is `Courier`, not `CourierClient`

### Addressing Modes (the `to` field)
| Mode | Syntax | When to use |
|------|--------|-------------|
| Direct email | `to: { email: "jane@example.com" }` | Quick send, no profile needed |
| Direct phone | `to: { phone_number: "+15551234567" }` | SMS/WhatsApp, no profile needed |
| User profile | `to: { user_id: "user-123" }` | User exists in Courier with stored contact info |
| Multi-tenant | `to: { user_id: "user-123", context: { tenant_id: "acme-corp" } }` | B2B apps with per-tenant branding. `tenant_id` directly beside `user_id` is a `400` |
| List | `to: { list_id: "beta-testers" }` | Send to a group of users |
| List pattern | `to: { list_pattern: "eng.*" }` | Send to all lists matching a prefix |
| Audience | `to: { audience_id: "active-trials" }` | A filter whose membership Courier stores and keeps current |
| Array | `to: [{ user_id: "a" }, { email: "b@example.com" }]` | Up to **500** recipients; above that `400 message.to has N recipients. Max is 500`, so use a list, an audience or [bulk](./bulk.md) |

If a `user_id` has no contact info for a channel, Courier skips that channel's providers and the log shows `INCOMPLETE_PROFILE_DATA`. With `method: "single"`, it falls through to the next channel. If no channel can reach the user, the message ends `UNROUTABLE`. The send call itself doesn't error.

---

## 1. Get an API Key

Create an API key in [Platform → API Keys](https://app.courier.com/settings/api-keys). Use a test key for development.

## 2. Install and Authenticate

```bash
npm install @trycourier/courier   # Node.js
pip install trycourier            # Python
npm install -g @trycourier/cli    # CLI
export COURIER_API_KEY="your-api-key"
```

The SDK, CLI, and curl all read `COURIER_API_KEY`. To pass the key in code instead: `new Courier({ apiKey: "..." })` (Node) or `Courier(api_key="...")` (Python).

## 3. Send a Message

With a Test key, replace `jane@example.com` with the address you signed up with. The built-in provider delivers nowhere else.

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

Python: the same call with `message={...}`, then `response.request_id`. CLI: `courier send message --message.to '{"email":"jane@example.com"}' --message.content '{"title":"Hello from Courier","body":"This is your first notification!"}'`. curl: `POST https://api.courier.com/send` with `Authorization: Bearer $COURIER_API_KEY` and the same `{ "message": … }` JSON body.

## 4. Check Delivery Status

Use the `requestId` from the send response to check delivery status.

The `requestId` returned by `send.message` doubles as the message ID for single sends, so you can pass it directly to `messages.retrieve` (and to the CLI's `--message-id` flag). For list and bulk sends this is not true. See the [CLI debugging note](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id).

`ENQUEUED` → `ROUTED` → `SENT` → `DELIVERED` is the happy path; `UNROUTABLE` and `UNDELIVERABLE` are the terminal failures, and final states can take seconds. Full glossary in [reliability.md](./reliability.md#message-status-glossary).

```typescript
const message = await client.messages.retrieve(response.requestId); // `response` from step 3
console.log(message.status);
```

Python: `client.messages.retrieve(response.request_id)`. CLI: `courier messages retrieve --message-id "REQUEST_ID" --format json`. curl: `GET https://api.courier.com/messages/REQUEST_ID` with the bearer header.

## 5. Send with a Template

Templates are designed in [Design Studio](https://app.courier.com/designer). Send one by passing `template` (its `nt_...` ID or an alias) and `data` in place of `content`, exactly as in SKILL.md's [Canonical SDK Shape](../../SKILL.md#canonical-sdk-shape). IDs are workspace-specific, so use your own. CLI: `courier send message --message.to '{"user_id":"user-123"}' --message.template "nt_..." --message.data '{"orderId":"12345"}'`.

## Common First-Run Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 404 Not Found on send | The template ID doesn't exist in this environment | Use the `nt_...` ID or alias from the same environment (Test vs Production) |
| Sent but not delivered | No provider for the channel, or a Test email to an address other than your sign-up address | Add a provider in [Integrations](https://app.courier.com/integrations) |
| `status: UNROUTABLE`, `reason: PROVIDER_ERROR` | The routing list references a provider that isn't installed. `error` names it, e.g. `"None of provider(s) twilio,slack is configured for channel email."` The wording varies by release, so branch on `reason` and read `error` | Install the provider, or remove it from the channel's routing list |
| `status: UNROUTABLE`, no provider error | No channel in `routing.channels` can reach the user (no contact info, no installed provider, or opted out) | Check `to`, `routing.channels`, installed providers, and preferences; create the profile with `email`/`phone_number`, or send to `{ email }` directly |
| `UNROUTABLE` on an inbox send with no `reason` and no `error`, or `"No provider(s) courier ... : undefined"` | The `courier` provider is missing, or the template has no routing strategy | See [inbox.md](../channels/inbox.md#troubleshooting) |
| `404` from `messages.retrieve` after a list/audience send | The `requestId` is the job, not a message ID | Retrieve `<requestId>:<user_id>`, see [CLI debugging](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id) |

## Environments

A workspace holds several environments (Production, Test, and custom ones such as Staging), and the API key on each request picks the environment. Each one has its own templates, brands, tags, journeys, subscription topics, provider integrations, API keys, logs and metrics. Team members, their roles, tracking settings and billing are shared.

- **Promote a template with Migrate assets.** In the templates page, open the template's menu and choose **Migrate assets**. Courier copies the template with its brands, tags, subscription topics, test events and event maps. Provider integrations aren't copied, so set them up in the destination before you send. To do the same from code, see [templates-as-code.md](./templates-as-code.md).
- **Set up dependencies in Production first.** A send whose template references a brand, tag or topic missing from that environment fails there, even though it worked in Test.
- For staging, use a custom environment in the same workspace. Separate workspaces are for separate billing.

## What's Next

Fallback across channels: [Multi-Channel](./multi-channel.md). Idempotency and retries: [Reliability](./reliability.md). Preferences: [Preferences](./preferences.md). Debugging: [CLI](./cli.md). A specific notification type: [Transactional](../transactional.md). Multi-step sequences: [Journeys](./journeys.md).

## Related

[Email](../channels/email.md) · [SMS](../channels/sms.md) · [Push](../channels/push.md) · [Patterns](./patterns.md)
