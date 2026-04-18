# Courier Notification Skills

A comprehensive agent skill for building production-ready notification systems across multiple channels. Covers everything from email deliverability to push permission priming, with a focus on user experience and reliability.

> **For AI Agents & Developers**: This skill provides structured guidance for implementing notifications with the [Courier API](https://www.courier.com). Use it to send emails, SMS, push notifications, Slack messages, and more through a unified interface.

## Why Use This Skill

- **Multi-channel notifications** — Send messages via email, SMS, push, Slack, Microsoft Teams, WhatsApp, and in-app inbox from a single API
- **Production-ready patterns** — Battle-tested code examples for authentication flows, order updates, billing alerts, and more
- **Developer-first** — TypeScript, Python, CLI, and curl examples for key patterns

## Who This Is For

- Developers building SaaS, e-commerce, marketplaces, or mobile apps
- Teams consolidating notification providers into a single API
- Engineers implementing user preferences, unsubscribe handling, or multi-channel routing

## Installation

**Cursor** (global, available in all projects):

```bash
git clone https://github.com/trycourier/courier-skills.git ~/.cursor/skills/courier-skills
```

**Cursor** (project-specific):

```bash
git clone https://github.com/trycourier/courier-skills.git .cursor/skills/courier-skills
```

**Claude Code**:

```bash
git clone https://github.com/trycourier/courier-skills.git ~/.claude/skills/courier-skills
```

Claude Code discovers skills from `~/.claude/skills/` automatically. The skill's `SKILL.md` frontmatter (`name` and `description` fields) is used for discovery — no additional configuration needed.

**Other AI Assistants** (Windsurf, Cline, etc.):

Clone to the skill directory supported by your assistant, or point it at the `SKILL.md` file manually. The skill follows standard markdown conventions and works with any AI coding tool that supports agent skills.

## What This Skill Covers

**Channels**
- Email (deliverability, SPF/DKIM/DMARC, design)
- SMS (10DLC registration, character limits)
- Push notifications (iOS/Android, permission priming)
- In-app inbox (real-time, badges, read states)
- Slack (Block Kit, bot setup)
- Microsoft Teams (Adaptive Cards)
- WhatsApp (templates, 24hr window)

**Transactional Notifications**
- Authentication (password reset, OTP, verification, security alerts)
- Orders (confirmation, shipping, delivery)
- Billing (receipts, dunning, subscriptions)
- Appointments (booking, reminders, rescheduling)
- Account (welcome, profile updates, settings)

**Growth Notifications**
- Onboarding (activation, first value, setup)
- Feature adoption (discovery, education, milestones)
- Engagement (activity, retention, habits)
- Re-engagement (winback, cart abandonment)
- Referral (viral loops, invites, rewards)
- Campaigns (promotional, upgrades)

**Cross-Cutting Guides**
- Quickstart (send your first notification)
- Multi-channel orchestration and routing
- User preference management
- Reliability (idempotency, retry logic, webhook signature verification)
- Batching and digests
- Throttling and rate limiting
- Notification catalog by app type
- Template management (CRUD, versioning, publish lifecycle)
- Elemental content format (element types, control flow, localization)
- Reusable code patterns (idempotency, consent, quiet hours, masking, retry)
- CLI (ad-hoc operations, debugging, agent workflows)
- MCP Server (structured API access for AI agents, setup for all editors)
- General migration (from any custom or third-party system)
- Migrate from Knock (concept mapping, code migration)
- Migrate from Novu (concept mapping, code migration)

## Structure

```
courier-skills/
├── SKILL.md                    # Start here - routes to the right resource
├── README.md                   # This file
└── resources/
    ├── channels/               # Channel-specific best practices
    │   ├── email.md
    │   ├── sms.md
    │   ├── push.md
    │   ├── inbox.md
    │   ├── inbox-v7-legacy.md
    │   ├── slack.md
    │   ├── ms-teams.md
    │   └── whatsapp.md
    ├── transactional/          # Transactional notification types
    │   ├── index.md
    │   ├── authentication.md
    │   ├── orders.md
    │   ├── billing.md
    │   ├── appointments.md
    │   └── account.md
    ├── growth/                 # Growth & lifecycle notifications
    │   ├── index.md
    │   ├── onboarding.md
    │   ├── adoption.md
    │   ├── engagement.md
    │   ├── reengagement.md
    │   ├── referral.md
    │   └── campaigns.md
    └── guides/                 # Cross-cutting concerns
        ├── quickstart.md
        ├── cli.md
        ├── mcp.md
        ├── multi-channel.md
        ├── preferences.md
        ├── reliability.md
        ├── batching.md
        ├── throttling.md
        ├── catalog.md
        ├── templates.md
        ├── routing-strategies.md
        ├── providers.md
        ├── elemental.md
        ├── patterns.md
        ├── migrate-general.md
        ├── migrate-from-knock.md
        └── migrate-from-novu.md
```

## Quick Start

Open `SKILL.md` - it has a routing table that directs you to the right resource based on what you need to do.

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
Courier handles provider rate limits automatically. For custom throttling logic, see `resources/guides/throttling.md`.

## Contributing

Found an issue or want to add a notification pattern? PRs welcome.

## License

[MIT](./LICENSE) © Courier, Inc.

---

Built for the [Courier](https://www.courier.com) notification platform. Works with any AI coding assistant that supports agent skills.
