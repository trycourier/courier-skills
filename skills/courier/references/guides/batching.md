# Notification Batching

## Quick Reference

### Rules
- NEVER batch: OTP, password reset, security alerts, order confirmations
- DO batch: likes, comments, follows, team activity, low-priority alerts
- **Let Courier aggregate.** Use the journey `batch` node (event rollup) or `add-to-digest` node (scheduled digests) — don't queue and aggregate in your own backend unless the built-in nodes genuinely can't express the logic
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

In your [Journey](./journeys.md) DAG, this is a single `batch` node — set `wait_period` to the quiet window and `max_wait_period` to the ceiling. See [The `batch` node](#the-batch-node).

### 2. Count-Based Batching

Send after N events accumulate, or after the window closes — whichever comes first.

```
[Event 1] → Count: 1
[Event 2] → Count: 2
[Event 3] → Count: 3 → max_items reached → Send batch
```

Set `max_items` on the `batch` node (1–1000, default 100). **Best for:** high-volume events like likes and views.

### 3. Digest Batching

Scheduled summaries at fixed intervals — use the `add-to-digest` node so the schedule and the user's frequency preference drive delivery.

| Digest Type | Frequency | Best For |
|-------------|-----------|----------|
| Real-time digest | Every 15-30 min | Active users, important updates |
| Daily digest | Once per day | Activity summaries, newsletters |
| Weekly digest | Once per week | Low-engagement users, recaps |

## Server-Side Batching

**Courier aggregates events for you — do not build this in your application.** Journeys have two purpose-built nodes for it. Reach for app-side queueing only when you need aggregation logic Courier can't express (see "App-side aggregation" below).

| Need | Use | Releases on |
|------|-----|-------------|
| Collect events into one payload, then send | `batch` node | A quiet `wait_period`, a `max_wait_period` ceiling, or `max_items` |
| Add events to a recurring digest a user subscribes to | `add-to-digest` node | The subscription topic's configured digest schedule |

### The `batch` node

Collects multiple events into one aggregated payload and fires a single downstream send. See [Journeys](./journeys.md#node-types-reference) for the full field reference.

```json
{
  "name": "Social Activity Batch",
  "nodes": [
    { "type": "trigger", "trigger_type": "api-invoke" },
    {
      "type": "batch",
      "scope": "user",
      "wait_period": "PT5M",
      "max_wait_period": "PT1H",
      "max_items": 25,
      "category_key": "target_id",
      "retain": { "type": "first", "count": 3 }
    }
  ],
  "enabled": true
}
```

Field notes:

- **`wait_period`** is a *quiet* window — it resets on each new event. `max_wait_period` is the hard ceiling and must be greater than `wait_period`, so a continuously-active user still gets their batch.
- **`category_key`** partitions the batch (≤256 chars). Keying on `target_id` gives one batch per post rather than one batch per user — this is how you get "3 people liked *this* post" instead of lumping unrelated activity together.
- **`retain`** controls which items survive into the payload: `{ type: "first" | "last" | "highest" | "lowest", count: 0–25 }`. `highest`/`lowest` also require `sort_key`.
- **Do not include node `id` fields.** They're server-generated; `POST /journeys` rejects client-supplied ids with a `400`. Send nodes are also not allowed on create — add them via `PUT` once the journey-scoped templates exist. See [Journeys](./journeys.md#standard-workflow).

Invoke once per event; Courier handles the accumulation:

```bash
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/invoke" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "data": { "event_type": "like", "actor_name": "Jane", "target_id": "post-789" }
  }'
```

### The `add-to-digest` node

Adds the event to a digest keyed by a subscription topic. The digest releases on that topic's schedule rather than on a per-run timer — this is the right node for "daily summary" and "weekly roundup", and it means the user's own digest-frequency preference controls delivery.

```json
{ "type": "add-to-digest", "subscription_topic_id": "<topic-id>" }
```

Inspect and force-release accumulated digests via the `digests` namespace:

```typescript
// What has piled up for a schedule so far? (schedule ids look like "sch/{uuid}")
const instances = await client.digests.schedules.listInstances(scheduleId);

// Release early — e.g. a "send me this now" button in your UI
await client.digests.schedules.release(scheduleId);
```

```python
instances = client.digests.schedules.list_instances(schedule_id)
client.digests.schedules.release(schedule_id)
```

### App-side aggregation (only when the nodes don't fit)

If your aggregation needs data or logic that only your backend has — cross-entity rollups, ranking by a computed score, joins against your own tables — keep the accumulation in your app and use Courier for timing only: a `throttle` node to limit frequency, a `delay` node for the window, and a `fetch` node to pull your precomputed payload at send time.

```json
{
  "type": "fetch",
  "method": "get",
  "url": "https://api.yourapp.com/users/{{user_id}}/pending-notifications",
  "merge_strategy": "overwrite"
}
```

This is strictly more work than the `batch` node. Reach for it only when you've established the built-in nodes can't express what you need.

### Batch Data in Templates

Access batched data in your notification template:

```
{{#if batch.is_multiple}}
  {{batch.first.actor_name}} and {{batch.others_count}} others liked your post
{{else}}
  {{batch.first.actor_name}} liked your post
{{/if}}
```

Precompute `is_multiple` (boolean) and `others_count` (batch count minus 1) in your data, since Handlebars does not support comparison operators or arithmetic.

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

Set `category_key` on the `batch` node to the field identifying the target (e.g. `"target_id"`) and Courier partitions the batches for you — one batch per post rather than one mixed batch per user.

### Type Aggregation

Combine different event types:

- "5 likes and 2 comments on your post"
- "Jane liked your post and started following you"

## Digest Implementation

### Preferred: the `add-to-digest` node

Add an `add-to-digest` node keyed to a subscription topic and let the topic's schedule release it. No cron job, no activity table, no empty-digest check — Courier only releases instances that accumulated events, and the user's own digest-frequency preference controls cadence. See [The `add-to-digest` node](#the-add-to-digest-node).

### Fallback: your own scheduled job

Use this only when the digest payload depends on data Courier doesn't hold — rankings, cross-system joins, computed scores.

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

## Channel Considerations

| Channel | Batching Approach |
|---------|-------------------|
| In-app | Batch aggressively, users check when ready |
| Push | Moderate batching, respect attention |
| Email | Daily/weekly digests work well |
| SMS | Rarely batch (high cost, high attention) |

## Related

- [Engagement](../lifecycle-marketing.md) - Activity notification patterns
- [Throttling](./throttling.md) - Rate limiting notifications
- [Preferences](./preferences.md) - User frequency preferences
- [Inbox](../channels/inbox.md) - In-app notification batching
- [Journeys](./journeys.md) - The `batch` and `add-to-digest` nodes, plus throttle, delay, branch, and send
