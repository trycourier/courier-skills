# Notification Batching

## Quick Reference

### Rules
- **Let Courier aggregate.** Use the journey `batch` node for event rollups. For summaries on a schedule the recipient picks (daily, weekly), use a topic digest, see [digests.md](./digests.md). Don't queue and aggregate in your own backend unless neither can express the logic
- The `batch` node releases on a quiet `wait_period` (at least `PT1M`), a `max_wait_period` ceiling, or `max_items`, whichever comes first
- **Avoid `category_key` for now.** Events with different values are not split into separate batches, and the payload lands under the literal key string, not under `batch.<value>`. To group by value, invoke a separate journey per value, or use a per-value throttle key. See [Batch Data in Templates](#batch-data-in-templates)

### Common Mistakes
- Rebuilding aggregation in your own queue when a `batch` node expresses it
- Setting `max_wait_period` less than or equal to `wait_period` (it must be greater)
- Setting `wait_period` below `PT1M`, which returns `400 wait_period must be at least 1 minute`
- Relying on `category_key` to split batches by value. It doesn't
- Using `{{json x}}` in the template. There is no `json` helper, so the render fails with "Missing helper"

---

Combine multiple notifications into single, digestible messages to reduce notification fatigue.

## Server-Side Batching

**Courier aggregates events for you. Do not build this in your application.** Use the journey `batch` node, or a topic digest when recipients choose the cadence. Reach for app-side queueing only when you need aggregation logic Courier can't express (see "App-side aggregation" below).

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
      "retain": { "type": "first", "count": 3 }
    },
    { "type": "exit" }
  ],
  "enabled": true
}
```

Field notes:

- **`wait_period`** is a *quiet* window, at least `PT1M`. It resets on each new event. `max_wait_period` is the hard ceiling and must be greater than `wait_period`, so a continuously-active user still gets their batch.
- **`retain`** controls which items survive into the payload: `{ type: "first" | "last" | "highest" | "lowest", count: 0–25 }`. `highest`/`lowest` also require `sort_key`. The order of the kept items isn't guaranteed.
- **One run per batch carries the downstream send.** The other events' runs end at the batch node, and the run that sends isn't reliably the first event's.
- **`category_key`** (≤256 chars) is best avoided for now, see [Batch Data in Templates](#batch-data-in-templates).
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

The same applies to a digest whose payload depends on data Courier doesn't hold (rankings, cross-system joins, computed scores): run your own scheduled job and send once per recipient. Use a template that isn't linked to a topic with a digest, or Courier holds your summary and folds it into its own.

```typescript
// Scheduled job, runs at the recipient's chosen time
async function sendDailyDigest(userId: string) {
  const activity = await getActivitySince(userId, lastDigestTime);
  if (activity.length === 0) return; // don't send empty digests

  await client.send.message({
    message: {
      to: { user_id: userId },
      template: "nt_01kmrc3v8q2x6n0d4j7t1wbpe", // not linked to a digest topic
      data: { topItems: getTopItems(activity, 3), total: activity.length },
    },
  });
}
```

### Batch Data in Templates

The template sees top-level `batch.count` (the true total) and `batch.items` (the events `retain` kept). Each item is that invoke's `data` object as is, with no wrapper, so `{{batch.items.[0].actor_name}}` reads `actor_name` from one event. The sending run's own `data` fields also sit at the top level. Courier's `condition` and `subtract` helpers do the comparison and the math:

```
{{#if (condition batch.count ">" 1)}}
  {{batch.items.[0].actor_name}} and {{subtract batch.count 1}} others liked your post
{{else}}
  {{batch.items.[0].actor_name}} liked your post
{{/if}}
```

Item order isn't guaranteed, so don't rely on `items.[0]` being the first or latest event. There is no `json` helper: `{{json x}}` fails the render with "Missing helper".

**With a `category_key`** the payload doesn't follow the documented `batch.<value>` shape. It lands at the root under the literal key string, so for `"category_key": "data.target_id"` read `{{[data.target_id].count}}` and `{{[data.target_id].items}}`. A key without a dot, such as `"target_id"`, overwrites that `data` field. Events with different values still share one batch. Avoid it for now. To group by value, invoke a separate journey per value, or use a per-value throttle key. If you must use it, read the payload as above and test the render first.

### Batch Cancellation

If user engages before batch sends, consider canceling. With [Journeys](./journeys.md), build a branch node that checks engagement before the send node, the journey exits early if the user already saw the content. See [Patterns, Sequence Cancellation](./patterns.md#sequence-cancellation).

## Related

- [Engagement](../lifecycle-marketing.md) - Activity notification patterns
- [Throttling](./throttling.md) - Rate limiting notifications
- [Preferences](./preferences.md) - Topics and opt-out
- [Inbox](../channels/inbox.md) - In-app notification batching
- [Digests](./digests.md) - Recipient-scheduled summaries on a subscription topic
- [Journeys](./journeys.md) - The `batch` node, plus throttle, delay, branch, and send
