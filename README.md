# Courier Notification Skills

A comprehensive agent skill for building production-ready notification systems across multiple channels. Covers everything from email deliverability to push permission priming, with a focus on user experience, compliance, and reliability.

> **For AI Agents & Developers**: This skill provides structured guidance for implementing notifications with the [Courier API](https://www.courier.com). Use it to send emails, SMS, push notifications, Slack messages, and more through a unified interface.

## Why Use This Skill

- **Multi-channel notifications** — Send messages via email, SMS, push, Slack, Microsoft Teams, WhatsApp, and in-app inbox from a single API
- **Production-ready patterns** — Battle-tested code examples for authentication flows, order updates, billing alerts, and more
- **Compliance built-in** — GDPR, TCPA, CAN-SPAM, and CCPA guidance for every channel
- **Developer-first** — TypeScript/JavaScript, Python, Ruby, Go, and cURL examples throughout

## Who This Is For

- Developers building SaaS, e-commerce, marketplaces, or mobile apps
- Teams consolidating notification providers into a single API
- Engineers implementing user preferences, unsubscribe handling, or multi-channel routing

## Installation

**Cursor** (global, available in all projects):

```bash
git clone https://github.com/trycourier/courier-skills.git ~/.cursor/skills/courier-skills
```

**Project-specific** (add to a single project):

```bash
git clone https://github.com/trycourier/courier-skills.git .cursor/skills/courier-skills
```

Also works with Windsurf, Cline, and other AI coding assistants that support skills.

## What This Skill Covers

**Channels**
- Email (deliverability, SPF/DKIM/DMARC, design)
- SMS (TCPA, 10DLC, character limits)
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
- Multi-channel orchestration and routing
- User preference management
- Compliance (GDPR, TCPA, CAN-SPAM)
- Reliability (idempotency, retry logic)
- Batching and digests
- Throttling and rate limiting
- Notification catalog by app type

## Structure

```
courier-notification-skills/
├── SKILL.md                    # Start here - routes to the right resource
├── README.md                   # This file
├── package.json                # npm package config
└── resources/
    ├── channels/               # Channel-specific best practices
    │   ├── email.md
    │   ├── sms.md
    │   ├── push.md
    │   ├── inbox.md
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
        ├── multi-channel.md
        ├── preferences.md
        ├── compliance.md
        ├── reliability.md
        ├── batching.md
        ├── throttling.md
        └── catalog.md
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
| Chat | Slack, Microsoft Teams, Discord |
| Messaging | WhatsApp Business API, Facebook Messenger |

## Frequently Asked Questions

**How do I send a notification with Courier?**  
Use the `courier.send()` method with a recipient, template, and data object. See the channel-specific guides for examples.

**What's the difference between transactional and marketing notifications?**  
Transactional notifications are triggered by user actions (password reset, order confirmation). Marketing notifications are sent proactively for engagement. Different compliance rules apply.

**How do I handle notification preferences?**  
See `resources/guides/preferences.md` for implementing user preference centers, channel opt-outs, and frequency controls.

**How do I ensure email deliverability?**  
Configure SPF, DKIM, and DMARC. Warm up your sending domain. Monitor bounce rates. Full guide in `resources/channels/email.md`.

**What about rate limiting and throttling?**
Courier handles provider rate limits automatically. For custom throttling logic, see `resources/guides/throttling.md`.

## Contributing

Found an issue or want to add a notification pattern? PRs welcome.

## License

MIT

---

Built for the [Courier](https://www.courier.com) notification platform. Works with any AI coding assistant that supports agent skills.
