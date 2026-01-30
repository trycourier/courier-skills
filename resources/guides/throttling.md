# Notification Throttling

## Quick Reference

### Rules
- NEVER throttle: OTP, security alerts, critical system notifications
- Critical notifications bypass all throttle limits
- Respect quiet hours: 10pm-8am local time (unless urgent)
- Different limits per channel and category
- Queue excess notifications for later (don't drop critical ones)

### Recommended Limits by Channel
| Channel | Limit | Window |
|---------|-------|--------|
| Push | 5-10 | Per hour |
| Email | 3-5 | Per day |
| SMS | 2-3 | Per day |
| In-app | 20-50 | Per hour |

### Priority Levels
| Priority | Examples | Throttle? |
|----------|----------|-----------|
| Critical | Security, OTP | NEVER |
| High | DMs, mentions | Minimal |
| Medium | Comments, likes | Standard |
| Low | Digests, promos | Aggressive |

### Common Mistakes
- Throttling critical/security notifications
- Same throttle limits for all notification types
- Dropping notifications instead of queuing
- Not tracking per-user notification counts
- Ignoring user timezone for quiet hours
- No alerting when throttle rate is too high

### Templates

**Check Throttle:**
```typescript
async function shouldSend(userId: string, priority: string): Promise<boolean> {
  if (priority === 'critical') return true;
  
  const count = await getNotificationCount(userId, '1h');
  const limits = { high: 20, medium: 10, low: 5 };
  return count < limits[priority];
}
```

**Quiet Hours Check:**
```typescript
function isQuietHours(timezone: string): boolean {
  const hour = new Date().toLocaleString('en-US', { 
    timeZone: timezone, hour: 'numeric', hour12: false 
  });
  return parseInt(hour) >= 22 || parseInt(hour) < 8;
}
```

---

Control notification frequency to prevent overwhelming users and respect rate limits.

## Why Throttle?

- **Prevent fatigue:** Too many notifications = users disable them
- **Respect rate limits:** Providers have sending limits
- **Improve engagement:** Well-timed notifications perform better
- **Reduce costs:** Fewer unnecessary sends

## Throttling vs Batching

| Concept | Purpose | Mechanism |
|---------|---------|-----------|
| **Throttling** | Limit frequency | Drop or delay excess |
| **Batching** | Combine related | Aggregate into one |

Use both together for optimal notification delivery.

## Throttling Strategies

### 1. Per-User Rate Limiting

Limit notifications per user over a time window.

```typescript
// Example: Max 10 notifications per hour per user
const WINDOW_MS = 60 * 60 * 1000; // 1 hour
const MAX_PER_WINDOW = 10;

async function shouldSendNotification(userId: string): Promise<boolean> {
  const recentCount = await getNotificationCount(userId, WINDOW_MS);
  return recentCount < MAX_PER_WINDOW;
}
```

**Recommended limits by channel:**

| Channel | Suggested Limit | Window |
|---------|-----------------|--------|
| Push | 5-10 | Per hour |
| Email | 3-5 | Per day |
| SMS | 2-3 | Per day |
| In-app | 20-50 | Per hour |

### 2. Per-Category Throttling

Different limits for different notification types:

```typescript
const THROTTLE_CONFIG = {
  'social': { maxPerHour: 10, maxPerDay: 30 },
  'marketing': { maxPerDay: 1 },
  'transactional': { maxPerHour: 20 }, // Higher limit
  'alerts': { maxPerHour: 5 }
};
```

### 3. Global Rate Limiting

Protect against system-wide spikes:

```typescript
// Circuit breaker pattern
const GLOBAL_MAX_PER_SECOND = 1000;

if (await getGlobalSendRate() > GLOBAL_MAX_PER_SECOND) {
  await queueForLater(notification);
} else {
  await sendNow(notification);
}
```

## Courier Throttling Features

### Send Limits

Configure send limits in Courier to automatically throttle:

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ACTIVITY_UPDATE",
    data: { ... },
    // Courier respects configured limits
    metadata: {
      tags: ["social", "low-priority"]
    }
  }
});
```

### Automation Throttling

Use Courier Automations to add delays and limits:

```typescript
// Invoke automation with throttle context
await courier.automations.invoke("activity-notification", {
  user_id: "user-123",
  data: { ... }
});
```

Configure in dashboard:
1. **Throttle step:** Max 5 per hour per user
2. **Delay step:** Wait if limit exceeded
3. **Send step:** Deliver notification

### Channel-Level Throttling

Set different limits per channel in your routing:

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "WEEKLY_SUMMARY",
    routing: {
      method: "single",
      channels: ["email"] // Email has its own throttle config
    }
  }
});
```

## Priority-Based Throttling

Not all notifications are equal. Implement priority queues:

### Priority Levels

| Priority | Examples | Throttle Behavior |
|----------|----------|-------------------|
| Critical | Security alerts, OTP | Never throttle |
| High | Direct messages, mentions | Minimal throttling |
| Medium | Comments, likes | Standard throttling |
| Low | Digests, recommendations | Aggressive throttling |

### Implementation

```typescript
type Priority = 'critical' | 'high' | 'medium' | 'low';

async function sendWithPriority(
  notification: Notification, 
  priority: Priority
) {
  // Critical always sends
  if (priority === 'critical') {
    return await sendImmediately(notification);
  }
  
  // Check throttle for other priorities
  const limits = {
    high: { perHour: 20 },
    medium: { perHour: 10 },
    low: { perHour: 5 }
  };
  
  const withinLimit = await checkThrottle(
    notification.userId, 
    limits[priority]
  );
  
  if (withinLimit) {
    await sendImmediately(notification);
  } else if (priority === 'high') {
    await queueForNextWindow(notification);
  } else {
    await dropOrDigest(notification);
  }
}
```

## Quiet Hours

Respect user time by not sending during sleep hours:

### Basic Quiet Hours

```typescript
function isQuietHours(userTimezone: string): boolean {
  const userTime = new Date().toLocaleString('en-US', { 
    timeZone: userTimezone 
  });
  const hour = new Date(userTime).getHours();
  
  // Quiet from 10pm to 8am
  return hour >= 22 || hour < 8;
}

async function sendOrDefer(notification: Notification) {
  const user = await getUser(notification.userId);
  
  if (isQuietHours(user.timezone)) {
    // Queue for 8am user's time
    await queueForTime(notification, getNext8am(user.timezone));
  } else {
    await sendImmediately(notification);
  }
}
```

### User-Configurable Quiet Hours

Let users set their own quiet hours:

```typescript
// Store in user preferences
const quietHours = {
  enabled: true,
  start: "22:00",
  end: "08:00",
  timezone: "America/New_York",
  allowCritical: true // Still send security alerts
};
```

## Provider Rate Limits

Respect provider-specific limits:

| Provider | Rate Limit | Notes |
|----------|------------|-------|
| **SendGrid** | Varies by plan | 100/sec typical |
| **Twilio SMS** | 1 msg/sec per number | Higher with short codes |
| **APNs** | ~100k/day typical | Soft limit |
| **FCM** | 500 msg/sec | Per project |
| **Slack** | 1 msg/sec per channel | 30-50 burst |

### Handling Rate Limit Responses

```typescript
async function sendWithRetry(notification: Notification) {
  try {
    await courier.send({ message: notification });
  } catch (error) {
    if (error.status === 429) {
      // Rate limited - queue for retry
      const retryAfter = error.headers['retry-after'] || 60;
      await queueForRetry(notification, retryAfter * 1000);
    } else {
      throw error;
    }
  }
}
```

## Throttle Feedback to Users

When throttling affects user experience, be transparent:

### Notification Count Indicators

```typescript
// In-app: Show "+5 more" instead of dropping silently
{
  visible: notifications.slice(0, 10),
  hiddenCount: Math.max(0, notifications.length - 10),
  message: notifications.length > 10 
    ? `+${notifications.length - 10} more notifications` 
    : null
}
```

### Digest Fallback

When throttle limit reached, queue for digest:

```typescript
if (!withinThrottleLimit) {
  await addToDigest(userId, notification);
  // User sees "3 updates" in next digest instead of nothing
}
```

## Monitoring Throttling

Track throttle metrics to tune your limits:

### Key Metrics

- **Throttle rate:** % of notifications throttled
- **Drop rate:** % of notifications dropped entirely
- **Digest inclusion rate:** % moved to digest
- **User complaints:** Feedback about "missing" notifications

### Alerting

```typescript
// Alert if throttling too aggressively
if (throttleRate > 0.3) {
  alert('High throttle rate - users may be missing notifications');
}

// Alert if not throttling enough (fatigue signal)
if (unsubscribeRate > 0.05) {
  alert('High unsubscribe rate - consider more aggressive throttling');
}
```

## Best Practices

### Start Conservative

Begin with generous limits and tighten based on data:

```typescript
// Start here
const INITIAL_LIMITS = {
  push: { perHour: 15 },
  email: { perDay: 10 }
};

// After monitoring, adjust
const OPTIMIZED_LIMITS = {
  push: { perHour: 8 },
  email: { perDay: 3 }
};
```

### Test Throttle Behavior

Ensure critical notifications aren't accidentally throttled:

```typescript
// Test: Security alerts should never be throttled
test('security alerts bypass throttle', async () => {
  // Max out the throttle
  for (let i = 0; i < 100; i++) {
    await sendLowPriority(userId);
  }
  
  // Security alert should still send
  const result = await sendSecurityAlert(userId);
  expect(result.status).toBe('sent');
});
```

### Log Throttle Decisions

For debugging and optimization:

```typescript
await logThrottleDecision({
  userId,
  notificationType,
  decision: 'throttled', // or 'sent', 'queued', 'dropped'
  reason: 'hourly_limit_exceeded',
  currentCount: 12,
  limit: 10
});
```

## Related

- [Batching](./batching.md) - Combining notifications
- [Reliability](./reliability.md) - Handling rate limit errors
- [Preferences](./preferences.md) - User frequency settings
- [Multi-Channel](./multi-channel.md) - Channel-specific limits
