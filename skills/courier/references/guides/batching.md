# Notification Batching

## Quick Reference

### Rules
- **Let Courier aggregate.** Use the journey `batch` node for event rollups. For summaries on a schedule the recipient picks (daily, weekly), use a topic digest, see [digests.md](./digests.md). Don't queue and aggregate in your own backend unless neither can express the logic
- The `batch` node releases on a quiet `wait_period`, a `max_wait_period` ceiling, or `max_items`, whichever comes first
- `category_key` partitions a batch by target, which is how you get "3 people liked *this* post" instead of one mixed batch per user

### Common Mistakes
- Rebuilding aggregation in your own queue when a `batch` node expresses it
- Setting `max_wait_period` less than or equal to `wait_period` (it must be greater)
- One mixed batch per user because `category_key` wasn't set

---

Combine multiple notifications into single, digestible messages to reduce notification fatigue.

## Server-Side Batching

**Courier aggregates events for you. Do not build this in your application.** Journeys have two purpose-built nodes for it. Reach for app-side queueing only when you need aggregation logic Courier can't express (see "App-side aggregation" below).

| Need | Use | Releases on |
|------|-----|-------------|
| Collect events into one payload, then send | `batch` node | A quiet `wait_period`, a `max_wait_period` ceiling, or `max_items` |
| A daily or weekly summary on the recipient's chosen schedule | A topic digest, see [digests.md](./digests.md) | The recipient's schedule for the topic |

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

- **`wait_period`** is a *quiet* window. It resets on each new event. `max_wait_period` is the hard ceiling and must be greater than `wait_period`, so a continuously-active user still gets their batch.
- **`category_key`** partitions the batch (≤256 chars). Keying on `target_id` gives one batch per post rather than one batch per user. This is how you get "3 people liked *this* post" instead of lumping unrelated activity together.
- **`retain`** controls which items survive into the payload: `{ type: "first" | "last" | "highest" | "lowest", count: 0–25 }`. `highest`/`lowest` also require `sort_key`.
- **Do not include node `id` fields.** They're server-generated; `POST /journeys` rejects client-supplied ids with `400 client-supplied node ids are not allowed`. Send nodes are rejected too, with a `422` that spells out the sequence: create the journey, create its scoped templates, then `PUT` to wire the send nodes. Add them via `PUT` once the journey-scoped templates exist. See [Journeys](./journeys.md#standard-workflow).

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

### App-side aggregation (only when the nodes don't fit)

If your aggregation needs data or logic that only your backend has, cross-entity rollups, ranking by a computed score, joins against your own tables. Keep the accumulation in your app and use Courier for timing only: a `throttle` node to limit frequency, a `delay` node for the window, and a `fetch` node to pull your precomputed payload at send time.

```json
{
  "type": "fetch",
  "method": "get",
  "url": "https://api.yourapp.com/users/{{user_id}}/pending-notifications",
  "merge_strategy": "overwrite"
}
```

This is strictly more work than the `batch` node. Reach for it only when you've established the built-in nodes can't express what you need.

The same applies to a digest whose payload depends on data Courier doesn't hold (rankings, cross-system joins, computed scores): run your own scheduled job and send once per recipient.

```typescript
// Scheduled job, runs at the recipient's chosen time
async function sendDailyDigest(userId: string) {
  const activity = await getActivitySince(userId, lastDigestTime);
  if (activity.length === 0) return; // don't send empty digests

  await client.send.message({
    message: {
      to: { user_id: userId },
      template: "nt_01kmrbtm6q9x3c7v1d5w2n8hj",
      data: { topItems: getTopItems(activity, 3), total: activity.length },
    },
  });
}
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

Precompute `is_multiple` (boolean) and `others_count` (batch count minus 1) in your data, since Handlebars does not support comparison operators or arithmetic.

### Batch Cancellation

If user engages before batch sends, consider canceling. With [Journeys](./journeys.md), build a branch node that checks engagement before the send node, the journey exits early if the user already saw the content. See [Patterns, Sequence Cancellation](./patterns.md#sequence-cancellation).

## Related

- [Engagement](../lifecycle-marketing.md) - Activity notification patterns
- [Throttling](./throttling.md) - Rate limiting notifications
- [Preferences](./preferences.md) - User frequency preferences
- [Inbox](../channels/inbox.md) - In-app notification batching
- [Digests](./digests.md) - Recipient-scheduled summaries on a subscription topic
- [Journeys](./journeys.md) - The `batch` node, plus throttle, delay, branch, and send
