# Courier Notification Skills

An agent skill for integrating Courier, adding notification features, and debugging delivery problems — across email, SMS, push, in-app inbox, Slack, Teams, and WhatsApp.

> **For AI Agents & Developers**: This skill provides structured guidance for implementing notifications with the [Courier API](https://www.courier.com). Use it to send emails, SMS, push notifications, Slack messages, and more through a unified interface.

## Why Use This Skill

- **Multi-channel notifications** — Send messages via email, SMS, push, Slack, Microsoft Teams, WhatsApp, and in-app inbox from a single API
- **Integration-first** — every use case maps to the Courier primitive that implements it, with TypeScript, Python, CLI, and curl examples
- **Built for debugging** — start from the CLI and delivery logs rather than guessing

## Who This Is For

- Developers building SaaS, e-commerce, marketplaces, or mobile apps
- Teams consolidating notification providers into a single API
- Engineers implementing user preferences, unsubscribe handling, or multi-channel routing

**Any assistant** (recommended — works with Claude Code, Cursor, Codex, and more):

```bash
npx skills add trycourier/courier-skills
```

This is the simplest path and works across tools.

**Claude Code** (plugin — self-updates and ships the docs MCP):

```bash
/plugin marketplace add trycourier/courier-skills
```

```bash
/plugin install courier@courier-skills
```

Run `/plugin update courier@courier-skills` to pick up changes. The plugin also ships the Courier docs MCP server (`.mcp.json`), so the agent can look things up with no extra setup.

**Manual clone** (any tool that reads a skills directory):

```bash
git clone https://github.com/trycourier/courier-skills.git /tmp/courier-skills
cp -R /tmp/courier-skills/skills/courier ~/.cursor/skills/
```

The skill lives in `skills/courier/`, so copy that directory into your assistant's skills directory — `~/.cursor/skills/` for Cursor, `~/.claude/skills/` for Claude Code, or `.cursor/skills/` inside a project. Discovery is driven by the `SKILL.md` `name` and `description` frontmatter, with no extra configuration.

## What This Skill Covers

**Channels**
- Email — deliverability, SPF/DKIM/DMARC, sender configuration
- SMS — 10DLC registration, character limits, opt-in/opt-out
- Push — APNs and FCM setup, device tokens, permission priming
- In-app inbox — JWT auth, React and mobile SDKs
- Slack — Block Kit, OAuth, bot setup
- Microsoft Teams — Adaptive Cards
- WhatsApp — approved templates, the 24-hour window

**Notification types**
- Transactional — password reset, OTP, orders and shipping, receipts, invoices, dunning, appointment reminders, account and security alerts
- Lifecycle marketing — onboarding and activation, feature adoption, activity notifications and digests, win-back, referral, promotional campaigns

Each maps the use case to the Courier primitive that implements it, and carries the rules you can't get wrong — never batching an OTP, masking PII in security alerts, recorded opt-in for marketing.

**Core platform**
- Quickstart — your first send
- Journeys — multi-step flows: delays, branches, batching, digests, throttling, A/B experiments, cancellation
- Templates and Elemental — content CRUD, publishing, versioning, localization
- Multi-channel routing — fallbacks, escalation, provider failover
- Preferences — subscription topics, preference centers, opt-out
- Batching and throttling — aggregation, digests, frequency caps
- Reliability — idempotency, retries, delivery statuses, webhook verification
- Routing strategies and provider configuration
- Reusable patterns — lists, audiences, tenants

**Tooling**
- CLI — ad-hoc operations and delivery debugging
- MCP — the API server for operating a workspace, and the docs server for looking things up

## Structure

```
courier-skills/
├── .claude-plugin/marketplace.json   # Claude Code plugin manifest
├── .mcp.json                         # Courier docs MCP, shipped with the plugin
├── AGENTS.md                         # Contributor guide
├── scripts/
│   └── verify-sdk-claims.py          # Checks every SDK call exists in the installed package
└── skills/courier/
    ├── SKILL.md                      # Entry point — routes to the right reference
    └── references/
        ├── transactional.md   lifecycle-marketing.md   sdk-reference.md
        ├── channels/
        │   ├── email.md   sms.md   push.md   inbox.md
        │   └── slack.md   ms-teams.md   whatsapp.md
        ├── inbox/                    # Rendering the inbox in your app (client-side)
        │   ├── rendering.md   auth.md   react.md
        │   └── web-components.md   react-native.md   legacy-v7.md
        └── guides/
            ├── quickstart.md   journeys.md   templates.md   elemental.md
            ├── multi-channel.md   preferences.md   reliability.md
            ├── batching.md   throttling.md   patterns.md
            ├── routing-strategies.md   providers.md
            └── cli.md   mcp.md
```

## Quick Start

Open `skills/courier/SKILL.md`. Its **Where to Look** table routes you to the one or two references that match your task.

## Integrations & Providers

This skill covers best practices for working with:

| Channel | Providers |
|---------|-----------|
| Email | SendGrid, Amazon SES, Postmark, Mailgun, Resend, SparkPost |
| SMS | Twilio, MessageBird, Vonage, Plivo, Telnyx |
| Push | Firebase Cloud Messaging (FCM), Apple Push Notification Service (APNs), Expo |
| Chat | Slack, Microsoft Teams |
| Messaging | WhatsApp Business API, Facebook Messenger |

## Frequently Asked Questions

**How do I send a notification with Courier?**  
Call `client.send.message({ message: { to, template, data } })` with the Node SDK (`@trycourier/courier`) or `client.send.message(message={...})` with the Python SDK (`trycourier`). Both SDKs read the API key from the `COURIER_API_KEY` environment variable by default. See the channel-specific guides for full examples.

**What's the difference between transactional and marketing notifications?**  
Transactional notifications are triggered by user actions (password reset, order confirmation). Marketing notifications are sent proactively for engagement.

**How do I handle notification preferences?**  
See `resources/guides/preferences.md` for implementing user preference centers, channel opt-outs, and frequency controls.

**How do I ensure email deliverability?**  
Configure SPF, DKIM, and DMARC. Warm up your sending domain. Monitor bounce rates. Full guide in `resources/channels/email.md`.

**What about rate limiting and throttling?**
Courier handles provider rate limits automatically. For frequency caps, use a journey `throttle` node — see `resources/guides/throttling.md`.

## Contributing

Found an issue or want to add a notification pattern? PRs welcome.

## License

[MIT](./LICENSE) © Courier, Inc.

---

Built for the [Courier](https://www.courier.com) notification platform. Works with any AI coding assistant that supports agent skills.
