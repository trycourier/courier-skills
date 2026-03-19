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

### Routing Edge Cases
| Situation | Behavior |
|-----------|----------|
| `user_id` has no email, email is first in `channels` | Skips email, tries next channel |
| `user_id` has no contact info at all | Message status: UNDELIVERABLE |
| User opted out of a channel via preferences | Channel skipped automatically |
| `routing` omitted entirely | Courier uses channels configured in the template |
| Provider returns 5xx | Courier retries, then tries next provider in priority order |
| All providers for a channel fail | With `method: "single"`, falls through to next channel |

### Common Mistakes
- Using `all` when `single` is appropriate (spams user on all channels)
- Not setting channel priority order correctly
- Missing fallback channels for critical notifications
- Sending same content to all channels (adapt per channel)
- Not respecting user preferences
- Forgetting idempotency keys (causes duplicates)

---

Orchestrate notifications across channels for maximum deliverability and engagement.

## Routing Methods

Courier provides two core routing methods:

### Single Channel (`method: "single"`)

Try channels in priority order until one succeeds. Best for most notifications where you want exactly one delivery.

**TypeScript:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "PASSWORD_RESET",
    routing: {
      method: "single",
      channels: ["email", "sms"]
    }
  }
});
```

**Python:**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "PASSWORD_RESET",
        "routing": {"method": "single", "channels": ["email", "sms"]},
    }
)
```

**Behavior:**
1. Attempt email delivery
2. If email fails (no email address, provider error), try SMS
3. Stop after first successful delivery

### All Channels (`method: "all"`)

Send to all specified channels simultaneously. Best for critical notifications.

**TypeScript:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "SECURITY_ALERT",
    routing: {
      method: "all",
      channels: ["email", "push", "sms"]
    }
  }
});
```

**Python:**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "SECURITY_ALERT",
        "routing": {"method": "all", "channels": ["email", "push", "sms"]},
    }
)
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

### Security Alert (Maximum Reach)

```typescript
// Critical - use all channels
await client.send.message({
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
await client.send.message({
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
await client.send.message({
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
await client.automations.invoke.invokeByTemplate("escalating-notification", {
  recipient: "user-123",
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
await client.send.message({
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
await client.send.message({
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
await client.send.message({
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
  items: [
    {
      topic_id: "weekly-digest",
      status: "OPTED_IN",
      has_custom_routing: true,
      custom_routing: ["email"]
    }
  ]
}
```

## Cross-Channel Coordination

### Deduplication

Prevent duplicate notifications with idempotency keys:

```typescript
await client.send.message({
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
  
  // Cancel the inbox notification to avoid duplicate engagement
  await client.messages.cancel(messageId);
  
  res.sendStatus(200);
});
```

### Cancellation

Cancel pending notifications if user takes action:

```typescript
// User completed action, cancel escalation
await client.automations.invoke.invokeAdHoc({
  recipient: userId,
  automation: {
    steps: [
      { action: "cancel", cancelation_token: `approval-${approvalId}` }
    ]
  }
});
```

## Provider Failover

### Setup (Dashboard)

1. Go to **Channels** in the [Courier dashboard](https://app.courier.com/channels)
2. Add multiple providers for the same channel type (e.g., two email providers)
3. Drag to set priority order — Courier tries top-to-bottom
4. Each provider needs its own credentials (API key, etc.)

```
Email Providers (Priority Order):
1. SendGrid (Primary)     ← tried first
2. Mailgun (Backup)       ← tried if SendGrid fails
3. AWS SES (Last resort)  ← tried if both fail

SMS Providers:
1. Twilio (Primary)
2. MessageBird (Backup)
```

### When Failover Triggers

Courier fails over to the next provider when:
- Provider returns a 5xx error (after built-in retries)
- Provider times out
- Provider-specific permanent error (e.g., invalid credentials)

Courier does NOT fail over for:
- Recipient-level failures (invalid email, bounced)
- Rate limiting (retries with backoff on same provider)
- Template rendering errors

### Checking Which Provider Was Used

Inspect the message delivery history to see which provider handled a send:

```bash
courier messages history --message-id "1-abc123" --format json
```

The history shows each provider attempt with timestamps and status.

### Provider-Specific Overrides

Pass provider-level configuration without changing dashboard settings:

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "OTP_CODE",
    providers: {
      twilio: {
        override: {
          messaging_service_sid: "MG..."
        }
      },
      sendgrid: {
        override: {
          ip_pool_name: "transactional"
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
