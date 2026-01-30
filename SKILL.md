---
name: courier-notification-skills
description: Use when building notifications across email, SMS, push, in-app, Slack, Teams, or WhatsApp. Covers transactional messages (password reset, OTP, orders, billing), growth notifications (onboarding, engagement, referral), multi-channel routing, compliance (GDPR, TCPA, CAN-SPAM), and reliability patterns.
---

# Courier Notification Skills

Guidance for building deliverable, compliant, and engaging notifications across all channels.

> Use the routing tables below to find implementation details for your specific task.

## Official Courier Documentation

For complete and current documentation, fetch the index at:
https://www.courier.com/docs/llms.txt

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
| Route across multiple channels, set up fallbacks | [Multi-Channel](./resources/guides/multi-channel.md) |
| Manage user notification preferences | [Preferences](./resources/guides/preferences.md) |
| Ensure GDPR, TCPA, CAN-SPAM compliance | [Compliance](./resources/guides/compliance.md) |
| Handle retries, idempotency, error recovery | [Reliability](./resources/guides/reliability.md) |
| Combine notifications, build digests | [Batching](./resources/guides/batching.md) |
| Control frequency, prevent fatigue | [Throttling](./resources/guides/throttling.md) |
| Plan notifications for your app type | [Catalog](./resources/guides/catalog.md) |

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
| In-app inbox setup | [inbox.md](./resources/channels/inbox.md) |
| Onboarding sequence | [onboarding.md](./resources/growth/onboarding.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Security alerts | [authentication.md](./resources/transactional/authentication.md), [multi-channel.md](./resources/guides/multi-channel.md) |
| Digest/batching | [batching.md](./resources/guides/batching.md), [preferences.md](./resources/guides/preferences.md) |
| Payment/billing notifications | [billing.md](./resources/transactional/billing.md), [reliability.md](./resources/guides/reliability.md) |
| Appointment reminders | [appointments.md](./resources/transactional/appointments.md), [sms.md](./resources/channels/sms.md) |
| WhatsApp templates | [whatsapp.md](./resources/channels/whatsapp.md) |
| Slack/Teams integration | [slack.md](./resources/channels/slack.md) or [ms-teams.md](./resources/channels/ms-teams.md) |

## Start Here

**New app?**
Start with the [Catalog](./resources/guides/catalog.md) to plan which notifications your app needs, then set up [Email deliverability](./resources/channels/email.md) and review [Multi-Channel routing](./resources/guides/multi-channel.md).

**Building transactional notifications?**
Check [Transactional Overview](./resources/transactional/index.md) for principles, then dive into the specific type you're building (authentication, orders, billing, appointments, or account).

**Building growth notifications?**
Check [Growth Overview](./resources/growth/index.md) to understand consent requirements and lifecycle stages, then dive into onboarding, adoption, engagement, re-engagement, referral, or campaigns.

**Compliance concerns?**
Review [Compliance](./resources/guides/compliance.md) for regulations by channel, then check channel-specific requirements in [SMS](./resources/channels/sms.md) (TCPA/10DLC) and [Email](./resources/channels/email.md) (CAN-SPAM).

**Deliverability issues?**
For email going to spam, check [Email](./resources/channels/email.md). For SMS delivery issues, check [SMS](./resources/channels/sms.md) for 10DLC registration requirements.
