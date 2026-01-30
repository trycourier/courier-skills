# Transactional Notifications

## Quick Reference

### Rules
- Transactional = triggered by user action, expected, required for service
- NO promotional content allowed (reclassifies as marketing, requires opt-in)
- No explicit opt-in required (implied consent from action)
- Send immediately or near-immediately
- ALWAYS use idempotency keys

### Timing Requirements
| Type | Delivery Time |
|------|---------------|
| OTP/2FA | < 10 seconds |
| Password reset | < 30 seconds |
| Order confirmation | < 1 minute |
| Security alert | < 1 minute |
| Shipping notification | < 5 minutes |

### Channel Selection
| Type | Primary | Fallback |
|------|---------|----------|
| OTP | SMS | Email |
| Password reset | Email | - |
| Order confirmation | Email | - |
| Shipping | Email + Push | - |
| Security alert | All channels | - |

### Common Mistakes
- Adding promotional content ("Use code SAVE20 on your next order!")
- Not using idempotency keys (causes duplicate sends)
- Slow delivery (users expect immediate)
- Missing essential information (order number, tracking link)
- No "I didn't request this" option in security emails
- Allowing opt-out from critical transactional (security, receipts)

### Template

**Transactional Send with Idempotency:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_CONFIRMATION",
    data: { orderId: "12345", items: [...] }
  }
}, {
  idempotencyKey: `order-confirmation-12345`
});
```

---

Core principles for sending transactional notifications that users expect and trust.

## What Makes a Notification Transactional?

Transactional notifications are:
- **Triggered by user action** or system event (not marketing campaigns)
- **Expected by the user** (they initiated something)
- **Required for service delivery** (order confirmations, OTPs, etc.)
- **Time-sensitive** (deliver immediately or near-immediately)

## Legal Definition

Under CAN-SPAM and GDPR, transactional notifications:
- **Do not require explicit opt-in** (implied consent from action)
- **Cannot contain promotional content** (or they become marketing)
- **Must be primarily informational** (confirm, update, alert)

### The FTC Test

Per the FTC's CAN-SPAM guidance, a message is transactional if it:
1. Facilitates or confirms a transaction the user agreed to
2. Provides information about an ongoing relationship
3. Delivers goods/services the user is entitled to receive
4. Provides account information (balance, usage, etc.)
5. Informs about changes to terms/features the user is using

**If you add promotional content**, the message is reclassified as marketing and requires opt-in.

## Categories

| Category | Examples | See |
|----------|----------|-----|
| Authentication | Password reset, OTP, verification, security alerts | [Authentication](./authentication.md) |
| Orders | Order confirmation, shipping, delivery, returns | [Orders](./orders.md) |
| Billing | Receipts, invoices, dunning, subscriptions | [Billing](./billing.md) |
| Appointments | Booking confirmations, reminders, rescheduling | [Appointments](./appointments.md) |
| Account | Welcome (non-promo), profile updates, settings | [Account](./account.md) |

## Core Principles

### 1. Immediate Delivery

Transactional notifications should be sent in real-time or near real-time:

| Type | Expected Delivery |
|------|-------------------|
| OTP/2FA codes | < 10 seconds |
| Password reset | < 30 seconds |
| Order confirmation | < 1 minute |
| Shipping notification | < 5 minutes |
| Security alert | < 1 minute |

**Use idempotency keys** to prevent duplicates while allowing safe retries:

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_CONFIRMATION",
    data: { orderId: "12345", items: [...] }
  }
}, {
  idempotencyKey: `order-confirmation-12345`
});
```

### 2. Clarity Over Creativity

Users need to understand and act quickly.

**Good:** Subject "Reset your password for Acme" with body "Click to reset your password. Link expires in 1 hour."

**Bad:** Subject "Important Security Update!" with body "We noticed something about your account..."

### 3. No Promotional Content

Keep transactional messages purely informational.

**Good (transactional):** "Your order #12345 has shipped. Track at acme.co/track/12345"

**Bad (now requires opt-in):** "Your order shipped! PS: Use code SAVE20 on your next order!"

### 4. Include Essential Information

| Notification Type | Must Include |
|-------------------|--------------|
| Password reset | Reset link, expiration, "I didn't request this" |
| OTP | Code, expiration, don't share warning |
| Order confirmation | Order number, items, total, estimated delivery |
| Shipping | Tracking number, carrier, estimated arrival |
| Payment receipt | Amount, date, payment method, what was purchased |

## Channel Selection

### By Urgency

| Urgency | Primary Channel | Backup |
|---------|----------------|--------|
| Critical (OTP, security) | SMS | Email |
| High (password reset) | Email | SMS |
| Medium (shipping) | Email + Push | - |
| Standard (receipts) | Email | In-app |

### By Type

- **OTP codes:** SMS primary, email fallback
- **Order shipped:** Email + Push (all channels)
- **Security alerts:** Email + Push + SMS (all channels for maximum reach)

## Subject Line Patterns

### Password Reset
- Reset your password for [App]
- [App] password reset request
- Your [App] password reset link

### Order Confirmation
- Order #12345 confirmed
- Your [App] order is confirmed
- Thanks for your order (#12345)

### Shipping
- Your order has shipped
- Order #12345 is on the way
- Your package shipped - arriving Thursday

### Payment
- Payment received - $99.00
- Receipt for your purchase
- Payment confirmation for [App]

## Error States

### What Users Need

**Resend functionality:**
- Allow after 60 seconds
- Limit attempts (3 per hour)
- Show countdown timer

**Expired links:**
- Clear "expired" message
- Offer to send new link
- Provide support contact

**"I didn't request this":**
- Include in password resets, OTPs, security alerts
- Link to security contact
- Log clicks for monitoring

## Testing

### Test Matrix

Test each transactional notification for:
- Delivery within expected time
- Correct content/data
- Mobile rendering
- Link functionality
- Expiration behavior
- Error states

## Related

- [Reliability](../guides/reliability.md) - Idempotency and retry patterns
- [Compliance](../guides/compliance.md) - Legal requirements
- [Multi-Channel](../guides/multi-channel.md) - Channel routing strategies
