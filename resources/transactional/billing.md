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
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "PAYMENT_RECEIVED",
    data: {
      amount: "$99.00",
      date: "January 29, 2026",
      paymentMethod: "Visa •••• 4242",
      description: "Pro Plan - Monthly"
    }
  }
}, {
  idempotencyKey: `payment-pay_123abc`
});
```

**Dunning (Payment Failed):**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "PAYMENT_FAILED",
    data: {
      amount: "$99.00",
      reason: "Card declined",
      updateUrl: "https://acme.com/billing",
      daysUntilCancel: 14
    },
    routing: { method: "all", channels: ["email", "push"] }
  }
}, {
  idempotencyKey: `dunning-inv_123-day-7`
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

Payment fails → escalate over time:

| Day | Action | Channels |
|-----|--------|----------|
| 0 | Initial failure notice | Email |
| 3 | Retry notification | Email |
| 7 | Urgent action required | Email + Push |
| 14 | Final notice | Email + Push + SMS |
| 15+ | Subscription canceled | Email |

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

### Trial Ending

Send 3 days before trial ends. Channels: Email + Push.

Subject: Your free trial ends in 3 days

Include:
- Trial end date
- What happens after (charge amount)
- Benefits of continuing
- Continue button
- Change plans option
- Cancel option

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

Always use idempotency keys:
- `payment-{paymentId}`
- `invoice-{invoiceId}`
- `dunning-{invoiceId}-day-{day}`

## Related

- [Email](../channels/email.md) - Email design for receipts
- [SMS](../channels/sms.md) - SMS for urgent billing alerts
- [Reliability](../guides/reliability.md) - Idempotency for billing
- [Compliance](../guides/compliance.md) - Receipt requirements
