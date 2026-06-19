# Billing Notifications

## Quick Reference

### Rules
- Payment confirmation: Send within 1 minute of successful charge
- ALWAYS include amount, date, payment method (last 4 digits)
- Upcoming invoice: Send 3-7 days before charge
- Trial ending: Send 3 days before trial ends
- Dunning: Escalate over time (email → email+push → all channels)
- Deep link directly to payment update form

### Dunning Escalation Schedule
| Day | Action | Channels |
|-----|--------|----------|
| 0 | Initial failure notice | Email |
| 3 | Retry notification | Email |
| 7 | Urgent action required | Email + Push |
| 14 | Final notice | Email + Push + SMS |
| 15+ | Subscription canceled | Email |

### Idempotency Keys
| Notification | Key Pattern |
|--------------|-------------|
| Payment confirmation | `payment-{paymentId}` |
| Invoice | `invoice-{invoiceId}` |
| Dunning | `dunning-{invoiceId}-day-{day}` |
| Trial ending | `trial-ending-{userId}` |

### Common Mistakes
- Delayed payment confirmation (users worry)
- No PDF receipt download option
- Aggressive dunning tone (be helpful, not threatening)
- Not offering downgrade as alternative to cancel
- Missing idempotency keys (duplicate receipts)
- Hard-to-find "update payment" link
- No trial ending reminder

### Templates

**Payment Confirmation:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbr9m2t6qf8w3x5c7v1dh",
    data: {
      amount: "$99.00",
      date: "January 29, 2026",
      paymentMethod: "Visa •••• 4242",
      description: "Pro Plan - Monthly"
    }
  }
}, {
  headers: { "Idempotency-Key": `payment-pay_123abc` }
});
```

**Dunning (Payment Failed):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbret4v8n2q6x1c5d7wfj",
    data: {
      amount: "$99.00",
      reason: "Card declined",
      updateUrl: "https://acme.com/billing",
      daysUntilCancel: 14
    },
    routing: { method: "all", channels: ["email", "push"] }
  }
}, {
  headers: { "Idempotency-Key": `dunning-inv_123-day-7` }
});
```

---

Best practices for receipts, invoices, dunning, and subscription notifications.

## Payment Confirmations

### When to Send

Immediately after successful payment (within 1 minute).

### Content Requirements

- Amount charged
- Date and time
- Payment method (last 4 digits)
- What was purchased
- Invoice/receipt number
- PDF download link (if applicable)
- Support contact

### Email Content

Subject: Payment received - $99.00

Include:
- Payment success indicator
- Amount, date, payment method
- Description of purchase
- Invoice number
- Download/view receipt links
- Billing support contact

Always use idempotency keys (e.g., `payment-{paymentId}`) to prevent duplicate sends.

## Invoice Notifications

### Upcoming Invoice (Subscription)

Send 3-7 days before charge.

Subject: Your upcoming invoice - $99.00 on Feb 1

Include:
- Plan name and amount
- Billing date
- Current payment method
- Update payment method link
- Manage subscription link

### Invoice Finalized

For usage-based or finalized invoices.

Include:
- Invoice number
- Amount due
- Due date
- Line item breakdown
- PDF download link
- Payment link

## Dunning (Payment Failed)

### Strategy Overview

Payment fails → escalate over time using the schedule defined in [Quick Reference > Dunning Escalation Schedule](#dunning-escalation-schedule) above.

### Initial Payment Failed (Day 0)

Subject: Action required: Payment failed for your Acme subscription

Include:
- Amount that failed
- Plan name
- Reason (card declined, insufficient funds, etc.)
- Update payment method button
- Next retry date
- Support contact

### Escalation (Day 7)

Add push notification. Increase urgency in messaging.

Include:
- Days until cancellation
- Clear CTA to update payment

### Final Notice (Day 14)

Maximum urgency - use all channels: Email + Push + SMS.

SMS: "Acme: Your subscription will be canceled tomorrow unless you update payment. Update: acme.com/billing"

## Subscription Notifications

### Subscription Confirmed

Include:
- Plan name and price
- Billing interval (monthly/yearly)
- Start date
- Features included

### Plan Changed

Include:
- Previous plan
- New plan
- New price
- Effective date
- Proration amount (if applicable)

### Trial Ending / Renewal Reminder

A trial-ending or renewal-reminder ladder is the canonical multi-step billing flow. Build it as a [Journey](../guides/journeys.md) so the timing, status checks, and exit conditions live in one place.

**Cadence:**

| When | Channels | Purpose |
|------|----------|---------|
| 7 days before trial end / renewal | Email | First heads-up, room to change plans |
| 3 days before | Email + Push | Reminder with clear next steps |
| 1 day before | Email + Push | Final notice |
| After end | Email | Welcome (converted) or trial-expired (not converted) |

Each reminder must include trial/renewal end date, charge amount, "Continue", "Change plan", and "Cancel" actions. Skip later reminders if the user already converted, canceled, or disabled auto-renew.

**Journey DAG:**

```json
{
  "name": "Trial Ending Reminder",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger",
      "trigger_type": "api-invoke",
      "schema": {
        "type": "object",
        "properties": {
          "user_id": { "type": "string" },
          "subscription_id": { "type": "string" },
          "trial_end": { "type": "string" },
          "reminder_times": {
            "type": "object",
            "properties": {
              "seven_days_before": { "type": "string" },
              "three_days_before": { "type": "string" },
              "one_day_before": { "type": "string" },
              "after_end": { "type": "string" }
            }
          }
        },
        "required": ["user_id", "subscription_id", "trial_end", "reminder_times"]
      }
    },

    { "id": "wait-7d-before", "type": "delay", "mode": "until", "until": "{{reminder_times.seven_days_before}}" },
    {
      "id": "check-status-7d",
      "type": "fetch",
      "method": "get",
      "url": "https://api.yourapp.com/subscriptions/{{subscription_id}}/status",
      "merge_strategy": "overwrite"
    },
    {
      "id": "branch-status-7d",
      "type": "branch",
      "paths": [
        {
          "label": "Already converted or canceled",
          "conditions": ["data.subscription.status", "is not equal", "trialing"],
          "nodes": [{ "id": "exit-7d", "type": "exit" }]
        }
      ],
      "default": {
        "label": "Still trialing",
        "nodes": [
          { "id": "send-7d", "type": "send", "message": { "template": "<trial-7d-template-id>" } }
        ]
      }
    },

    { "id": "wait-3d-before", "type": "delay", "mode": "until", "until": "{{reminder_times.three_days_before}}" },
    {
      "id": "check-status-3d",
      "type": "fetch",
      "method": "get",
      "url": "https://api.yourapp.com/subscriptions/{{subscription_id}}/status",
      "merge_strategy": "overwrite"
    },
    {
      "id": "branch-status-3d",
      "type": "branch",
      "paths": [
        {
          "conditions": ["data.subscription.status", "is not equal", "trialing"],
          "nodes": [{ "id": "exit-3d", "type": "exit" }]
        }
      ],
      "default": {
        "nodes": [
          { "id": "send-3d", "type": "send", "message": { "template": "<trial-3d-template-id>" } }
        ]
      }
    },

    { "id": "wait-1d-before", "type": "delay", "mode": "until", "until": "{{reminder_times.one_day_before}}" },
    {
      "id": "check-status-1d",
      "type": "fetch",
      "method": "get",
      "url": "https://api.yourapp.com/subscriptions/{{subscription_id}}/status",
      "merge_strategy": "overwrite"
    },
    {
      "id": "branch-status-1d",
      "type": "branch",
      "paths": [
        {
          "conditions": ["data.subscription.status", "is not equal", "trialing"],
          "nodes": [{ "id": "exit-1d", "type": "exit" }]
        }
      ],
      "default": {
        "nodes": [
          { "id": "send-1d", "type": "send", "message": { "template": "<trial-1d-template-id>" } }
        ]
      }
    },

    { "id": "wait-after-end", "type": "delay", "mode": "until", "until": "{{reminder_times.after_end}}" },
    {
      "id": "check-status-final",
      "type": "fetch",
      "method": "get",
      "url": "https://api.yourapp.com/subscriptions/{{subscription_id}}/status",
      "merge_strategy": "overwrite"
    },
    {
      "id": "branch-final",
      "type": "branch",
      "paths": [
        {
          "label": "Converted to paid",
          "conditions": ["data.subscription.status", "is equal", "active"],
          "nodes": [
            { "id": "send-welcome-paid", "type": "send", "message": { "template": "<welcome-paid-template-id>" } },
            { "id": "exit-converted", "type": "exit" }
          ]
        }
      ],
      "default": {
        "label": "Trial expired",
        "nodes": [
          { "id": "send-expired", "type": "send", "message": { "template": "<trial-expired-template-id>" } },
          { "id": "exit-expired", "type": "exit" }
        ]
      }
    }
  ],
  "enabled": true
}
```

**Invoke when a trial starts (precompute the timestamps, mirror `user_id` into `data`):**

```typescript
function offsetISO(end: Date, days: number): string {
  return new Date(end.getTime() - days * 24 * 60 * 60 * 1000).toISOString();
}

const trialEnd = new Date("2026-06-01T00:00:00Z");

await client.journeys.invoke(JOURNEY_ID, {
  user_id: "user-123",
  profile: { email: "jane@example.com" },
  data: {
    user_id: "user-123",
    subscription_id: "sub_abc",
    trial_end: trialEnd.toISOString(),
    reminder_times: {
      seven_days_before: offsetISO(trialEnd, 7),
      three_days_before: offsetISO(trialEnd, 3),
      one_day_before: offsetISO(trialEnd, 1),
      after_end: trialEnd.toISOString(),
    },
  },
});
```

```python
from datetime import datetime, timedelta, timezone

trial_end = datetime(2026, 6, 1, tzinfo=timezone.utc)

def offset_iso(end: datetime, days: int) -> str:
    return (end - timedelta(days=days)).isoformat().replace("+00:00", "Z")

client.journeys.invoke(
    template_id=JOURNEY_ID,
    user_id="user-123",
    profile={"email": "jane@example.com"},
    data={
        "user_id": "user-123",
        "subscription_id": "sub_abc",
        "trial_end": trial_end.isoformat().replace("+00:00", "Z"),
        "reminder_times": {
            "seven_days_before": offset_iso(trial_end, 7),
            "three_days_before": offset_iso(trial_end, 3),
            "one_day_before": offset_iso(trial_end, 1),
            "after_end": trial_end.isoformat().replace("+00:00", "Z"),
        },
    },
)
```

**Why this shape:**
- `delay` `mode: "until"` schedules each reminder at an absolute time computed by your app — Courier doesn't compute "N days before" for you.
- The `fetch` node before each send is what makes this safe in production: a converted or canceled user stops getting reminders without any external cancel call.
- Each `send` node references a journey-scoped template (created via `POST /journeys/{id}/templates`). For per-template `name` vs Designer-managed copy, see [journeys.md](../guides/journeys.md) and [templates.md](../guides/templates.md).
- Use idempotent invocation keys at your application layer (one journey run per `subscription_id`) to avoid double-scheduling on retries.

### Subscription Canceled

Subject: Your Acme subscription has been canceled

Include:
- Plan that was canceled
- Access end date
- Resubscribe option
- Feedback request

## Usage Alerts

### Approaching Limit

Send when user reaches 80% of their limit.

Subject: You've used 80% of your API calls

Include:
- Current usage vs limit
- Percentage used
- Estimated time until limit reached
- View usage link
- Upgrade option

### Limit Reached

Channels: Email + Push + In-app

Include:
- What limit was reached
- When it resets
- Upgrade option
- Impact on service

## Channel Strategy

| Notification | Email | Push | SMS | Timing |
|--------------|-------|------|-----|--------|
| Payment successful | Yes | - | - | Immediate |
| Upcoming invoice | Yes | - | - | 3-7 days before |
| Payment failed (initial) | Yes | - | - | Immediate |
| Payment failed (escalation) | Yes | Yes | - | Day 7 |
| Payment failed (final) | Yes | Yes | Yes | Day 14 |
| Trial ending | Yes | Yes | - | 3 days before |
| Usage warning | Yes | Yes | - | At 80% |
| Usage limit reached | Yes | Yes | - | Immediate |

## Best Practices

### Clarity

- State amounts clearly
- Show what was purchased
- Include invoice number
- Provide easy access to PDF

### Payment Updates

- Deep link directly to payment update form
- Pre-fill what you can
- Make the process as short as possible

### Dunning

- Increase urgency gradually
- Be helpful, not threatening
- Offer alternatives (downgrade vs cancel)
- Make it easy to resolve

### Idempotency

Always use idempotency keys — see [Quick Reference > Idempotency Keys](#idempotency-keys) above for the key patterns.

## Related

- [Journeys](../guides/journeys.md) - Multi-step billing flows (trial ending, dunning, renewal reminders)
- [Email](../channels/email.md) - Email design for receipts
- [SMS](../channels/sms.md) - SMS for urgent billing alerts
- [Reliability](../guides/reliability.md) - Idempotency for billing
