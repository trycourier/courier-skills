# Courier Notification Skills

A comprehensive agent skill for building production-ready notification systems across multiple channels. Covers everything from email deliverability to push permission priming, with a focus on user experience, compliance, and reliability.

## Installation

Use your package manager or skill installer to add this skill to your project.

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

## License

MIT
