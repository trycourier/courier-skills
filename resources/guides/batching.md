# Notification Batching

## Quick Reference

### Rules
- NEVER batch: OTP, password reset, security alerts, order confirmations
- DO batch: likes, comments, follows, team activity, low-priority alerts
- Time window batching: wait 5-10 minutes before sending
- Actor aggregation: "Jane and 5 others" (not 6 separate notifications)
- Never send empty digests
- Cancel batch if user engages before send

### Batch Decision Matrix
| Notification | Batch? | Strategy |
|--------------|--------|----------|
| OTP/2FA | NO | Immediate |
| Password reset | NO | Immediate |
| Security alert | NO | Immediate |
| Order confirmation | NO | Immediate |
| Likes | YES | 5-10 min window |
| Comments | YES | Group by thread |
| New followers | YES | Daily digest |
| Team activity | YES | Hourly summary |

### Common Mistakes
- Batching time-sensitive notifications (OTP, security)
- Batching too aggressively (users miss important info)
- Sending empty digests
- Not canceling batch when user already engaged
- Same batch window for all notification types
- No way for users to choose digest frequency

### Templates

**Actor Aggregation:**
```typescript
function formatActors(actors: string[]): string {
  if (actors.length === 1) return actors[0];
  if (actors.length === 2) return `${actors[0]} and ${actors[1]}`;
  return `${actors[0]}, ${actors[1]}, and ${actors.length - 2} others`;
}
// "Jane, Bob, and 3 others liked your post"
```

**Batched Send:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Your post is popular!",
      body: "Jane, Bob, and 8 others liked your post"
    }
  }
});
```

---

Combine multiple notifications into single, digestible messages to reduce notification fatigue.

## Why Batch Notifications?

- **Reduce fatigue:** "Jane and 5 others liked your post" is better than 6 separate notifications
- **Improve engagement:** Batched notifications have higher open rates
- **Lower costs:** Fewer sends = lower provider costs
- **Better UX:** Users prefer summaries over interruption storms

## When to Batch

### Good Candidates for Batching

| Notification Type | Batch Strategy |
|-------------------|----------------|
| Social likes | Combine by target (post, comment) |
| Comments on same item | Group by thread |
| New followers | Daily/weekly digest |
| Team activity | Hourly or daily summary |
| Low-priority alerts | Scheduled digest |

### Don't Batch These

| Notification Type | Why Not |
|-------------------|---------|
| OTP/2FA codes | Time-sensitive, security |
| Password resets | Immediate action needed |
| Order confirmations | User expects immediate |
| Security alerts | Urgent, actionable |
| Direct messages | Real-time conversation |

## Batching Strategies

### 1. Time-Window Batching

Collect notifications over a time window, then send a summary.

```
[Event 1] → Queue
[Event 2] → Queue      → [5 min window closes] → Send batch
[Event 3] → Queue
```

**Best for:** Social activity, team updates, non-urgent alerts

**Implementation:**

```typescript
// Queue notification instead of sending immediately
await courier.automations.invoke("batch-likes", {
  user_id: targetUserId,
  data: {
    actorName: "Jane",
    targetType: "post",
    targetId: "post-123"
  }
});
```

In your Courier Automation:
1. **Delay step:** Wait 5-10 minutes
2. **Fetch step:** Get all queued events for this user/target
3. **Send step:** Send batched notification with aggregated data

### 2. Count-Based Batching

Send after N events accumulate, or after timeout (whichever comes first).

```
[Event 1] → Count: 1
[Event 2] → Count: 2
[Event 3] → Count: 3 → Threshold reached → Send batch
```

**Best for:** High-volume events like likes, views

### 3. Digest Batching

Scheduled summaries at fixed intervals.

| Digest Type | Frequency | Best For |
|-------------|-----------|----------|
| Real-time digest | Every 15-30 min | Active users, important updates |
| Daily digest | Once per day | Activity summaries, newsletters |
| Weekly digest | Once per week | Low-engagement users, recaps |

## Courier Automations for Batching

### Using the Batch Step

Courier Automations has a built-in batch step that collects events over a time window:

```typescript
// Each event triggers the automation
await courier.automations.invoke("social-activity-batch", {
  user_id: "user-123",
  data: {
    event_type: "like",
    actor_id: "user-456",
    actor_name: "Jane",
    target_id: "post-789"
  }
});
```

Configure the automation in the Courier dashboard:
1. **Batch step:** Collect events for 5 minutes
2. **Send step:** Use aggregated data in template

### Batch Data in Templates

Access batched data in your notification template:

```
{{#if batch.count > 1}}
  {{batch.first.actor_name}} and {{batch.count - 1}} others liked your post
{{else}}
  {{batch.first.actor_name}} liked your post
{{/if}}
```

## Aggregation Patterns

### Actor Aggregation

Combine by who did the action:

- 1 actor: "Jane liked your post"
- 2 actors: "Jane and Bob liked your post"
- 3+ actors: "Jane, Bob, and 3 others liked your post"

```typescript
function formatActors(actors: string[]): string {
  if (actors.length === 1) return actors[0];
  if (actors.length === 2) return `${actors[0]} and ${actors[1]}`;
  return `${actors[0]}, ${actors[1]}, and ${actors.length - 2} others`;
}
```

### Target Aggregation

Combine by what was affected:

- "3 comments on your post 'API Design Tips'"
- "New activity on 2 of your projects"

### Type Aggregation

Combine different event types:

- "5 likes and 2 comments on your post"
- "Jane liked your post and started following you"

## Digest Implementation

### Daily Digest Flow

```typescript
// Scheduled job runs daily at 9am user's local time
async function sendDailyDigest(userId: string) {
  // Fetch activity since last digest
  const activity = await getActivitySince(userId, lastDigestTime);
  
  if (activity.length === 0) return; // Don't send empty digests
  
  await courier.send({
    message: {
      to: { user_id: userId },
      template: "DAILY_DIGEST",
      data: {
        likes: activity.filter(a => a.type === 'like').length,
        comments: activity.filter(a => a.type === 'comment').length,
        followers: activity.filter(a => a.type === 'follow').length,
        topItems: getTopItems(activity, 3)
      }
    }
  });
}
```

### User Preference for Digest Frequency

Let users choose their batching preference:

```typescript
// Check user's digest preference
const prefs = await courier.users.preferences.get(userId);
const digestPref = prefs.items.find(p => p.topic_id === "activity-digest");

// Options: "realtime", "daily", "weekly", "off"
if (digestPref?.custom_routing?.frequency === "realtime") {
  // Send immediately
} else {
  // Queue for digest
}
```

## Best Practices

### Time Window Selection

| Event Volume | Recommended Window |
|--------------|-------------------|
| < 10/hour | 15-30 minutes |
| 10-50/hour | 5-10 minutes |
| 50+/hour | 2-5 minutes or count-based |

### Don't Batch Too Aggressively

- Users still want timely information
- Direct mentions/replies should be faster than likes
- Consider urgency when setting windows

### Empty Digest Handling

Never send empty digests:

```typescript
if (batchedEvents.length === 0) {
  return; // Skip this digest
}
```

### Batch Cancellation

If user engages before batch sends, consider canceling:

```typescript
// User opened the app and saw the activity
await courier.automations.cancel({
  cancelation_token: `digest-${userId}-${date}`
});
```

## Channel Considerations

| Channel | Batching Approach |
|---------|-------------------|
| In-app | Batch aggressively, users check when ready |
| Push | Moderate batching, respect attention |
| Email | Daily/weekly digests work well |
| SMS | Rarely batch (high cost, high attention) |

## Related

- [Engagement](../growth/engagement.md) - Activity notification patterns
- [Throttling](./throttling.md) - Rate limiting notifications
- [Preferences](./preferences.md) - User frequency preferences
- [Inbox](../channels/inbox.md) - In-app notification batching
