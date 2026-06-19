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

**Actor Aggregation:** Use `formatActors()` from [Patterns](./patterns.md#actor-aggregation) — formats as "Jane, Bob, and 3 others".

**Batched Send:**
```typescript
await client.send.message({
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

```bash
# Invoke the batching journey for each event
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/invoke" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'"$TARGET_USER_ID"'",
    "data": {
      "actorName": "Jane",
      "targetType": "post",
      "targetId": "post-123"
    }
  }'
```

In your [Journey](./journeys.md) DAG:
1. **Throttle node:** Limit to 1 run per user per 5-10 minutes
2. **Delay node:** Wait for the batch window to close
3. **Fetch node:** Pull queued events from your backend (your app queues and aggregates)
4. **Send node:** Send batched notification with aggregated data

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

## Server-Side Batching

### Journeys + Fetch for Aggregation

[Journeys](./journeys.md) can implement batch/digest patterns by combining a **throttle** node (to limit how often a user receives a batch), a **delay** node (to wait for the batch window), and a **fetch** node (to pull aggregated events from your backend). The journey itself does not aggregate events — your application queues the events, and the journey's fetch node retrieves the aggregated data at send time.

```json
{
  "name": "Social Activity Batch",
  "nodes": [
    { "id": "trigger-1", "type": "trigger", "trigger_type": "api-invoke" },
    {
      "id": "throttle-per-user",
      "type": "throttle",
      "scope": "user",
      "max_allowed": 1,
      "period": "PT5M"
    },
    { "id": "wait-5m", "type": "delay", "mode": "duration", "duration": "PT5M" },
    {
      "id": "fetch-batched-events",
      "type": "fetch",
      "method": "get",
      "url": "https://api.yourapp.com/users/{{user_id}}/pending-notifications",
      "merge_strategy": "overwrite"
    },
    { "id": "send-batch", "type": "send", "message": { "template": "<batch-template-id>" } }
  ],
  "enabled": true
}
```

Your application invokes the journey on each event. The throttle node ensures only one run proceeds per user per window. That run waits, fetches aggregated data from your backend, and sends a single batched notification.

```bash
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/invoke" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "data": {
      "event_type": "like",
      "actor_name": "Jane",
      "target_id": "post-789"
    }
  }'
```

> **Note:** Journeys do not have a built-in batch/digest node that aggregates events automatically. The aggregation lives in your application; the journey orchestrates the timing and send. For built-in event aggregation, see the Automations batch step below.

### Automations Batch Step

Courier Automations have a built-in batch step that collects and aggregates events server-side. If you need Courier to handle the aggregation (not just the timing), use Automations:

```typescript
await client.automations.invoke.invokeByTemplate("social-activity-batch", {
  recipient: "user-123",
  data: {
    event_type: "like",
    actor_id: "user-456",
    actor_name: "Jane",
    target_id: "post-789"
  }
});
```

### Batch Data in Templates

Access batched data in your notification template:

```
{{#if batch.is_multiple}}
  {{batch.first.actor_name}} and {{batch.others_count}} others liked your post
{{else}}
  {{batch.first.actor_name}} liked your post
{{/if}}
```

Precompute `is_multiple` (boolean) and `others_count` (batch count minus 1) in your data or automation step, since Handlebars does not support comparison operators or arithmetic.

## Aggregation Patterns

### Actor Aggregation

Combine by who did the action. Use `formatActors()` from [Patterns](./patterns.md#actor-aggregation):

- 1 actor: "Jane liked your post"
- 2 actors: "Jane and Bob liked your post"
- 3+ actors: "Jane, Bob, and 3 others liked your post"

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
  
  await client.send.message({
    message: {
      to: { user_id: userId },
      template: "nt_01kmrbtm6q9x3c7v1d5w2n8hj",
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
// Store digest frequency on profile custom data
const profile = await client.profiles.retrieve(userId);
const digestFrequency = profile.profile?.custom?.digest_frequency ?? "daily";

// Options: "realtime", "daily", "weekly", "off"
if (digestFrequency === "realtime") {
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

If user engages before batch sends, consider canceling. With [Journeys](./journeys.md), build a branch node that checks engagement before the send node — the journey exits early if the user already saw the content. See [Patterns — Sequence Cancellation](./patterns.md#sequence-cancellation).

**Legacy: Automations cancellation** (if you have existing Automations):

```typescript
await client.automations.invoke.invokeAdHoc({
  recipient: userId,
  automation: {
    steps: [
      { action: "cancel", cancelation_token: `digest-${userId}-${date}` }
    ]
  }
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
- [Journeys](./journeys.md) - Build multi-step batch/digest flows with throttle, delay, and send nodes
- [Automations](https://www.courier.com/docs/automations/overview) - Legacy dashboard-configured batch/digest steps
