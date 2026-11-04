# Notification Batching

**Contents:** [Quick Reference](#quick-reference) · [Server-Side Batching](#server-side-batching) · [The batch node](#the-batch-node) · [App-side aggregation (only when the nodes don't fit)](#app-side-aggregation-only-when-the-nodes-dont-fit) · [Batch Data in Templates](#batch-data-in-templates) · [Batch Cancellation](#batch-cancellation) · [Related](#related)

## Quick Reference

### Rules
- **Let Courier aggregate.** Use the journey `batch` node for event rollups. For summaries on a schedule the recipient picks (daily, weekly), use a topic digest, see [digests.md](./digests.md). Don't queue and aggregate in your own backend unless neither can express the logic
- The `batch` node releases on a quiet `wait_period` (`PT1M` to `P1D`), a `max_wait_period` ceiling (from `wait_period` up to `P7D`), or `max_items`, whichever comes first
- **`category_key` groups events inside one batch. It doesn't split them.** Write it as one whole reference, `"{{data.event_type}}"`. The batch still releases once, with the groups under `batch.categories.<value>`. See [Batch Data in Templates](#batch-data-in-templates)

### Common Mistakes
- Rebuilding aggregation in your own queue when a `batch` node expresses it
- Setting `max_wait_period` below `wait_period` or above `P7D`, or `wait_period` above `P1D`. Each returns a `400`, such as `max_wait_period must be at most 7 days`
- Setting `wait_period` below `PT1M`, which returns `400 wait_period must be at least 1 minute`
- Relying on `category_key` to split batches by value. It groups events inside one batch, which still releases once
- Writing `category_key` as a plain path (`"target_id"` or `"data.target_id"`). It returns `400 category_key must be a reference like "{{data.category}}"`
- Relying on `retain` names or `sort_key`: `first` keeps the most recent events, `last` the earliest, and `highest`/`lowest` ignore `sort_key`. See [the retain table](#batch-data-in-templates)
- Writing a list `loop` path without the `data.` root (`batch.items`). The send fails with `js-block: batch is not defined`
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

- **`wait_period`** is a *quiet* window, at least `PT1M`. It resets on each new event. `max_wait_period` is the hard ceiling, at least `wait_period` and at most `P7D`, so a continuously-active user still gets their batch.
- **`retain`** controls which items survive into the payload: `{ type: "first" | "last" | "highest" | "lowest", count: 0–25 }`. `highest`/`lowest` also require `sort_key`, though it has no effect today; see [Batch Data in Templates](#batch-data-in-templates) for what each type actually keeps. `retain` is shared across categories: a count of 3 keeps 3 events for the whole batch, not 3 per category.
- **One run per batch carries the downstream send.** The other events' runs end at the batch node, and the run that sends isn't reliably the first event's.
- **`category_key`** (≤256 chars) is one whole reference into the event, such as `"{{data.event_type}}"`. Events are counted and listed by that value inside the batch. A plain path, or a reference inside other text, returns 400.
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
  "url": "https://api.yourapp.com/users/{{recipient}}/pending-notifications",
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

**`retain` doesn't behave as its names suggest.** In current behavior it only looks at arrival order:

| `retain.type` | Keeps | Order of `items` |
|---|---|---|
| `first` | The most recent events | Newest first |
| `last` | The earliest events | Oldest first |
| `highest` | Same as `first`; `sort_key` is ignored | Newest first |
| `lowest` | Same as `last`; `sort_key` is ignored | Oldest first |

So `items.[0]` with `first` is the latest event. To keep the latest events, use `first`. There is no way to keep the top events by a value such as priority: send everything and pick in your backend, see [App-side aggregation](#app-side-aggregation-only-when-the-nodes-dont-fit). Check a test run before shipping copy that depends on which events were kept.

There is no `json` helper: `{{json x}}` fails the render with "Missing helper".

**With a `category_key`** such as `"{{data.event_type}}"`, the groups sit under `batch.categories`, keyed by each value, each with its own `count` and `items`. `batch.count` and `batch.items` still cover the whole batch. A category with no events is absent, so guard each one:

```
{{#if batch.categories.like}}{{batch.categories.like.count}} likes{{/if}}
{{#if batch.categories.comment}}{{batch.categories.comment.count}} comments{{/if}}
```

A category's `count` is its true total, but its `items` only holds the events `retain` kept for the whole batch, so it can be shorter than `count`, or empty. An event with no value at the key counts in the totals but in no category, and `categories` is left out when no event had a value.

To list items, use a `list` element whose `loop` starts at `data.` (`data.batch.items`, or `data.batch.categories.like.items`), with each item as `$.item`. A loop path without the `data.` root fails the whole send with `js-block: batch is not defined`:

```json
{
  "type": "list",
  "list_type": "unordered",
  "loop": "data.batch.categories.like.items",
  "elements": [
    { "type": "list-item", "elements": [
      { "type": "string", "content": "{{$.item.actor_name}} liked your post" }
    ] }
  ]
}
```

Categories don't split the send: the batch releases once. To cover several posts in one message, key the categories by something readable, such as `"{{data.post_title}}"`, since the key is what the recipient sees. Keys can hold spaces and dots; read one with brackets, `{{batch.categories.[Launch notes].count}}`. `loop` can't iterate `batch.categories`, because it's an object, not an array (the send fails with `A loop expression must evaluate to an array`). List every category with `{{#each}}` instead: in an `html` element for email, or in a text element for other channels, which renders but can't be edited in the designer:

```
{{#each batch.categories}}{{@key}}: {{count}} new{{/each}}
```

For a separate notification per post ("3 people liked *this* post"), the batch node can't do it, since every batch is per user. Aggregate per post in your own backend, see [App-side aggregation](#app-side-aggregation-only-when-the-nodes-dont-fit).

The template editor may flag `{{batch.count}}` and other `batch` paths as unknown variables. They render; check with a test run.

### Batch Cancellation

If user engages before batch sends, consider canceling. With [Journeys](./journeys.md), build a branch node that checks engagement before the send node, the journey exits early if the user already saw the content. See [Patterns, Sequence Cancellation](./patterns.md#sequence-cancellation).

## Related

- [Engagement](../lifecycle-marketing.md) - Activity notification patterns
- [Throttling](./throttling.md) - Rate limiting notifications
- [Preferences](./preferences.md) - Topics and opt-out
- [Inbox](../channels/inbox.md) - In-app notification batching
- [Digests](./digests.md) - Recipient-scheduled summaries on a subscription topic
- [Journeys](./journeys.md) - The `batch` node, plus throttle, delay, branch, and send
