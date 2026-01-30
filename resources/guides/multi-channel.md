# Multi-Channel Routing

## Quick Reference

### Rules
- `method: "single"`: Try channels in order until one succeeds (use for most cases)
- `method: "all"`: Send to all channels simultaneously (use for critical alerts)
- Each channel requires user to have valid contact info (email, phone, push token)
- Channel order in array = priority order for fallbacks
- Courier auto-checks user preferences when configured
- Use idempotency keys to prevent duplicate sends across retries

### Channel Selection by Use Case
| Use Case | Method | Channels |
|----------|--------|----------|
| OTP/2FA | single | [sms, email] |
| Password reset | single | [email] |
| Order confirmation | single | [email] |
| Order shipped | all | [email, push, inbox] |
| Security alert | all | [email, push, sms, inbox] |
| Activity mention | all | [push, inbox] |
| Weekly digest | single | [email] |

### Common Mistakes
- Using `all` when `single` is appropriate (spams user on all channels)
- Not setting channel priority order correctly
- Missing fallback channels for critical notifications
- Sending same content to all channels (adapt per channel)
- Not respecting user preferences
- Forgetting idempotency keys (causes duplicates)

### Templates

**Single with Fallback:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "OTP_CODE",
    routing: {
      method: "single",
      channels: ["sms", "email"]
    }
  }
});
```

**All Channels (Critical):**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "SECURITY_ALERT",
    routing: {
      method: "all",
      channels: ["email", "push", "sms", "inbox"]
    }
  }
});
```

---

Orchestrate notifications across channels for maximum deliverability and engagement.

## Routing Methods

Courier provides two core routing methods:

### Single Channel (`method: "single"`)

Try channels in priority order until one succeeds. Best for most notifications where you want exactly one delivery.

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "PASSWORD_RESET",
    routing: {
      method: "single",
      channels: ["email", "sms"] // Try email first, SMS if email fails
    }
  }
});
```

**Behavior:**
1. Attempt email delivery
2. If email fails (no email address, provider error), try SMS
3. Stop after first successful delivery

### All Channels (`method: "all"`)

Send to all specified channels simultaneously. Best for critical notifications.

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "SECURITY_ALERT",
    routing: {
      method: "all",
      channels: ["email", "push", "sms"] // Send to all three
    }
  }
});
```

**Behavior:**
- Attempts delivery to all channels in parallel
- Each channel is independent (one failure doesn't affect others)
- User receives on all channels where they have valid contact info

## Channel Priority Matrix

### By Urgency

| Urgency | Strategy | Channels | Example |
|---------|----------|----------|---------|
| Critical | All channels | Email + Push + SMS + In-app | Account compromised |
| High | Primary + aggressive fallback | Push → SMS → Email | OTP code |
| Medium | Best single channel | Email or Push | Order shipped |
| Low | Least intrusive | In-app only | Weekly digest available |

### By Notification Type

| Notification | Primary | Secondary | Rationale |
|--------------|---------|-----------|-----------|
| **OTP/2FA** | SMS | Email | Speed, visibility, works offline |
| **Password reset** | Email | - | Secure link delivery |
| **Order confirmed** | Email | In-app | Receipt for records |
| **Order shipped** | Email + Push | - | Detail + awareness |
| **Out for delivery** | Push + SMS | - | Real-time, actionable |
| **Security alert** | All | - | Maximum reach |
| **Direct message** | Push | In-app | Immediate, conversational |
| **Comment/mention** | Push | In-app | Immediate, contextual |
| **Likes (batched)** | In-app | - | Low priority, batch |
| **Weekly digest** | Email | - | Long-form content |
| **Appointment reminder** | SMS + Push | Email | Time-sensitive |

## Channel Selection Examples

### Password Reset

```typescript
// Email only - secure link delivery
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "PASSWORD_RESET",
    data: { 
      resetUrl: "https://acme.com/reset?token=abc123",
      expiresIn: "1 hour"
    },
    routing: {
      method: "single",
      channels: ["email"]
    }
  }
});
```

### OTP Code with Fallback

```typescript
// SMS preferred, email fallback
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "OTP_CODE",
    data: { code: "847293" },
    routing: {
      method: "single",
      channels: ["sms", "email"] // Try SMS first
    }
  }
});
```

### Security Alert (Maximum Reach)

```typescript
// Critical - use all channels
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "SECURITY_ALERT",
    data: {
      alertType: "new_login",
      device: "Chrome on Windows",
      location: "New York, USA",
      time: new Date().toISOString()
    },
    routing: {
      method: "all",
      channels: ["email", "push", "sms", "inbox"]
    }
  }
});
```

### Order Shipped

```typescript
// Email for details, push for awareness
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_SHIPPED",
    data: {
      orderNumber: "12345",
      trackingUrl: "https://acme.co/track/12345",
      carrier: "FedEx",
      estimatedDelivery: "Thursday, Jan 30"
    },
    routing: {
      method: "all",
      channels: ["email", "push", "inbox"]
    }
  }
});
```

### Activity Notification

```typescript
// Push for immediate, inbox for persistence
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "NEW_COMMENT",
    data: {
      commenterName: "Jane",
      commentPreview: "Great point about the API design!",
      postId: "post-456"
    },
    routing: {
      method: "all",
      channels: ["push", "inbox"]
    }
  }
});
```

## Escalation Patterns

### Time-Based Escalation

Start with less intrusive channel, escalate if no engagement:

```
T+0:      In-app notification
T+15min:  Push notification (if unread)
T+1hr:    Email (if still unread)
T+24hr:   SMS (if critical and still unread)
```

**Implementation with Courier Automations:**

```typescript
// Invoke automation that handles escalation
await courier.automations.invoke("escalating-notification", {
  user_id: "user-123",
  data: {
    template: "APPROVAL_REQUEST",
    approvalId: "apr-789",
    requestedBy: "Jane"
  }
});
```

Configure the automation in Courier dashboard:
1. Send to In-app
2. Wait 15 minutes
3. Check if read → If not, send Push
4. Wait 1 hour
5. Check if read → If not, send Email

### Delivery-Based Escalation

Automatically try next channel when delivery fails:

```typescript
// Single routing method handles this automatically
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "IMPORTANT_UPDATE",
    routing: {
      method: "single",
      channels: ["push", "email", "sms"] // Fallback chain
    }
  }
});
```

**Failure reasons that trigger fallback:**
- Missing contact info (no email address, no phone, no push token)
- Provider error (temporary or permanent)
- Invalid recipient (bounced email, invalid phone)

## Channel-Specific Formatting

Same notification, optimized for each channel:

### Email (Detailed)

```typescript
channels: {
  email: {
    override: {
      subject: "Your order #12345 has shipped",
      body: {
        // Rich HTML with images, tracking details, etc.
      }
    }
  }
}
```

### Push (Concise)

```typescript
channels: {
  push: {
    override: {
      title: "Order shipped!",
      body: "Arriving Thursday. Tap to track.",
      data: { deepLink: "acme://orders/12345" }
    }
  }
}
```

### SMS (Ultra-Short)

```typescript
channels: {
  sms: {
    override: {
      body: "Acme: Order #12345 shipped! Arrives Thu. Track: acme.co/t/12345"
    }
  }
}
```

### Complete Multi-Channel Example

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_SHIPPED",
    data: {
      orderNumber: "12345",
      carrier: "FedEx",
      trackingNumber: "TRACK123",
      estimatedDelivery: "Thursday, January 30",
      items: [
        { name: "Widget Pro", quantity: 2 }
      ]
    },
    routing: {
      method: "all",
      channels: ["email", "push", "inbox"]
    },
    channels: {
      email: {
        override: {
          subject: "Your order #12345 has shipped!"
        }
      },
      push: {
        override: {
          title: "Order shipped! 📦",
          body: "Arriving Thursday. Tap to track.",
          data: {
            deepLink: "acme://orders/12345",
            image: "https://acme.com/images/package.png"
          }
        }
      }
    }
  }
});
```

## User Preferences Integration

### Respect User Choices

Let users control which channels they receive:

```typescript
// Check preferences before routing
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "WEEKLY_DIGEST",
    routing: {
      method: "single",
      channels: ["email", "inbox"] // Courier filters by user preference
    }
  }
});
```

Courier automatically checks user preferences and filters channels.

### Set Up Preference Topics

1. Create topics in Courier dashboard (Settings → Preferences)
2. Link templates to topics
3. Courier checks preferences before delivery

```typescript
// User's preference might be:
{
  topics: {
    "weekly-digest": {
      status: "OPTED_IN",
      channels: {
        email: true,
        push: false,
        sms: false
      }
    }
  }
}
```

## Cross-Channel Coordination

### Deduplication

Prevent duplicate notifications with idempotency keys:

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_SHIPPED",
    data: { orderId: "12345" }
  }
}, {
  idempotencyKey: `order-shipped-12345`
});
```

### Read State Sync

Mark notification as read across channels when user engages with one:

```typescript
// When user opens email
app.post('/webhooks/email-opened', async (req, res) => {
  const { messageId, userId } = req.body;
  
  // Mark the corresponding inbox notification as read
  await courier.messages.read(messageId);
  
  res.sendStatus(200);
});
```

### Cancellation

Cancel pending notifications if user takes action:

```typescript
// User completed action, cancel escalation
await courier.automations.cancel({
  cancelation_token: `approval-${approvalId}`
});
```

## Provider Failover

### Multiple Providers per Channel

Configure backup providers in Courier dashboard:

```
Email Providers (Priority Order):
1. SendGrid (Primary)
2. Mailgun (Backup)
3. AWS SES (Last resort)

SMS Providers:
1. Twilio (Primary)
2. MessageBird (Backup)
```

Courier automatically tries the next provider if one fails.

### Provider-Specific Overrides

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "OTP_CODE",
    providers: {
      twilio: {
        override: {
          messaging_service_sid: "MG..."
        }
      }
    }
  }
});
```

## Monitoring & Analytics

### Track Per Channel

| Metric | What It Tells You |
|--------|-------------------|
| Delivery rate | % successfully delivered |
| Open/read rate | User engagement |
| Click-through rate | Action taken |
| Bounce/failure rate | Data quality issues |
| Unsubscribe rate | Channel fatigue |

### Track Routing Effectiveness

```typescript
// Analyze which channels perform best
const analytics = {
  notification: "order_shipped",
  channels: {
    email: { sent: 10000, opened: 4500, clicked: 2000 },
    push: { sent: 8000, opened: 6000, clicked: 3500 },
    sms: { sent: 5000, clicked: 2500 }
  }
};

// Push has highest engagement for this notification type
// Consider making push primary
```

## Best Practices

### Do

- **Match channel to content:** Long content → email, urgent → push/SMS
- **Respect preferences:** Let users choose their channels
- **Use fallbacks:** Have backup channels for critical notifications
- **Adapt content:** Optimize message for each channel's constraints
- **Track performance:** Monitor per-channel metrics

### Don't

- **Spam all channels:** Sending same notification everywhere annoys users
- **Ignore context:** User active in app? Don't also send email
- **Over-escalate:** Not everything needs SMS
- **Forget mobile:** 60%+ of notifications read on mobile

## Quick Reference

| Use Case | Recommended Approach |
|----------|---------------------|
| OTP/2FA | `single` → [sms, email] |
| Password reset | `single` → [email] |
| Order confirmation | `single` → [email] |
| Order shipped | `all` → [email, push, inbox] |
| Delivery update | `all` → [push, sms] |
| Security alert | `all` → [email, push, sms, inbox] |
| Direct message | `all` → [push, inbox] |
| Activity mention | `all` → [push, inbox] |
| Weekly digest | `single` → [email] |
| Appointment reminder | `all` → [sms, push] |

## Related

- [Preferences](./preferences.md) - User channel preferences
- [Reliability](./reliability.md) - Failover and retry logic
- [Batching](./batching.md) - Combining notifications
- [Throttling](./throttling.md) - Rate limiting per channel
- [Email](../channels/email.md) - Email-specific guidance
- [SMS](../channels/sms.md) - SMS-specific guidance
- [Push](../channels/push.md) - Push notification guidance
- [Inbox](../channels/inbox.md) - In-app notifications
- [Slack](../channels/slack.md) - Slack integration
- [MS Teams](../channels/ms-teams.md) - Teams integration
- [WhatsApp](../channels/whatsapp.md) - WhatsApp integration
