# Notification Throttling

## Quick Reference

### Rules
- **Inside a journey, the `throttle` node is the rate limiter**: `scope: "user"`, `"global"`, or `"dynamic"` with a `throttle_key`, plus `max_allowed` and an ISO 8601 `period`. It counts passes through that node only
- **[Send limits](https://www.courier.com/docs/send/statuses#send-limits)** cap what a user, topic, or tenant receives across every send, per hour, day, week, month, or billing period. Blocked messages end `THROTTLED` and never send later. Send limits have no API endpoint, so code and MCP can't set them; set them in the Courier app. A provider's **[send rate limit](./providers.md#send-rate-limits)** is different: it caps how fast Courier sends through that provider, and queues the extra sends instead of blocking them
- **For user-facing cadence control, prefer [digest schedules](./digests.md)** over your own throttle: the recipient picks the frequency and Courier does the collecting
- **The SDK already handles provider `429`s** on your call to Courier (see [reliability.md](./reliability.md#retry-logic)); provider-side rate limits are Courier's job during delivery

### Common Mistakes
- Rebuilding rate limiting in application code when the send is already inside a journey that could carry a `throttle` node
- Expecting `metadata.tags` to throttle anything (they are an analytics/filtering handle, not a control)
- Hand-rolling a 429 retry around the SDK, which already retries with backoff

---

## Courier Throttling Features

For quiet hours, use a [delivery window](./scheduling.md#delivery-window-business-hours-quiet-hours), not a throttle.

### Journey Throttle Node

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

Place the throttle before the send node. Once a user hits the cap, later runs skip the send. Nothing waits or retries, so if the excess should arrive later, use a [`batch` node](./batching.md) or a [digest](./digests.md) instead.

## Provider Rate Limits

To cap how fast Courier sends through one provider config, set a [send rate limit](./providers.md#send-rate-limits) (`settings.rate_limit`) on it with an `add` operation on `PATCH /providers/{id}`. The limit covers the whole config, per environment. Sends above the rate are queued, not dropped. Provider-side rate limits are absorbed by Courier's own delivery retries (up to 24 hours), then fail over to another provider or channel.

## Related

- [Journeys](./journeys.md) - Native throttle nodes for journey-level rate limiting
- [Batching](./batching.md) - Combining notifications
- [Reliability](./reliability.md) - Handling rate limit errors
- [Preferences](./preferences.md) - User frequency settings
- [Multi-Channel](./multi-channel.md) - Channel-specific limits
