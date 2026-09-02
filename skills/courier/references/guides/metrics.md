# Template Metrics

`GET /notifications/{id}/metrics` returns one template's delivery funnel as a time series: sent, delivered, opened, clicked, errors, and undeliverable, broken out per provider and channel inside every bucket. Use it to build a dashboard, alert when a delivery rate drops, push the numbers into a warehouse, or answer "how is this template doing?" without opening the Courier app.

This is aggregates for one template. For one message's timeline, use [cli.md](./cli.md) and Message Logs instead.

## Quick Reference

### Rules

- **Window is `lookback` OR `start`+`end`, never a mix.** `lookback` is an ISO 8601 duration counted back from now (`P30D`, `P12W`, `PT12H`), default `P30D`. `start`+`end` are ISO 8601 timestamps with an offset and must be supplied together. If you send both forms, `start`/`end` win and `lookback` is ignored.
- **Label charts with the response's `start` and `end`, not the values you requested.** Courier widens the window outward to whole buckets, so a request for the last 36 hours at `DAY` returns two full days.
- **Go coarser, don't split the range.** A granularity too fine for the window returns `400`. Switch `HOUR` to `DAY` rather than issuing several calls.
- **There is no bucket-level total.** Sum the rows in a bucket yourself, and guard the division: a quiet bucket has `sent: 0`.
- **A window past your plan's cap returns `402`, not a truncated series.** Check the cap before widening.
- **Per-template only.** Workspace-wide means `client.notifications.list()` then one call per template, paced against the plan's requests-per-second.
- **US region only.**

### Common Mistakes

- Treating an all-empty series as proof a template sent nothing. **An unknown template ID returns `200` with an empty series, not `404`.** Confirm the ID first.
- Expecting sends made without a template to show up. They never appear here.
- Reading `opened` on a channel with no open tracking. It is always `0` there, which is not the same as "nobody opened it."
- Assuming `errors` and `undeliverable` are the same failure. They aren't; see the field table below.
- Requesting `HOUR` granularity over a month, or `WEEK` over ten years, and expecting a truncated result instead of a `400`.
- Retrying a `429` immediately. Honor `Retry-After`.

### SDK shape

| | Node | Python |
|---|---|---|
| Fetch metrics | `client.notifications.getMetrics(templateId, { lookback, granularity })` | `client.notifications.get_metrics(template_id, lookback=..., granularity=...)` |

Available in all seven server SDKs (Node, Python, Ruby, Go, Java, PHP, C#).

CLI: `courier notifications get-metrics --id <template-id> --lookback P7D --granularity DAY`. See [cli.md](./cli.md#template-metrics).

## Pick a window and granularity

`granularity` sets the bucket size: `HOUR`, `DAY` (the default), `WEEK`, or `MONTH`. `WEEK` buckets start on Sunday. All boundaries are UTC, with no timezone support, so a "day" is a UTC day.

A finer granularity caps the window it can cover:

| Granularity | Maximum window |
|---|---|
| `HOUR` | 7 days |
| `DAY` | 90 days |
| `WEEK` | Uncapped |
| `MONTH` | Uncapped |

`WEEK` and `MONTH` have no window cap, but **every response is limited to 1000 buckets**, and a request that would exceed that returns `400` too.

Either one of `start`/`end` alone returns `400`, as does a `start` that is not earlier than `end`. An `end` in the future is accepted and not clamped, so the trailing buckets come back empty.

## Read the response

```json
{
  "notificationId": "nt_01kx4h2jdafq8bk9aftxak4b40",
  "granularity": "DAY",
  "start": "2026-08-17T00:00:00Z",
  "end": "2026-08-20T00:00:00Z",
  "series": [
    { "period": "2026-08-17T00:00:00Z", "data": [] },
    {
      "period": "2026-08-18T00:00:00Z",
      "data": [
        { "provider": "sendgrid", "channel": "email", "sent": 412, "delivered": 408, "opened": 173, "clicked": 41, "errors": 0, "undeliverable": 4 },
        { "provider": "twilio", "channel": "sms", "sent": 96, "delivered": 95, "opened": 0, "clicked": 12, "errors": 1, "undeliverable": 0 }
      ]
    }
  ]
}
```

`series` holds one entry per bucket between the snapped `start` and `end`, oldest first. Each entry has a `period` (the start of the bucket, UTC) and a `data` array with one row per provider and channel that handled a message in that bucket. Quiet buckets are still returned with `data: []`, so a series plots as-is with no gap filling on your side.

What each count means:

| Field | Means |
|---|---|
| `sent` | Messages handed to the provider |
| `delivered` | Provider confirmed delivery. Depends on the provider reporting it back |
| `opened` | Messages opened at least once. Always `0` on channels with no open tracking |
| `clicked` | Messages with at least one tracked link click |
| `errors` | Messages the provider rejected or failed on, **including ones a later provider then delivered** |
| `undeliverable` | Messages Courier could not deliver on any provider for the channel |

Because `errors` counts a provider-level failure even when a fallback succeeded, `errors > 0` with `undeliverable: 0` is a healthy multi-provider setup doing its job, not an outage.

## Fetch and roll up

```typescript
const metrics = await client.notifications.getMetrics(templateId, {
  lookback: "P7D",
  granularity: "DAY",
});

function totals(bucket) {
  return bucket.data.reduce(
    (acc, row) => ({
      sent: acc.sent + row.sent,
      delivered: acc.delivered + row.delivered,
      opened: acc.opened + row.opened,
    }),
    { sent: 0, delivered: 0, opened: 0 }
  );
}

for (const bucket of metrics.series) {
  const { sent, delivered, opened } = totals(bucket);
  console.log(bucket.period, {
    sent,
    deliveryRate: sent ? delivered / sent : null,
    openRate: delivered ? opened / delivered : null,
  });
}
```

Chart the range as `metrics.start` to `metrics.end`, which are the snapped values.

```python
metrics = client.notifications.get_metrics(
    template_id,
    lookback="P7D",
    granularity="DAY",
)

for bucket in metrics.series:
    sent = sum(row.sent for row in bucket.data)
    delivered = sum(row.delivered for row in bucket.data)
    print(bucket.period, delivered / sent if sent else None)
```

## Break out by channel

Each row already carries `provider` and `channel`, so comparing channel performance for one template needs no extra calls. Roll the whole series up by channel:

```typescript
const byChannel = {};

for (const bucket of metrics.series) {
  for (const row of bucket.data) {
    const c = (byChannel[row.channel] ??= { sent: 0, delivered: 0, opened: 0, clicked: 0 });
    c.sent += row.sent;
    c.delivered += row.delivered;
    c.opened += row.opened;
    c.clicked += row.clicked;
  }
}
```

Use that to decide which channel deserves to be primary in a [routing strategy](./routing-strategies.md), and remember `opened` is structurally `0` on channels without open tracking, so compare those on `clicked`.

## Plan limits and rate limits

| Plan | Max lookback | Requests per second |
|---|---|---|
| Developer (free) | 30 days | 1 |
| Business | 90 days | 2 |
| Enterprise | 730 days | 5 |

Rate limits are per workspace, and every response carries `RateLimit-*` headers, so a backfill can pace itself instead of guessing.

Walking every template in a workspace means one call per template against that limit. Read the headers and back off rather than firing the whole list concurrently:

```typescript
const { results, paging } = await client.notifications.list();

for (const template of results) {
  const metrics = await client.notifications.getMetrics(template.id, {
    lookback: "P30D",
    granularity: "DAY",
  });
  // handle metrics, then pace the next call on the plan's requests-per-second
}
```

`notifications.list()` is paginated, so a real workspace sweep pages through `paging` as well. See [templates.md](./templates.md#list-templates).

## Errors

| Status | `type` | When |
|---|---|---|
| 400 | `invalid_params` | Malformed duration or timestamp, one of `start`/`end` without the other, `start` not earlier than `end`, a granularity too fine for the window, or more than 1000 buckets |
| 402 | `payment_required` | The window reaches further back than the plan's cap. Not a truncated series |
| 429 | `rate_limit_exceeded` | Too many requests per second. Wait the seconds in `Retry-After` |
| 503 | `service_unavailable` | Temporary. Retry after the seconds in `Retry-After` |

## Not available via MCP

The API MCP server at `mcp.courier.com` has **no metrics tool**. Its notification tools cover create, retrieve, content, versions, publish, archive, duplicate, and checks only. Use an SDK call, the CLI (`courier notifications get-metrics`), or a plain HTTP request; see [mcp.md](./mcp.md#known-gaps).

## Related

- [templates.md](./templates.md) - the rest of the `/notifications` API: CRUD, publishing, versions
- [cli.md](./cli.md) - per-message triage when one send failed, rather than aggregates
- [reliability.md](./reliability.md) - delivery statuses and webhooks for real-time per-message events
- [multi-channel.md](./multi-channel.md) - acting on what the per-channel numbers tell you
- [Analytics](https://www.courier.com/docs/platform/analytics/analytics) - the same metrics in the Courier app
- [Template Metrics API docs](https://www.courier.com/docs/platform/analytics/template-metrics-api)
