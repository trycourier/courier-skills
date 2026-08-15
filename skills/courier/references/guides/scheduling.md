# Scheduling and Delays

Courier can defer a single send natively. You don't queue it in your own app and fire it later. Set `message.delay` and Courier holds the message until the right time. Three modes, all on the same field.

## Quick Reference

### Rules

- **`message.delay` defers one send.** For a delay that's one step inside a multi-step flow, use a journey [`delay` node](./journeys.md) instead.
- **Duration is rounded up to the next minute.** `90000` ms (90 s) delivers at 2 minutes. Don't rely on sub-minute precision.
- **A delivery window delays until the *next* open time.** A send outside the window isn't dropped. It waits.
- **Cancel a still-pending scheduled send** with `client.messages.cancel(messageId)` if its trigger goes stale. See [Patterns](./patterns.md#sequence-cancellation).

### The three modes

| Mode | Field | Delivers |
|---|---|---|
| Duration | `delay: { duration: <ms> }` | That many milliseconds from now (rounded up to the minute) |
| Timestamp | `delay: { until: "<ISO 8601>" }` | At an exact date/time |
| Delivery window | `delay: { until: "<opening-hours>", timezone: "<IANA>" }` | At the next moment inside the allowed hours |

## Duration delay

Delay by a number of milliseconds from now.

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_reminder",
    delay: { duration: 3600000 }, // 1 hour
    data: { task_name: "Review the quarterly report" },
  },
});
```

Handy values: 5 min `300000`, 1 hour `3600000`, 1 day `86400000`.

## Timestamp delay

Schedule for an exact moment with an ISO 8601 string. A date alone resolves to midnight UTC; include a time and offset (or `Z`) to be precise.

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_meeting_reminder",
    delay: { until: "2026-01-15T09:00:00-05:00" }, // 9am US Eastern
  },
});
```

## Delivery window (business hours, quiet hours)

Restrict delivery to allowed hours with an opening-hours expression. Courier sends immediately if the current time is inside the window, otherwise it waits for the next open slot. This is the native way to honor quiet hours. You do **not** need to build a scheduler.

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_activity_summary",
    delay: {
      until: "Mo-Fr 09:00-17:00",
      timezone: "America/Los_Angeles",
    },
  },
});
// Sent Thursday noon → delivers now. Sent Saturday → delivers Monday 9:00am PT.
```

Opening-hours patterns: business hours `Mo-Fr 09:00-17:00`, weekends `Sa-Su 00:00-23:59`, split `Mo-Fr 09:00-12:00,14:00-18:00`, single day `Mo 09:00-17:00`. Start is inclusive; end is exclusive.

**Timezone resolution** (highest priority first). `delay.timezone` only applies to opening-hours `until` values, an ISO timestamp already carries its own offset.

1. `message.delay.timezone`
2. `message.to.timezone`, or the user profile's `zoneinfo`
3. the user profile's `timezone`
4. `UTC`

## When to reach for what

| You want | Use |
|---|---|
| One send, later | `message.delay` (this file) |
| A delay between steps of a sequence | journey [`delay` node](./journeys.md) (`mode: duration` or `mode: until`) |
| "Never during quiet hours" on every send | `message.delay` delivery window, not app-side logic |
| Recurring / cron scheduling | a journey on a Segment/schedule trigger, or Broadcasts for one-off list sends |

Never re-implement a scheduler in your application when a duration, a timestamp, or a delivery window on the send does the job.

## Related

- [Journeys](./journeys.md), multi-step flows and the `delay` node
- [Patterns](./patterns.md), cancelling a pending scheduled send when its trigger goes stale
- [Throttling](./throttling.md), frequency caps and fatigue, a separate concern from scheduling
