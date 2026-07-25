# Courier Notification Skills — the agent skill for building notifications with Courier

Give your AI coding assistant everything it needs to **integrate [Courier](https://www.courier.com), ship notification features, and debug delivery** — across email, SMS, push, in-app inbox, Slack, Microsoft Teams, and WhatsApp. Works with Claude Code, Cursor, Codex, and any tool that supports [agent skills](https://www.courier.com/docs).

```bash
npx skills add trycourier/courier-skills
```

> **What is this?** A packaged, verified knowledge base that teaches an AI agent *how to use Courier well* — the right primitive for each use case, the exact SDK shapes for the installed version, and the rules you can't get wrong (never batch an OTP, mask PII in security alerts, recorded opt-in for marketing). Every API claim is checked against the installed SDK, so the code your agent writes actually runs.

## What you can build with it

Ask your assistant in plain English; the skill routes it to the right Courier primitive and writes working code (TypeScript, Python, CLI, or curl):

- **"Send a welcome email from my Node backend"** → a single `client.send.message` with a template
- **"Add an in-app notification center to my React app"** → the Courier Inbox, JWT auth, real-time updates
- **"Batch these into a daily digest so users aren't spammed"** → a journey with an `add-to-digest` node
- **"Fall back from push to email if push fails"** → a routing strategy with ordered channels
- **"Let users choose which notifications they get"** → preference topics + a hosted preference page
- **"Why didn't this message deliver?"** → the CLI delivery ladder: `messages list` → `history` → `content`
- **"Send to a segment of trial users that stays current"** → an audience with live filter rules
- **"Give each B2B tenant its own branding and defaults"** → tenants with per-tenant brand and preferences

One `send` call does the whole job: address a **user** (or list, audience, or tenant), content comes from a **template** or inline, **routing** picks the channels, and **preferences** gate delivery. Multi-step flows — anything with a delay, branch, or aggregation — are **journeys**, defined as JSON and invoked by API.

## Install

**Any assistant** (recommended — Claude Code, Cursor, Codex, and more):

```bash
npx skills add trycourier/courier-skills
```

**Claude Code** (plugin — self-updates and ships the Courier docs MCP):

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

Discovery is driven by the `SKILL.md` `name` and `description` frontmatter — no extra configuration.

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

The same shape sends email, SMS, push, Slack, Teams, WhatsApp, or in-app — the channel is decided by routing and the user's profile, not by a different API. [See the quickstart →](https://www.courier.com/docs)

## What the skill covers

**Channels** — Email (deliverability, SPF/DKIM/DMARC), SMS (10DLC, opt-in/opt-out), Push (APNs/FCM, device tokens), In-app Inbox (JWT auth, React / Web Components / React Native / iOS / Android / Flutter), Slack (Block Kit, OAuth), Microsoft Teams (Adaptive Cards), WhatsApp (approved templates, the 24-hour window).

**Notification types** — Transactional (password reset, OTP, orders, receipts, dunning, security alerts) and lifecycle marketing (onboarding, adoption, digests, win-back, campaigns) — each mapped to the Courier primitive that implements it, with the safety rules inline.

**Core platform** — Quickstart, Journeys (delays, branches, batching, digests, throttling, A/B, cancellation), Templates & Elemental, multi-channel routing, preferences & preference sections, brands, audiences, tenants, reliability (idempotency, retries, delivery statuses, webhooks), routing strategies, provider configuration.

**Tooling** — the CLI for ad-hoc operations and delivery debugging, and MCP (the [API server](https://mcp.courier.com) to operate a workspace, the [docs server](https://www.courier.com/docs/mcp) to look things up).

## Who it's for

- Developers building SaaS, e-commerce, marketplaces, or mobile apps
- Teams consolidating email/SMS/push/chat providers behind one notification API
- Engineers implementing preference centers, unsubscribe handling, or multi-channel routing
- Anyone pairing an AI coding assistant with Courier and wanting it to get the API right the first time

## Frequently asked questions

**How do I send a notification with Courier?**
Call `client.send.message({ message: { to, template, data } })` with the Node SDK ([`@trycourier/courier`](https://www.npmjs.com/package/@trycourier/courier)) or `client.send.message(message={...})` with the Python SDK (`trycourier`). Both read the API key from `COURIER_API_KEY` by default.

**Which channels does Courier support?**
Email, SMS, push, in-app inbox, Slack, Microsoft Teams, and WhatsApp — through one unified `send` API, across providers like SendGrid, SES, Postmark, Twilio, Vonage, FCM, and APNs.

**How do I add an in-app notification center (notification bell/feed)?**
Use the Courier Inbox: send to the `inbox` channel server-side, and render it client-side with the React, Web Components, or React Native SDK, secured with a per-user scoped JWT. The skill's inbox references cover the full setup.

**What's the difference between transactional and marketing notifications?**
Transactional notifications are triggered by a user action (password reset, order confirmation) and should never be batched or delayed. Marketing notifications are sent proactively and require recorded opt-in.

**How do I handle notification preferences?**
See [`references/guides/preferences.md`](./skills/courier/references/guides/preferences.md) for per-user subscription topics, opt-out, hosted [preference pages](https://www.courier.com/docs/platform/preferences/hosted-page), and workspace-level preference sections.

**How do I debug why a message wasn't delivered?**
Start from the delivery ladder in the skill: confirm Courier accepted the request (`requestId`), then `courier messages list --trace-id`, `history`, and `content` to see where it stopped and what rendered — before touching the channel.

**How do I build multi-step flows (onboarding, escalation, win-back)?**
Use [Journeys](https://www.courier.com/docs/platform/journeys/building-journeys-via-api) — a JSON DAG of send/delay/branch/fetch/throttle/batch nodes you create, publish, and invoke over the API.

## Repository structure

```
courier-skills/
├── .claude-plugin/marketplace.json   # Claude Code plugin manifest
├── .mcp.json                         # Courier docs MCP, shipped with the plugin
├── AGENTS.md                         # Contributor guide
├── scripts/verify-sdk-claims.py      # Checks every SDK call exists in the installed package
└── skills/courier/
    ├── SKILL.md                      # Entry point — routes to the right reference
    └── references/
        ├── transactional.md   lifecycle-marketing.md   sdk-reference.md
        ├── channels/  (email, sms, push, inbox, slack, ms-teams, whatsapp)
        ├── inbox/     (rendering, auth, react, web-components, react-native, legacy-v7)
        └── guides/    (quickstart, journeys, templates, elemental, multi-channel,
                        preferences, batching, throttling, brands, audiences, tenants,
                        patterns, routing-strategies, providers, reliability, cli, mcp)
```

Open `skills/courier/SKILL.md` — its **Where to Look** table routes you to the one or two references that match your task.

## Integrations & providers

| Channel | Providers |
|---------|-----------|
| Email | SendGrid, Amazon SES, Postmark, Mailgun, Resend, SparkPost |
| SMS | Twilio, MessageBird, Vonage, Plivo, Telnyx |
| Push | Firebase Cloud Messaging (FCM), Apple Push Notification service (APNs), Expo |
| Chat | Slack, Microsoft Teams |
| Messaging | WhatsApp Business API, Facebook Messenger |

## Links

- **Courier** — [courier.com](https://www.courier.com) · [Documentation](https://www.courier.com/docs) · [API Reference](https://www.courier.com/docs/api-reference/)
- **SDKs** — [`@trycourier/courier` (Node)](https://www.npmjs.com/package/@trycourier/courier) · `trycourier` (Python)
- **MCP** — [API server](https://mcp.courier.com) · [docs server](https://www.courier.com/docs/mcp)

## Contributing

Found an issue or want to add a notification pattern? PRs welcome. Every documented SDK call is verified against the installed package by `scripts/verify-sdk-claims.py` — run it before submitting.

## License

[MIT](./LICENSE) © Courier, Inc.

---

Built for the [Courier](https://www.courier.com) notification platform. Works with any AI coding assistant that supports agent skills.
