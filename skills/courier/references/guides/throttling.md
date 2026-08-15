# Notification Throttling

## Quick Reference

### Rules
- **Courier's native rate limiter is the journey `throttle` node**: `scope: "user"`, `"global"`, or `"dynamic"` with a `throttle_key`, plus `max_allowed` and an ISO 8601 `period`
- **Courier does not throttle plain `send.message` calls server-side.** A frequency cap on direct sends is either a journey in front of the send or logic in your application
- **For user-facing cadence control, prefer [digest schedules](./preferences.md#digest-schedules)** over your own throttle: the recipient picks the frequency and Courier does the collecting
- **The SDK already handles provider `429`s** on your call to Courier (see [reliability.md](./reliability.md#retry-logic)); provider-side rate limits are Courier's job during delivery

### Common Mistakes
- Rebuilding rate limiting in application code when the send is already inside a journey that could carry a `throttle` node
- Expecting `metadata.tags` to throttle anything (they are an analytics/filtering handle, not a control)
- Hand-rolling a 429 retry around the SDK, which already retries with backoff

---

Control notification frequency to prevent overwhelming users and respect rate limits.

## Throttling vs Batching

| Concept | Purpose | Mechanism |
|---------|---------|-----------|
| **Throttling** | Limit frequency | Drop or delay excess |
| **Batching** | Combine related | Aggregate into one |

Use both together for optimal notification delivery.

## Courier Throttling Features

### Metadata Tags for Your Own Analytics

Courier does not throttle sends server-side based on arbitrary tags, the `metadata.tags` field is primarily a grouping and filtering handle for your own analytics, message logs, and webhook consumers. Attach tags so you can later filter `courier messages list --tag ...`, slice analytics, or drive your own rate-limit decisions in the application tier.

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbuc9q3x7v1d5c8n2w6hj",
    data: { /* ... */ },
    metadata: {
      tags: ["social", "low-priority"]
    }
  }
});
```

Provider-level rate limits (e.g. SendGrid/Twilio caps) are enforced per provider. See [Provider Rate Limits](#provider-rate-limits) below for the 429 retry pattern. For user-facing cadence control, use [digest schedules](./preferences.md#digest-schedules) on a subscription topic, where the recipient picks the frequency. For quiet hours, use a [delivery window](./scheduling.md#delivery-window-business-hours-quiet-hours).

### Journey Throttling (Recommended)

[Journeys](./journeys.md) have a native `throttle` node that rate-limits runs per user, globally, or by a dynamic key:

```json
{
  "id": "throttle-per-user",
  "type": "throttle",
  "scope": "user",
  "max_allowed": 5,
  "period": "PT1H"
}
```

Scope options: `user` (per recipient), `global` (across all runs), `dynamic` (custom key via `throttle_key`). See [Journeys, Node Types Reference](./journeys.md#node-types-reference) for full details.

Configure in dashboard:
1. **Throttle step:** Max 5 per hour per user
2. **Delay step:** Wait if limit exceeded
3. **Send step:** Deliver notification

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

A `429` from Courier's API is retried by the SDK automatically, with backoff and `retry-after`
honored, so don't wrap the call in your own 429 handler (see
[reliability.md](./reliability.md#retry-logic)). Provider-side rate limits are absorbed by Courier's
own delivery retries, which continue for up to 24 hours.

## Related

- [Journeys](./journeys.md) - Native throttle nodes for journey-level rate limiting
- [Batching](./batching.md) - Combining notifications
- [Reliability](./reliability.md) - Handling rate limit errors
- [Preferences](./preferences.md) - User frequency settings
- [Multi-Channel](./multi-channel.md) - Channel-specific limits
