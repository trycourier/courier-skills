---
name: courier-notification-skills
description: Use when building notifications across email, SMS, push, in-app, Slack, Teams, or WhatsApp. Covers transactional messages (password reset, OTP, orders, billing), growth notifications (onboarding, engagement, referral), multi-channel routing, compliance (GDPR, TCPA, CAN-SPAM), and reliability patterns.
---

# Courier Notification Skills

Guidance for building deliverable, compliant, and engaging notifications across all channels.

## How to Use This Skill

1. **Identify the task** — What channel, notification type, or cross-cutting concern is the user working on?
2. **Read only what's needed** — Use the routing tables below to find the 1-2 files relevant to the task. Do NOT read all files.
3. **Check for live docs** — For current API signatures and SDK methods, fetch `https://www.courier.com/docs/llms.txt`
4. **Synthesize before coding** — Plan the complete implementation (channels, routing, compliance, error handling) before writing code.
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

## Universal Rules

- NEVER batch or delay OTP, password reset, or security alert notifications
- Use idempotency keys for sends where duplicates would be harmful (payments, security alerts, OTPs)
- NEVER expose full email/phone in security change notifications (mask them)
- ALWAYS include "I didn't request this" links in security-related emails
- ALWAYS use E.164 format for phone numbers
- Only send to channels the user has asked for or that make sense for the use case — don't blast every channel by default
- For template sends, use Courier-generated `nt_...` IDs as canonical; treat IDs as opaque workspace-specific values and resolve aliases to `nt_...` before sending

### Courier Inbox Version Detection

Before providing Inbox guidance, **determine which SDK version the user is on**:

1. **Check for v7 indicators** — Look for any of: `@trycourier/react-provider`, `@trycourier/react-inbox`, `@trycourier/react-toast`, `@trycourier/react-hooks`, `<CourierProvider>`, `useInbox()`, `useToast()`, `<Inbox />` (not `<CourierInbox />`), `clientKey` prop, `renderMessage` prop. Check `package.json` if available.
2. **Check for v8 indicators** — Look for any of: `@trycourier/courier-react`, `@trycourier/courier-react-17`, `@trycourier/courier-ui-inbox`, `useCourier()`, `<CourierInbox />`, `<CourierToast />`, `courier.shared.signIn()`, `registerFeeds`, `listenForUpdates`.
3. **If unclear, ask** — "Which version of the Courier Inbox SDK are you using? If you have `@trycourier/react-inbox` in your package.json, that's v7. If you have `@trycourier/courier-react`, that's v8."

**ALWAYS use v8 for new projects — v7 is legacy.** If the user is on v7:
- **Do NOT write new v7 code.** The correct path is to upgrade to v8.
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
- The question is about best practices, compliance, or notification design (llms.txt won't help)

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

| Need to... | See |
|------------|-----|
| Send emails, fix deliverability, set up SPF/DKIM/DMARC | [Email](./resources/channels/email.md) |
| Send SMS, handle TCPA/10DLC compliance | [SMS](./resources/channels/sms.md) |
| Send push notifications, handle iOS/Android differences | [Push](./resources/channels/push.md) |
| Build in-app notification center | [Inbox](./resources/channels/inbox.md) |
| Send Slack messages with Block Kit | [Slack](./resources/channels/slack.md) |
| Send Microsoft Teams messages | [MS Teams](./resources/channels/ms-teams.md) |
| Send WhatsApp messages with templates | [WhatsApp](./resources/channels/whatsapp.md) |

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
| Ensure GDPR, TCPA, CAN-SPAM compliance | [Compliance](./resources/guides/compliance.md) |
| Handle retries, idempotency, error recovery | [Reliability](./resources/guides/reliability.md) |
| Combine notifications, build digests | [Batching](./resources/guides/batching.md) |
| Control frequency, prevent fatigue | [Throttling](./resources/guides/throttling.md) |
| Plan notifications for your app type | [Catalog](./resources/guides/catalog.md) |
| Use the CLI for ad-hoc operations, debugging, agent workflows | [CLI](./resources/guides/cli.md) |
| Use the MCP Server for structured API access from AI agents | [MCP Server](./resources/guides/mcp.md) |
| Manage templates via API or understand Elemental content format | [Templates](./resources/guides/templates.md) |
| Reusable code patterns (consent, quiet hours, masking, retry) | [Patterns](./resources/guides/patterns.md) |
| Migrate from any notification system to Courier | [General Migration](./resources/guides/migrate-general.md) |
| Migrate from Knock to Courier | [Migrate from Knock](./resources/guides/migrate-from-knock.md) |
| Migrate from Novu to Courier | [Migrate from Novu](./resources/guides/migrate-from-novu.md) |

## Minimal File Sets by Task

For common tasks, you only need to read these specific files:

| Task | Files to Read |
|------|---------------|
| OTP/2FA implementation | [authentication.md](./resources/transactional/authentication.md), [sms.md](./resources/channels/sms.md) |
| Password reset | [authentication.md](./resources/transactional/authentication.md), [email.md](./resources/channels/email.md) |
| Order notifications | [orders.md](./resources/transactional/orders.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Email setup & deliverability | [email.md](./resources/channels/email.md), [compliance.md](./resources/guides/compliance.md) |
| SMS setup & compliance | [sms.md](./resources/channels/sms.md) (includes 10DLC, TCPA) |
| Push notification setup | [push.md](./resources/channels/push.md) |
| In-app inbox setup | [inbox.md](./resources/channels/inbox.md) — check SDK version first (v7 vs v8) |
| Onboarding sequence | [onboarding.md](./resources/growth/onboarding.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Security alerts | [authentication.md](./resources/transactional/authentication.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Digest/batching | [batching.md](./resources/guides/batching.md), [preferences.md](./resources/guides/preferences.md) |
| Payment/billing notifications | [billing.md](./resources/transactional/billing.md), [reliability.md](./resources/guides/reliability.md) |
| Appointment reminders | [appointments.md](./resources/transactional/appointments.md), [sms.md](./resources/channels/sms.md) |
| WhatsApp templates | [whatsapp.md](./resources/channels/whatsapp.md) |
| Slack/Teams integration | [slack.md](./resources/channels/slack.md) or [ms-teams.md](./resources/channels/ms-teams.md) |
| New to Courier / first notification | [quickstart.md](./resources/guides/quickstart.md) |
| CLI debugging / ad-hoc operations | [cli.md](./resources/guides/cli.md) |
| CLI + delivery debugging | [cli.md](./resources/guides/cli.md), [reliability.md](./resources/guides/reliability.md) |
| MCP Server setup | [mcp.md](./resources/guides/mcp.md) |
| Migrating from any system | [migrate-general.md](./resources/guides/migrate-general.md), [quickstart.md](./resources/guides/quickstart.md) |
| Migrating from Knock | [migrate-from-knock.md](./resources/guides/migrate-from-knock.md), [quickstart.md](./resources/guides/quickstart.md) |
| Migrating from Novu | [migrate-from-novu.md](./resources/guides/migrate-from-novu.md), [quickstart.md](./resources/guides/quickstart.md) |
| Template CRUD / programmatic templates | [templates.md](./resources/guides/templates.md) |
| Elemental content format | [templates.md](./resources/guides/templates.md) |
| Inline vs templated sending | [templates.md](./resources/guides/templates.md), [quickstart.md](./resources/guides/quickstart.md) |
| Lists, bulk sends, multi-tenant | [patterns.md](./resources/guides/patterns.md) |
| Provider failover setup | [multi-channel.md](./resources/guides/multi-channel.md) |
| Webhook setup & signature verification | [reliability.md](./resources/guides/reliability.md) |
| Preference topics and opt-out | [preferences.md](./resources/guides/preferences.md) |
| Inbox JWT auth and React setup | [inbox.md](./resources/channels/inbox.md) — check SDK version first (v7 vs v8) |
| Understanding `to` field / addressing | [quickstart.md](./resources/guides/quickstart.md) |

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

- **Compliance concerns** (GDPR, TCPA, CAN-SPAM)
  → Read [Compliance](./resources/guides/compliance.md), then channel-specific rules in [SMS](./resources/channels/sms.md) or [Email](./resources/channels/email.md).

- **New to Courier** or sending your first notification
  → Start with [Quickstart](./resources/guides/quickstart.md).

- **Debugging delivery issues**
  → Use the [CLI](./resources/guides/cli.md) to inspect messages and delivery history. Email going to spam? [Email](./resources/channels/email.md). SMS not arriving? [SMS](./resources/channels/sms.md). General failures? [Reliability](./resources/guides/reliability.md).

- **Ad-hoc operations, CI/CD, or AI agent workflows**
  → Use **MCP** if your editor supports it (Cursor, Claude Code, Claude Desktop, Windsurf, VSCode) — see [MCP Server](./resources/guides/mcp.md). Use **CLI** for shell-only environments, CI/CD, or when MCP isn't available — see [CLI](./resources/guides/cli.md). Both use the same API key and cover the same API surface.

- **Managing templates programmatically** or understanding **Elemental** (Courier's JSON templating language)
  → See [Templates](./resources/guides/templates.md) for the full CRUD lifecycle, all element types, control flow, and localization.

- **Reusable code patterns** (consent check, quiet hours, idempotency, fallback)
  → See [Patterns](./resources/guides/patterns.md) for copy-paste implementations in TypeScript, Python, CLI, and curl.

- **Migrating from another notification system** to Courier
  → From **Knock**: [Migrate from Knock](./resources/guides/migrate-from-knock.md). From **Novu**: [Migrate from Novu](./resources/guides/migrate-from-novu.md). From **any other system** (custom-built, SendGrid direct, Twilio direct, etc.): [General Migration](./resources/guides/migrate-general.md).
