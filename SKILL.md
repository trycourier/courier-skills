---
name: courier-notification-skills
description: Use when building notifications with Courier across email, SMS, push, in-app inbox, Slack, Teams, or WhatsApp. Covers transactional messages (password reset, OTP, orders, billing), growth notifications (onboarding, engagement, referral), multi-channel routing, preferences and topics, reliability and webhooks, template CRUD and Elemental content, routing strategies, provider configuration, the Courier CLI and MCP server, and migrations from Knock, Novu, or other notification systems.
---

# Courier Notification Skills

Guidance for building deliverable and engaging notifications across all channels.

## How to Use This Skill

1. **Identify the task** — What channel, notification type, or cross-cutting concern is the user working on?
2. **Read only what's needed** — Use the routing tables below to find the 1-2 files relevant to the task. Do NOT read all files.
3. **Check for live docs** — For current API signatures and SDK methods, fetch `https://www.courier.com/docs/llms.txt`
4. **Synthesize before coding** — Plan the complete implementation (channels, routing, error handling) before writing code.
5. **Apply the rules** — Each resource file starts with a "Quick Reference" section containing hard rules. Treat these as constraints, not suggestions.
6. **Check universal rules** — Before generating any notification code, verify it doesn't violate the Universal Rules below.

## Handling Vague Requests

If the user's request doesn't clearly map to a specific channel, notification type, or guide, **ask clarifying questions before reading any resource files**. Don't guess — a wrong routing wastes time and produces irrelevant code.

**Ask these questions as needed:**

1. **What channel?** — "Which channel are you sending through: email, SMS, push, in-app, Slack, Teams, or WhatsApp?"
2. **What type?** — "Is this a transactional notification (triggered by a user action, like a password reset or order confirmation) or a marketing/growth notification (sent proactively, like a feature announcement)?"
3. **New or existing?** — "Are you starting from scratch, or do you have existing Courier code? If existing, what SDK packages do you have installed?"
4. **What language?** — "Are you using TypeScript/Node.js, Python, or another language?"

You don't need to ask all four — just the ones needed to route to the right 1-2 files. If the request is clearly about a specific topic (e.g., "help me with SMS"), skip the questions and go directly to the relevant resource.

**Routing consequences of question 3 ("new or existing"):**

| Answer | Skip | Load |
|--------|------|------|
| New to Courier / no existing code | (nothing) | [quickstart.md](./resources/guides/quickstart.md) + the relevant channel or type file |
| Existing — has `@trycourier/courier` or `trycourier` installed | `quickstart.md` install + env-setup sections | Jump directly to channel or type file; assume `client` is constructed. Offer `courier messages list` as a one-line health check if useful. |
| Existing — Inbox v7 (`@trycourier/react-*`) | v8 guidance | See "Courier Inbox Version Detection" block below, then [inbox-v7-legacy.md](./resources/channels/inbox-v7-legacy.md) |

## Canonical SDK Shape

Before you write or evaluate any Courier code, ground it in this shape. If anything in a file below appears to contradict it, trust this block and fetch live docs to resolve — do **not** paste the contradicting snippet.

**Node.js (`@trycourier/courier`, Stainless-generated):**

```typescript
import Courier from "@trycourier/courier";

// Reads process.env.COURIER_API_KEY by default
const client = new Courier();

await client.send.message({
  message: {
    to: { user_id: "user-123" },           // or { email }, { phone_number }, { list_id }, { tenant_id }, etc.
    template: "nt_01kmrbq6ypf25tsge12qek41r0", // OR content: { title, body } / { version, elements }
    data: { /* merge variables */ },
  },
}, {
  // Pass the Idempotency-Key via headers. Always set it explicitly here —
  // that is the one path guaranteed to be sent to the API across SDK
  // versions. Verify against your installed SDK version before relying on
  // any other `idempotencyKey` request option.
  headers: { "Idempotency-Key": "order-confirmation-12345" },
});
```

**Python (`trycourier`, Stainless-generated):**

```python
from courier import Courier

# Reads COURIER_API_KEY from env by default
client = Courier()

client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbq6ypf25tsge12qek41r0",
        "data": {},
    },
    # Pass the Idempotency-Key via extra_headers. Python does not accept
    # idempotency_key= as a keyword argument — the header is the only way.
    extra_headers={"Idempotency-Key": "order-confirmation-12345"},
)
```

**Method naming quick lookup (generated SDKs — both SDKs follow the same structure, Node = camelCase, Python = snake_case):**

| Operation | Node | Python |
|-----------|------|--------|
| Send a message | `client.send.message({ message })` | `client.send.message(message=...)` |
| Create a template | `client.notifications.create({ notification, state })` → returns `{ id, name, content, … }` at top level | `client.notifications.create(notification=..., state=...)` → `response.id` |
| Publish a template | `client.notifications.publish(templateId)` | `client.notifications.publish(template_id)` |
| Retrieve a message | `client.messages.retrieve(id)` | `client.messages.retrieve(id)` |
| List messages | `client.messages.list({ ... })` | `client.messages.list(...)` |
| Subscribe a user to a list (additive) | `client.lists.subscriptions.subscribeUser(userId, { list_id })` | `client.lists.subscriptions.subscribe_user(user_id, list_id=...)` |
| Replace a list's subscribers | `client.lists.subscriptions.subscribe(listId, { recipients })` | `client.lists.subscriptions.subscribe(list_id, recipients=...)` |
| Create/replace a tenant | `client.tenants.update(tenantId, body)` | `client.tenants.update(tenant_id, ...)` |
| Add a user to a tenant | `client.users.tenants.addSingle(tenantId, { user_id })` | `client.users.tenants.add_single(tenant_id, user_id=...)` |
| Create a bulk job | `client.bulk.createJob({ message: { event } })` (event required) | `client.bulk.create_job(message={"event": ...})` |
| Create/update a profile (merge) | `client.profiles.create(userId, { profile })` | `client.profiles.create(user_id, profile=...)` |
| Get a user's preferences | `client.users.preferences.retrieve(userId)` | `client.users.preferences.retrieve(user_id)` |
| Update a user's preference for a topic | `client.users.preferences.updateOrCreateTopic(topicId, { user_id, topic: { status, ... } })` | `client.users.preferences.update_or_create_topic(topic_id, user_id=..., topic=...)` |
| Register a user's device token | `client.users.tokens.addSingle(token, { user_id, provider_key, device })` | `client.users.tokens.add_single(token, user_id=..., provider_key=..., device=...)` |
| Trigger an automation from a template | `client.automations.invoke.invokeByTemplate(templateId, { recipient, data })` | `client.automations.invoke.invoke_by_template(template_id, recipient=..., data=...)` |
| Trigger an ad-hoc automation | `client.automations.invoke.invokeAdHoc({ recipient, automation })` | `client.automations.invoke.invoke_ad_hoc(recipient=..., automation=...)` |
| Create a routing strategy | `client.routingStrategies.create({ name, routing, channels?, providers? })` → returns `{ id: "rs_...", ... }` | `client.routing_strategies.create(name=..., routing=..., ...)` |
| Replace a routing strategy (full PUT) | `client.routingStrategies.replace(id, { name, routing, ... })` | `client.routing_strategies.replace(id, name=..., routing=..., ...)` |
| Configure a provider | `client.providers.create({ provider, settings, title?, alias? })` | `client.providers.create(provider=..., settings=..., ...)` |
| List provider catalog (required `settings` schema) | `client.providers.catalog.list({ keys?, name?, channel? })` | `client.providers.catalog.list(keys=..., channel=...)` |
| Cancel a message | `client.messages.cancel(messageId)` | `client.messages.cancel(message_id)` |
| Retrieve a template | `client.notifications.retrieve(templateId)` | `client.notifications.retrieve(template_id)` |
| List templates | `client.notifications.list()` | `client.notifications.list()` |
| Replace a template (full PUT) | `client.notifications.replace(templateId, { notification, state })` | `client.notifications.replace(template_id, notification=..., state=...)` |
| Archive a template | `client.notifications.archive(templateId)` | `client.notifications.archive(template_id)` |
| Get published template content | `client.notifications.retrieveContent(templateId)` | `client.notifications.retrieve_content(template_id)` |

> The table above covers the most common operations. [templates.md](./resources/guides/templates.md), [routing-strategies.md](./resources/guides/routing-strategies.md), and [providers.md](./resources/guides/providers.md) each contain their own complete SDK shape tables for CRUD on their respective resources (including `list`, `retrieve`, `replace`, `archive`).

**Shapes that do NOT exist (do not invent them):**

- `client.messages.archive(...)` — archive is REST-only: `POST /messages/{id}/archive`. Note: `client.notifications.archive(id)` and `client.routingStrategies.archive(id)` / `client.providers.archive(id)` DO exist — this restriction is specific to the messages namespace.
- `client.tenants.createOrReplace(...)` — use `client.tenants.update`
- `client.lists.subscribe(listId, userId)` — use `subscriptions.subscribeUser` or `subscriptions.subscribe`
- Bulk `createJob({ message: { template } })` without `event` — `event` is required
- `client.users.preferences.update(...)` — use `client.users.preferences.updateOrCreateTopic(topicId, { user_id, topic })`.
- `client.automations.invoke(templateId, ...)` — the real shape is `client.automations.invoke.invokeByTemplate(...)` or `client.automations.invoke.invokeAdHoc(...)`.
- `client.routing.create(...)` / `client.strategies.*` — the real namespace is `client.routingStrategies.*` (Node) / `client.routing_strategies.*` (Python).
- `client.integrations.*` — there is no `integrations` namespace; provider configurations live under `client.providers.*` and the provider type catalog under `client.providers.catalog.*`.

**Shapes that exist but should not be the default:**

- `client.profiles.update(userId, { patch: [...] })` — this DOES exist and applies a JSON Patch (RFC 6902). Use it only when the user specifically needs atomic field-level ops (`add`/`remove`/`replace`/`test` on specific paths). For the common "merge these fields into the profile" case, use `client.profiles.create(userId, { profile })` (POST, deep-merge).
- `client.profiles.replace(userId, { profile })` — this DOES exist and is a full PUT that overwrites the profile. Use it only when you need to reset a profile to a known-good state. For everyday writes, `client.profiles.create` (merge) is safer because it won't silently drop fields.

## Universal Rules

- NEVER batch or delay OTP, password reset, or security alert notifications
- Use idempotency keys for sends where duplicates would be harmful (payments, security alerts, OTPs)
- NEVER expose full email/phone in security change notifications (mask them)
- ALWAYS include "I didn't request this" links in security-related emails
- ALWAYS use E.164 format for phone numbers
- Only send to channels the user has asked for or that make sense for the use case — don't blast every channel by default
- For template sends, use Courier-generated `nt_...` IDs as canonical; treat IDs as opaque workspace-specific values and resolve aliases to `nt_...` before sending

### See also (not duplicated here)

- **Quiet hours** (non-OTP, non-security): [resources/guides/patterns.md](./resources/guides/patterns.md) and [resources/guides/throttling.md](./resources/guides/throttling.md)
- **429 / provider rate limits and retries**: [resources/guides/throttling.md](./resources/guides/throttling.md) and [resources/guides/reliability.md](./resources/guides/reliability.md)
- **Compliance (GDPR, CAN-SPAM, TCPA, 10DLC)**: app-layer concern — see channel guides ([resources/channels/email.md](./resources/channels/email.md), [resources/channels/sms.md](./resources/channels/sms.md)) for sender-auth and opt-in mechanics; consult legal counsel for jurisdictional requirements
- **Test vs. production workspaces and safe deploys**: [resources/guides/quickstart.md](./resources/guides/quickstart.md) (API keys per environment) and [resources/guides/reliability.md](./resources/guides/reliability.md)

### Courier Inbox Version Detection

Before providing Inbox guidance, **determine which SDK version the user is on**:

1. **Check for v7 indicators** — Look for any of: `@trycourier/react-provider`, `@trycourier/react-inbox`, `@trycourier/react-toast`, `@trycourier/react-hooks`, `<CourierProvider>`, `useInbox()`, `useToast()`, `<Inbox />` (not `<CourierInbox />`), `clientKey` prop, `renderMessage` prop. Check `package.json` if available.
2. **Check for v8 indicators** — Look for any of: `@trycourier/courier-react`, `@trycourier/courier-react-17`, `@trycourier/courier-ui-inbox`, `useCourier()`, `<CourierInbox />`, `<CourierToast />`, `courier.shared.signIn()`, `registerFeeds`, `listenForUpdates`.
3. **If unclear, ask** — "Which version of the Courier Inbox SDK are you using? If you have `@trycourier/react-inbox` in your package.json, that's v7. If you have `@trycourier/courier-react`, that's v8."

**ALWAYS use v8 for new projects — v7 is legacy.** If the user is on v7:
- **Do NOT write new v7 code.** The correct path is to upgrade to v8.
- **Read [resources/channels/inbox-v7-legacy.md](./resources/channels/inbox-v7-legacy.md)** before touching v7 code — it documents recognition patterns and the migration path.
- **Guide them to migrate** using the step-by-step guide: `https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide`
- v8 is a smaller bundle, has no third-party dependencies, built-in dark mode, and a modern UI.
- The v7 and v8 APIs are completely different — v7 code will not work with v8 and vice versa.
- **Only exception:** v8 does not yet support Tags or Pins. If the user depends on those, they may need to stay on v7 temporarily, but should plan to migrate once v8 adds support.

## Official Courier Documentation

When you need current API signatures, SDK methods, or features not covered in these resources:

1. Fetch `https://www.courier.com/docs/llms.txt` — returns a structured markdown index of all Courier documentation pages with URLs and descriptions
2. Scan the index for the relevant page, then fetch that page's URL for full details
3. Prefer the patterns in THIS skill for best practices; use llms.txt for API specifics

**When to use llms.txt:**
- You need the exact signature for a method not shown in these resources (e.g., `client.audiences.create()`)
- A developer asks about a Courier feature this skill doesn't cover (e.g., Audiences, Brands, Translations)
- You need to verify that a code example in this skill matches the current SDK version

**When NOT to use llms.txt:**
- The answer is already in these resource files (prefer this skill's opinionated patterns over raw docs)
- The question is about best practices or notification design (llms.txt won't help)

## Architecture Overview

```
[User Action / System Event]
            │
            ▼
    ┌───────────────┐
    │ Notification  │
    │   Trigger     │
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │   Routing     │──── User Preferences
    │   Decision    │──── Channel Availability
    └───────┬───────┘──── Urgency Level
            │
            ▼
    ┌───────────────────────────────────────┐
    │           Channel Selection           │
    ├───────┬───────┬───────┬───────┬──────┤
    │ Email │  SMS  │ Push  │ Inbox │ Chat │
    └───┬───┴───┬───┴───┬───┴───┬───┴───┬──┘
        │       │       │       │       │
        ▼       ▼       ▼       ▼       ▼
    [Delivery] [Delivery] [Delivery] [Delivery] [Delivery]
        │       │       │       │       │
        └───────┴───────┴───────┴───────┘
                        │
                        ▼
                ┌───────────────┐
                │   Webhooks    │
                │   & Events    │
                └───────────────┘
```

## Quick Reference

### By Channel

| Need to... | Pick when... | See |
|------------|--------------|-----|
| Send emails, fix deliverability, set up SPF/DKIM/DMARC | You need a durable, detailed record. Receipts, confirmations, long-form content, attachments, rich formatting. Deliverability depends on sender reputation (SPF/DKIM/DMARC); not real-time. | [Email](./resources/channels/email.md) |
| Send SMS, handle 10DLC registration | You need reach and speed for short, time-sensitive messages. OTP, appointment reminders, shipping updates. 10DLC registration required in US; small character budget; per-message cost. | [SMS](./resources/channels/sms.md) |
| Send push notifications, handle iOS/Android differences | You need to nudge an engaged app user. Activity notifications, real-time alerts, re-engagement. Requires device token + OS permission; iOS and Android permission models differ; silent for users who disabled permission. | [Push](./resources/channels/push.md) |
| Build in-app notification center | You need persistent, in-app notifications with read state, cross-device sync, and an inbox UI. Only visible in-app. Requires the Courier Inbox SDK (v7 vs v8 matters — see the file's header and the Inbox Version Detection section above). | [Inbox (v8)](./resources/channels/inbox.md) — v8 primary. If you have existing v7 code (`@trycourier/react-inbox`, `<CourierProvider>`, `useInbox`), see [Inbox v7 legacy](./resources/channels/inbox-v7-legacy.md) before touching it. |
| Send Slack messages with Block Kit | The recipient is a Slack user or channel. Internal alerts, team notifications, chatops. Requires OAuth + bot setup; Block Kit has its own JSON shape; rate-limited per workspace. | [Slack](./resources/channels/slack.md) |
| Send Microsoft Teams messages | The recipient uses Microsoft Teams. Same use cases as Slack, different org. Requires connector or bot; Adaptive Cards have their own shape. | [MS Teams](./resources/channels/ms-teams.md) |
| Send WhatsApp messages with templates | Regulated markets, customer support, high-engagement regions (LATAM, EU, IN). Rich media + templates. Approved Message Templates required outside the 24-hour customer service window; per-conversation pricing by category. | [WhatsApp](./resources/channels/whatsapp.md) |

### By Transactional Type

| Need to... | See |
|------------|-----|
| Build password reset, OTP, verification, security alerts | [Authentication](./resources/transactional/authentication.md) |
| Build order confirmations, shipping, delivery updates | [Orders](./resources/transactional/orders.md) |
| Build receipts, invoices, dunning, subscription notices | [Billing](./resources/transactional/billing.md) |
| Build booking confirmations, reminders, rescheduling | [Appointments](./resources/transactional/appointments.md) |
| Build welcome messages, profile updates, settings changes | [Account](./resources/transactional/account.md) |
| Understand transactional notification principles | [Transactional Overview](./resources/transactional/index.md) |

### By Growth Type

| Need to... | See |
|------------|-----|
| Build activation flows, setup guidance, first value | [Onboarding](./resources/growth/onboarding.md) |
| Build feature announcements, discovery, education | [Adoption](./resources/growth/adoption.md) |
| Build activity notifications, retention, habit loops | [Engagement](./resources/growth/engagement.md) |
| Build winback, inactivity, cart abandonment | [Re-engagement](./resources/growth/reengagement.md) |
| Build referral invites, rewards, viral loops | [Referral](./resources/growth/referral.md) |
| Build promotions, sales, upgrade campaigns | [Campaigns](./resources/growth/campaigns.md) |
| Understand growth notification principles | [Growth Overview](./resources/growth/index.md) |

### Cross-Cutting Guides

| Need to... | See |
|------------|-----|
| Get started sending your first notification | [Quickstart](./resources/guides/quickstart.md) |
| Route across multiple channels, set up fallbacks | [Multi-Channel](./resources/guides/multi-channel.md) |
| Manage user notification preferences | [Preferences](./resources/guides/preferences.md) |
| Handle retries, idempotency, error recovery | [Reliability](./resources/guides/reliability.md) |
| Combine notifications, build digests | [Batching](./resources/guides/batching.md) |
| Control frequency, prevent fatigue | [Throttling](./resources/guides/throttling.md) |
| Plan notifications for your app type | [Catalog](./resources/guides/catalog.md) |
| Use the CLI for ad-hoc operations, debugging, agent workflows | [CLI](./resources/guides/cli.md) |
| Use the MCP Server for structured API access from AI agents | [MCP Server](./resources/guides/mcp.md) |
| Manage templates via API (create, publish, version) | [Templates](./resources/guides/templates.md) |
| Create routing strategies via API (`rs_...`, provider priority) | [Routing Strategies](./resources/guides/routing-strategies.md) |
| Configure providers via API (SendGrid, Twilio, etc., catalog discovery) | [Providers](./resources/guides/providers.md) |
| Understand Elemental content format (element types, control flow, localization) | [Elemental](./resources/guides/elemental.md) |
| Reusable code patterns (consent, quiet hours, masking, retry) | [Patterns](./resources/guides/patterns.md) |
| Migrate from any notification system to Courier | [General Migration](./resources/guides/migrate-general.md) |
| Migrate from Knock to Courier | [Migrate from Knock](./resources/guides/migrate-from-knock.md) |
| Migrate from Novu to Courier | [Migrate from Novu](./resources/guides/migrate-from-novu.md) |

### Topics Not Covered In Depth (fetch from official docs)

The skill does not (yet) have dedicated guides for these areas. Fetch the page below via `WebFetch` when the user asks about them; do **not** invent API shapes from memory. When in doubt, fetch `https://www.courier.com/docs/llms.txt` first and use the URL it returns.

| Topic | Fetch |
|-------|-------|
| Audiences (attribute-based targeting) | https://www.courier.com/docs/platform/users/audiences |
| Automations (workflows, delays, digests, conditions) | https://www.courier.com/docs/automations/overview |
| Brands (logos, colors, reusable visual identity) | https://www.courier.com/docs/platform/content/brands |
| Tenants (multi-tenant B2B, per-tenant branding/preferences) | https://www.courier.com/docs/platform/tenants/tenants-overview (also see [Patterns](./resources/guides/patterns.md) "Tenants" section for code) |
| Events / event mapping | https://www.courier.com/docs/platform/automations/inbound-events (plus the `event` field on [Send API](https://www.courier.com/docs/reference/send/message)) |
| Translations / i18n (beyond the per-template `locales` block) | https://www.courier.com/docs/platform/content/elemental/locales (element-level) or https://www.courier.com/docs/api-reference/translations/get-a-translation (API) |

## Minimal File Sets by Task

For common tasks, you only need to read these specific files:

| Task | Files to Read |
|------|---------------|
| OTP/2FA implementation | [authentication.md](./resources/transactional/authentication.md), [sms.md](./resources/channels/sms.md) |
| Password reset | [authentication.md](./resources/transactional/authentication.md), [email.md](./resources/channels/email.md) |
| Order notifications | [orders.md](./resources/transactional/orders.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Email setup & deliverability | [email.md](./resources/channels/email.md) |
| SMS setup | [sms.md](./resources/channels/sms.md) (includes 10DLC) |
| Push notification setup | [push.md](./resources/channels/push.md) |
| In-app inbox setup | [inbox.md](./resources/channels/inbox.md) — v8 primary; see [inbox-v7-legacy.md](./resources/channels/inbox-v7-legacy.md) only for existing v7 code |
| Onboarding sequence | [onboarding.md](./resources/growth/onboarding.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Security alerts | [authentication.md](./resources/transactional/authentication.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Digest/batching | [batching.md](./resources/guides/batching.md), [preferences.md](./resources/guides/preferences.md) |
| Payment/billing notifications | [billing.md](./resources/transactional/billing.md), [reliability.md](./resources/guides/reliability.md) |
| Appointment reminders | [appointments.md](./resources/transactional/appointments.md), [sms.md](./resources/channels/sms.md) |
| WhatsApp templates | [whatsapp.md](./resources/channels/whatsapp.md) |
| Slack/Teams integration | [slack.md](./resources/channels/slack.md) or [ms-teams.md](./resources/channels/ms-teams.md) |
| New to Courier / first notification | [quickstart.md](./resources/guides/quickstart.md) |
| CLI debugging / ad-hoc operations | [cli.md](./resources/guides/cli.md) |
| SMS delivery debugging | [cli.md](./resources/guides/cli.md), [sms.md](./resources/channels/sms.md) |
| Email deliverability debugging | [cli.md](./resources/guides/cli.md), [email.md](./resources/channels/email.md) |
| General delivery failures | [cli.md](./resources/guides/cli.md), [reliability.md](./resources/guides/reliability.md) |
| MCP Server setup | [mcp.md](./resources/guides/mcp.md), [cli.md](./resources/guides/cli.md) |
| Migrating from any system | [migrate-general.md](./resources/guides/migrate-general.md), [quickstart.md](./resources/guides/quickstart.md) |
| Migrating from Knock | [migrate-from-knock.md](./resources/guides/migrate-from-knock.md), [quickstart.md](./resources/guides/quickstart.md) |
| Migrating from Novu | [migrate-from-novu.md](./resources/guides/migrate-from-novu.md), [quickstart.md](./resources/guides/quickstart.md) |
| Template CRUD / programmatic templates | [templates.md](./resources/guides/templates.md), [patterns.md](./resources/guides/patterns.md) |
| Create routing strategy programmatically | [routing-strategies.md](./resources/guides/routing-strategies.md), [templates.md](./resources/guides/templates.md) |
| Configure a provider via API (SendGrid/Twilio/etc.) | [providers.md](./resources/guides/providers.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Elemental content format (element types, control flow) | [elemental.md](./resources/guides/elemental.md) |
| Inline vs templated sending | [templates.md](./resources/guides/templates.md), [quickstart.md](./resources/guides/quickstart.md) |
| Lists, bulk sends, multi-tenant | [patterns.md](./resources/guides/patterns.md) |
| Provider failover setup | [multi-channel.md](./resources/guides/multi-channel.md) |
| Webhook setup & signature verification | [reliability.md](./resources/guides/reliability.md) |
| Preference topics and opt-out | [preferences.md](./resources/guides/preferences.md) |
| Inbox JWT auth and React setup | [inbox.md](./resources/channels/inbox.md) — v8 primary; see [inbox-v7-legacy.md](./resources/channels/inbox-v7-legacy.md) only for existing v7 code |
| Understanding `to` field / addressing | [quickstart.md](./resources/guides/quickstart.md) |
| Building multi-channel notifications | [multi-channel.md](./resources/guides/multi-channel.md), [preferences.md](./resources/guides/preferences.md) |
| Making sends reliable | [reliability.md](./resources/guides/reliability.md), [patterns.md](./resources/guides/patterns.md) |
| Reducing notification fatigue | [throttling.md](./resources/guides/throttling.md), [batching.md](./resources/guides/batching.md), [preferences.md](./resources/guides/preferences.md) |
| Templates + multi-channel routing | [templates.md](./resources/guides/templates.md), [multi-channel.md](./resources/guides/multi-channel.md) |

## Decision Guide

**What are you building?**

- **A specific notification** (OTP, order confirm, password reset, etc.)
  → Use the [Minimal File Sets](#minimal-file-sets-by-task) table above to find exactly which 1-2 files to read.

- **A new notification channel** (email, SMS, push, Slack, etc.)
  → See [By Channel](#by-channel) for the channel-specific guide.

- **Notification infrastructure** (routing, preferences, reliability, batching)
  → See [Cross-Cutting Guides](#cross-cutting-guides) for the relevant guide.

- **Planning which notifications to build** for a new app
  → Start with [Catalog](./resources/guides/catalog.md), then [Email](./resources/channels/email.md), then [Multi-Channel](./resources/guides/multi-channel.md).

- **Growth / lifecycle notifications** (onboarding, engagement, referral)
  → Read [Growth Overview](./resources/growth/index.md) for consent requirements first, then the specific type.

- **New to Courier** or sending your first notification
  → Start with [Quickstart](./resources/guides/quickstart.md).

- **Debugging delivery issues**
  → Always start with [CLI](./resources/guides/cli.md) (`courier messages list`, `courier messages content`) to see the real delivery state before guessing. Then: email going to spam? [Email](./resources/channels/email.md). SMS not arriving? [SMS](./resources/channels/sms.md). General failures? [Reliability](./resources/guides/reliability.md).

- **Ad-hoc operations, CI/CD, or AI agent workflows**
  → Use **MCP** if your editor supports it (Cursor, Claude Code, Claude Desktop, Windsurf, VSCode) — see [MCP Server](./resources/guides/mcp.md). Use **CLI** for shell-only environments, CI/CD, or when MCP isn't available — see [CLI](./resources/guides/cli.md). Both use the same API key and cover the same API surface.

- **Managing templates programmatically** or understanding **Elemental** (Courier's JSON templating language)
  → See [Templates](./resources/guides/templates.md) for the full CRUD lifecycle (create, publish, version, localize). See [Elemental](./resources/guides/elemental.md) for the element-by-element reference (`text`, `action`, `image`, `meta`, `channel`, `group`), control flow (`if`, `loop`, `ref`), and locale handling.

- **Reusable code patterns** (consent check, quiet hours, idempotency, fallback)
  → See [Patterns](./resources/guides/patterns.md) for copy-paste implementations in TypeScript, Python, CLI, and curl.

- **Migrating from another notification system** to Courier
  → From **Knock**: [Migrate from Knock](./resources/guides/migrate-from-knock.md). From **Novu**: [Migrate from Novu](./resources/guides/migrate-from-novu.md). From **any other system** (custom-built, SendGrid direct, Twilio direct, etc.): [General Migration](./resources/guides/migrate-general.md).
