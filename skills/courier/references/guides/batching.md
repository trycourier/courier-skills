# Notification Batching

**Contents:** [Quick Reference](#quick-reference) · [Server-Side Batching](#server-side-batching) · [The batch node](#the-batch-node) · [App-side aggregation (only when the nodes don't fit)](#app-side-aggregation-only-when-the-nodes-dont-fit) · [Batch Data in Templates](#batch-data-in-templates) · [Related](#related)

## Quick Reference

### Rules
- **Let Courier aggregate.** Use the journey `batch` node for event rollups. For summaries on a schedule the recipient picks (daily, weekly), use a topic digest, see [digests.md](./digests.md). Don't queue and aggregate in your own backend unless neither can express the logic
- The `batch` node releases on a quiet `wait_period` (`PT1M` to `P1D`), a `max_wait_period` ceiling (from `wait_period` up to `P7D`), or `max_items`, whichever comes first
- **`category_key` groups events inside one batch. It doesn't split them.** Write it as one whole reference, `"{{data.event_type}}"`. The batch still releases once, with the groups under `batch.categories.<value>`. See [Batch Data in Templates](#batch-data-in-templates)

### Common Mistakes
- Setting `max_wait_period` below `wait_period` or above `P7D`, or `wait_period` above `P1D`. Each returns a `400`, such as `max_wait_period must be at most 7 days`
- Setting `wait_period` below `PT1M`, which returns `400 wait_period must be at least 1 minute`
- Writing `category_key` as a plain path (`"target_id"` or `"data.target_id"`). It returns `400 category_key must be a reference like "{{data.category}}"`
- Relying on `retain` names or `sort_key`: `first` keeps the most recent events, `last` the earliest, and `highest`/`lowest` ignore `sort_key`. See [the retain table](#batch-data-in-templates)
- Writing a list `loop` path without the `data.` root (`batch.items`). The send fails with `js-block: batch is not defined`
- Using `{{json x}}` in the template. There is no `json` helper, so the render fails with "Missing helper"

---

## Server-Side Batching

### The `batch` node

Collects events into one payload and fires a single downstream send. Full field reference: [Journeys](./journeys.md#node-types-reference).

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

- **`wait_period`** resets on each new event; `max_wait_period` is the hard ceiling, so a continuously active user still gets their batch.
- **`retain`** is shared across categories: a count of 3 keeps 3 events for the whole batch, not 3 per category. What each type actually keeps is in [Batch Data in Templates](#batch-data-in-templates).
- **One run per batch carries the downstream send.** The other events' runs end at the batch node, and the run that sends isn't reliably the first event's.
- **`category_key`** (≤256 chars) counts and lists events by that value inside the batch. A reference inside other text returns 400, like a plain path.
- Add the downstream send node by `PUT` once the journey exists, as for any journey ([Standard Workflow](./journeys.md#standard-workflow)).

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

If the aggregation needs data or logic only your backend has (cross-entity rollups, ranking by a computed score, joins against your own tables), keep the accumulation in your app and use Courier for timing only: a `throttle` node to limit frequency, a `delay` node for the window, and a `fetch` node to pull your precomputed payload at send time.

```json
{
  "type": "fetch",
  "method": "get",
  "url": "https://api.yourapp.com/users/{{recipient}}/pending-notifications",
  "merge_strategy": "overwrite"
}
```

For a scheduled summary built from data Courier doesn't hold, run your own job and send once per recipient. Use a template that isn't linked to a topic with a digest, or Courier holds your summary and folds it into its own.

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

## Related

- [Engagement](../lifecycle-marketing.md) - Activity notification patterns
- [Throttling](./throttling.md) - Rate limiting notifications
- [Preferences](./preferences.md) - Topics and opt-out
- [Inbox](../channels/inbox.md) - In-app notification batching
- [Digests](./digests.md) - Recipient-scheduled summaries on a subscription topic
- [Journeys](./journeys.md) - The `batch` node, plus throttle, delay, branch, and send
