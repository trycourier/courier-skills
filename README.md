# Courier Notification Skills: the agent skill for building notifications with Courier

Give your AI coding assistant everything it needs to integrate [Courier](https://www.courier.com), ship notification features, and debug delivery across email, SMS, push, in-app inbox, Slack, Microsoft Teams, and WhatsApp. Works with Claude Code, Cursor, Codex, and any tool that supports agent skills.

```bash
npx skills add trycourier/courier-skills
```

> **What is this?** A packaged, verified knowledge base that teaches an AI agent how to use Courier well: the right primitive for each use case, the exact SDK shapes for the installed version, and the rules you cannot get wrong (never batch an OTP, mask PII in security alerts, recorded opt-in for marketing). Every API claim is checked against the installed SDK, so the code your agent writes actually runs.

**New to building notifications with AI?** Start with Courier's [Build with AI onboarding guide](https://www.courier.com/docs/tools/ai-onboarding), which covers the CLI, the [Courier MCP server](https://www.courier.com/docs/mcp), agent skills, and machine-readable docs.

## What you can build with it

Ask your assistant in plain English. The skill routes the request to the right Courier primitive and writes working code in TypeScript, Python, CLI, or curl:

- "Send a welcome email from my Node backend" gives you a single `client.send.message` with a template.
- "Add an in-app notification center to my React app" gives you the Courier Inbox with JWT auth and real-time updates.
- "Batch these into a daily digest so users are not spammed" gives you a journey with an `add-to-digest` node.
- "Fall back from push to email if push fails" gives you a routing strategy with ordered channels.
- "Let users choose which notifications they get" gives you preference topics and a hosted preference page.
- "Why did this message not deliver?" gives you the CLI delivery ladder: `messages list`, then `history`, then `content`.
- "Send to a segment of trial users that stays current" gives you an audience with live filter rules.
- "Give each B2B tenant its own branding and defaults" gives you tenants with per-tenant brand and preferences.
- "Send a one-time passcode and an order receipt" gives you transactional sends with idempotency, and never batched or delayed.
- "Build a 5-day onboarding series and a win-back flow" gives you lifecycle journeys with delays, branches, and recorded opt-in.

One `send` call does the whole job. You address a user (or a list, audience, or tenant), content comes from a template or inline, routing picks the channels, and preferences gate delivery. Multi-step flows, meaning anything with a delay, a branch, or aggregation, are journeys: defined as JSON and invoked by API.

## Install

**Any assistant** (recommended; works with Claude Code, Cursor, Codex, and more):

```bash
npx skills add trycourier/courier-skills
```

**Claude Code** (plugin; self-updates and ships the Courier docs MCP):

```bash
/plugin marketplace add trycourier/courier-skills
/plugin install courier@courier-skills
```

Run `/plugin update courier@courier-skills` to pick up changes. The plugin ships the [Courier docs MCP server](https://www.courier.com/docs/mcp) (`.mcp.json`), so the agent can look things up with no extra setup.

**Manual clone** (any tool that reads a skills directory):

```bash
git clone https://github.com/trycourier/courier-skills.git /tmp/courier-skills
cp -R /tmp/courier-skills/skills/courier ~/.cursor/skills/   # or ~/.claude/skills/
```

Discovery is driven by the `name` and `description` frontmatter in `SKILL.md`, with no extra configuration.

## The 30-second example

```typescript
import Courier from "@trycourier/courier";

const client = new Courier(); // reads COURIER_API_KEY from the environment

await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "welcome-email",       // or inline content: { title, body }
    data: { name: "Alice" },
  },
});
```

The same shape sends email, SMS, push, Slack, Teams, WhatsApp, or in-app. The channel is decided by routing and the user's profile, not by a different API. See the [quickstart](https://www.courier.com/docs).

## What the skill covers

**Channels.** Email (deliverability, SPF/DKIM/DMARC), SMS (10DLC, opt-in and opt-out), push (APNs and FCM, device tokens), in-app inbox (JWT auth, plus React, Web Components, React Native, iOS, Android, and Flutter rendering), Slack (Block Kit, OAuth), Microsoft Teams (Adaptive Cards), and WhatsApp (approved templates, the 24-hour window).

**Notification types.** [Transactional](./skills/courier/references/transactional.md) (password reset, OTP, orders, receipts, dunning, security alerts) and [lifecycle marketing](./skills/courier/references/lifecycle-marketing.md) (onboarding, adoption, digests, win-back, campaigns). Each is mapped to the Courier primitive that implements it, with the safety rules stated inline: transactional sends are never batched or delayed and mask PII, and marketing sends require recorded opt-in and one-click unsubscribe.

**Core platform.** Quickstart, journeys (delays, branches, batching, digests, throttling, A/B experiments, cancellation), templates and Elemental, multi-channel routing, preferences and preference sections, brands, audiences, tenants, reliability (idempotency, retries, delivery statuses, webhooks), routing strategies, and provider configuration.

**Tooling.** The CLI for ad-hoc operations and delivery debugging, and MCP: the [API server](https://mcp.courier.com) to operate a workspace and the [docs server](https://www.courier.com/docs/mcp) to look things up.

## Who it is for

- Developers building SaaS, e-commerce, marketplaces, or mobile apps.
- Teams consolidating email, SMS, push, and chat providers behind one notification API.
- Engineers implementing preference centers, unsubscribe handling, or multi-channel routing.
- Anyone pairing an AI coding assistant with Courier who wants it to get the API right the first time.

## Frequently asked questions

**How do I send a notification with Courier?**
Call `client.send.message({ message: { to, template, data } })` with the Node SDK ([`@trycourier/courier`](https://www.npmjs.com/package/@trycourier/courier)) or `client.send.message(message={...})` with the Python SDK (`trycourier`). Both read the API key from `COURIER_API_KEY` by default.

**Which channels does Courier support?**
Email, SMS, push, in-app inbox, Slack, Microsoft Teams, and WhatsApp, all through one unified `send` API, across providers like SendGrid, Amazon SES, Postmark, Twilio, Vonage, Firebase FCM, and Apple APNs.

**How do I add an in-app notification center or notification bell?**
Use the Courier Inbox. Send to the `inbox` channel server-side, then render it client-side with the React, Web Components, or React Native SDK, secured with a per-user scoped JWT. The inbox references in this skill cover the full setup, including real-time updates and unread counts.

**What is the difference between transactional and marketing notifications?**
Transactional notifications are triggered by a user action (password reset, order confirmation) and should never be batched or delayed. Marketing notifications are sent proactively and require recorded opt-in. See the [transactional guide](./skills/courier/references/transactional.md) and the [lifecycle marketing guide](./skills/courier/references/lifecycle-marketing.md) for patterns and the rules for each.

**How do I handle notification preferences?**
See [`references/guides/preferences.md`](./skills/courier/references/guides/preferences.md) for per-user subscription topics, opt-out, hosted [preference pages](https://www.courier.com/docs/platform/preferences/hosted-page), and workspace-level preference sections.

**How do I debug why a message was not delivered?**
Start from the delivery ladder in the skill. Confirm Courier accepted the request (it returns a `requestId`), then run `courier messages list --trace-id`, `history`, and `content` to see where it stopped and what rendered, before touching the channel.

**How do I build multi-step flows like onboarding, escalation, or win-back?**
Use [Journeys](https://www.courier.com/docs/platform/journeys/building-journeys-via-api), a JSON graph of send, delay, branch, fetch, throttle, and batch nodes that you create, publish, and invoke over the API.

## Repository structure

```
courier-skills/
├── .claude-plugin/marketplace.json   : Claude Code plugin manifest
├── .mcp.json                         : Courier docs MCP, shipped with the plugin
├── AGENTS.md                         : contributor guide
└── skills/courier/
    ├── SKILL.md                      : entry point that routes to the right reference
    └── references/
        ├── transactional.md   lifecycle-marketing.md   sdk-reference.md
        ├── channels/  (email, sms, push, inbox, slack, ms-teams, whatsapp)
        ├── inbox/     (rendering, auth, react, web-components, react-native, legacy-v7)
        └── guides/    (quickstart, journeys, templates, elemental, multi-channel,
                        preferences, batching, throttling, brands, audiences, tenants,
                        patterns, routing-strategies, providers, reliability, cli, mcp)
```

Open `skills/courier/SKILL.md`. Its **Where to Look** table routes you to the one or two references that match your task.

## Integrations and providers

Courier is provider-agnostic. You write one `send` call and Courier delivers through whichever provider you configure, so you can switch or add providers without changing application code. Commonly used integrations by channel:

| Channel | Providers |
|---------|-----------|
| Email | SendGrid, Amazon SES, Postmark, Mailgun, Resend, SparkPost, Mandrill, Mailjet, MailerSend, Amply, Gmail, OneSignal, SMTP |
| SMS | Twilio, Vonage, Telnyx, Sinch, Plivo, MessageBird, MessageMedia, Azure SMS, TextUs, Africa's Talking, SMSCentral |
| Push | Firebase Cloud Messaging (FCM), Apple Push Notification service (APNs), Expo, OneSignal, Airship |
| Chat | Slack, Microsoft Teams |
| Messaging | WhatsApp Business API |
| In-app | Courier Inbox |

Courier supports 50+ providers in total. For the complete, current list see the [Courier integrations docs](https://www.courier.com/docs/platform/channels/), or call `client.providers.catalog.list()` for the live catalog in your workspace.

## Links

- **Courier**: [courier.com](https://www.courier.com), [Documentation](https://www.courier.com/docs), [API Reference](https://www.courier.com/docs/api-reference/), [Build with AI](https://www.courier.com/docs/tools/ai-onboarding)
- **MCP**: [Courier MCP server docs](https://www.courier.com/docs/mcp), [API server endpoint](https://mcp.courier.com)
- **SDKs**: [`@trycourier/courier` (Node)](https://www.npmjs.com/package/@trycourier/courier), `trycourier` (Python)

## Contributing

Found an issue or want to add a notification pattern? PRs welcome. Keep every documented SDK call grounded in the installed package's own type definitions rather than reconstructing signatures from memory.

## License

[MIT](./LICENSE) © Courier, Inc.

Built for the [Courier](https://www.courier.com) notification platform. Works with any AI coding assistant that supports agent skills.
