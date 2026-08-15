# Reliability

> **Reading order:** This file covers **concepts and failure modes** (idempotency semantics, retry strategy, delivery statuses, provider failover). For **copy-paste code** implementing these patterns in TypeScript, Python, CLI, and curl, see [Patterns](./patterns.md). For webhooks in either direction, see [Webhooks](./webhooks.md).

## Quick Reference

### Rules
- ALWAYS use idempotency keys for transactional notifications
- Courier stores idempotency keys for 24 hours
- The SDK client already retries `408`, `409`, `429`, `5xx`, and connection errors (`maxRetries` defaults to 2). Tune it rather than wrapping calls in your own loop
- Other `4xx` are not retried by anyone. Fix the request instead
- Respond to webhooks with 200 immediately, process async
- Handle webhook duplicates (they can be delivered multiple times)
- Configure multiple providers per channel for failover

### Idempotency Key Patterns
| Notification | Key Pattern |
|--------------|-------------|
| Order confirmation | `order-confirmation-{orderId}` |
| Password reset | `password-reset-{userId}-{resetRequestId}` |
| Payment receipt | `payment-receipt-{paymentId}` |
| Shipping update | `shipping-{shipmentId}-{status}` |
| OTP code | `otp-{userId}-{otpRequestId}` |
| Welcome email | `welcome-{userId}` |

Use a **request id** (the unique id of the OTP/reset attempt from your own system) rather than a timestamp. It's deterministic on retry, so the second attempt of the *same* OTP request gets deduped while a legitimate *new* OTP request gets a fresh key.

### Common Mistakes
- Missing idempotency keys (causes duplicate notifications)
- Static idempotency keys for notifications that should repeat (OTP needs a unique per-request ID, not a fixed key)
- Adding a retry loop around an SDK call, which multiplies attempts (the SDK already retries transient failures)
- Blocking on webhook processing (should be async)
- Not handling webhook duplicates
- No fallback providers configured
- No alerting on high failure rates

### Templates

See [Patterns](./patterns.md) for full copy-paste implementations: [Idempotency Keys](./patterns.md#idempotency-keys) and [Webhook Handler](./patterns.md#webhook-handler).

### Message Status Glossary

The value returned as `message.status` from `client.messages.retrieve` (and the `status` field on `messages list` rows and webhook events). Happy-path progression is roughly `ENQUEUED → ROUTED → SENT → DELIVERED`; terminal failures are `UNROUTABLE` and `UNDELIVERABLE`. A send can also settle into `CANCELED`, `THROTTLED`, `DIGESTED`, or `DELAYED` without ever reaching a provider.

| Status | Meaning | Typical cause / next step |
|--------|---------|---------------------------|
| `ENQUEUED` | Courier has accepted the request and queued it for routing. | Transient, re-check in a few seconds. |
| `ROUTED` | Routing decision made; message is ready to hand to a provider. | Transient. |
| `SENT` | At least one provider accepted the payload for delivery. For email this means the provider returned 2xx; for Inbox it means the message is visible in the feed. | Transient on the way to `DELIVERED`, or terminal for Inbox/webhook channels. |
| `DELIVERED` | Provider confirmed the message reached the recipient (e.g. email DSN, SMS carrier report). | Terminal success. |
| `OPENED` / `CLICKED` | Engagement signals for email (requires open/click tracking). **`OPENED` is not a reliable signal of human engagement**, Apple Mail Privacy Protection and Gmail image proxying prefetch the tracking pixel, so it fires without the recipient reading anything. Build logic on `CLICKED` or in-app read state. | Terminal success with engagement. |
| `UNMAPPED` | The `event` on the send didn't map to any notification/template in this workspace. Common for bulk sends with a typo'd `event` value. | Fix the event ID or create an event mapping in Settings. |
| `UNROUTABLE` | Routing failed, no channel/provider combination could accept the send. Check `reason` and `error` for detail (e.g. `reason: "PROVIDER_ERROR"` with message `"No provider(s) resend in the list of message channel provider(s): postmark."` means the channel's routing list references a provider that isn't installed). | Fix provider configuration in [Integrations](https://app.courier.com/integrations), adjust `routing.channels`, or populate the user's contact info. |
| `UNDELIVERABLE` | All providers attempted returned a terminal failure (bounce, invalid number, suppressed). | Verify the recipient's contact info; inspect `providers[].providerResponse` for the specific error. |
| `CANCELED` | The send was canceled before delivery, via `client.messages.cancel`, a journey Cancel node, or a canceled journey run. | Expected when you cancel; otherwise check what issued the cancel. |
| `THROTTLED` | Dropped by a `throttle` node that had reached its cap. | Expected under frequency caps; raise the cap or widen the window if unintended. |
| `DIGESTED` / `DELAYED` | Held rather than sent now, rolled into a digest, or waiting out a `delay`. | Transient; the message sends when the digest releases or the delay elapses. |

Other statuses you may see on list rows, `FILTERED` (suppressed by a preference or condition) and `SIMULATED` (a test send that was never dispatched), are terminal and need no action.

Statuses are returned verbatim on webhooks and on `GET /messages/{id}`. For list/bulk sends, a single `requestId` can fan out to many per-recipient `message_id`s, each with its own status, look them up via `courier messages list --trace-id "<requestId>"` (see [CLI debugging](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id)).

---

Ensure notifications are delivered reliably with idempotency, retry logic, and error handling.

## Idempotency

### Why It Matters

Without idempotency, you might send duplicate notifications if:
- Network timeout occurs but request succeeded
- Your application retries a failed request
- Webhook is delivered multiple times

### Courier Idempotency Keys

Add the `Idempotency-Key` header to your API requests. Courier stores keys for 24 hours and returns cached responses for duplicate requests. See [Patterns > Idempotency Keys](./patterns.md#idempotency-keys) for TypeScript, Python, CLI, and curl examples.

### Key Patterns

See [Idempotency Key Patterns](#idempotency-key-patterns) in the Quick Reference above for the canonical table.

### Don't Over-Dedupe

Some notifications should be sent multiple times:

- **OTP / password reset:** User might request multiple. Key off the unique request id (e.g. `otp-{userId}-{otpRequestId}`) so a legitimate new request gets a fresh key while a retry of the same request is deduped.
- **Welcome messages:** Only send once. Use a static key like `welcome-{userId}`.

## Retry Logic

Three layers retry independently. Know which one you're looking at before adding your own.

### 1. The SDK client, for your call to Courier

Both SDKs retry automatically: `maxRetries` defaults to **2** (3 requests total), covering `408`,
`409`, `429`, `5xx`, and connection errors, with exponential backoff from 0.5s capped at 8s plus
jitter. Other `4xx` are not retried. `retry-after` is honored when the server sends it.

**Don't wrap an SDK call in your own retry loop**, or the attempts multiply. Configure it instead:
`new Courier({ maxRetries: 4 })`, or per request `{ maxRetries: 0 }`. See
[Patterns](./patterns.md#retries-the-sdk-already-does-this).

### 2. Courier, for its delivery to the provider

Once Courier accepts a send, it owns delivery. It retries provider outages, timeouts, rate limits,
and transient errors on its side:

| Layer | Timeline |
|---|---|
| Message delivery | First 10 attempts exponential (5s to 15 min), then every 15 min, up to **24 hours** and ~104 attempts |
| Status tracking | Delivery/open/click tracking continues for up to **72 hours** |
| Webhook delivery | Retried for about **24 hours** (see [webhooks.md](./webhooks.md#responding)) |

This is not configurable, and it is not something to reimplement. Watch it in
[Message Logs](https://www.courier.com/docs/platform/analytics/message-logs) or via
`courier messages history`.

### 3. Your ingest path

The layer that is genuinely yours. If a send is part of a larger unit of work that must survive a
process crash, that belongs in your queue or job runner, not in a wrapper around the SDK. Pair it
with an [idempotency key](#idempotency) so a replay doesn't double-send.


## Error Handling

### Error Categories

| Category | Example | Action |
|----------|---------|--------|
| Client error (4xx) | Invalid template | Don't retry, fix issue |
| Server error (5xx) | Service unavailable | Retry with backoff |
| Network error | Timeout | Retry with backoff |
| Rate limit (429) | Too many requests | Retry with longer delay |

### Handling Different Errors

- **400 Bad Request:** Log, alert engineering, don't retry
- **429 Rate Limited:** Queue for later with 60+ second delay
- **5xx Server Error:** Retry with exponential backoff
- **Unknown Error:** Log, alert, don't retry

## Webhooks

Courier `POST`s workspace events to your endpoint: message status changes, template publishes,
audience membership changes. Setup, the full event-type list, payload shapes, signature
verification in TypeScript and Python, and **inbound** webhooks all live in
[webhooks.md](./webhooks.md).

The parts that matter for reliability:

- **Acknowledge with a 2xx inside 10 seconds**, then process asynchronously. A slow handler becomes
  a delivery failure.
- **Retries** cover network errors, timeouts, `408`, `429`, and any `5xx`, for roughly a day. Any
  other `4xx` is not retried.
- **Redelivery is expected**, so handlers must be idempotent. `data.id` identifies the *resource*, not
  the event, so a single message emits several events sharing it. Dedupe on `data.id` **plus**
  status, never `data.id` alone.
- **Verify the `courier-signature` HMAC against the raw request bytes**, in constant time, with a
  timestamp tolerance. See [Verifying Signatures](./webhooks.md#verify-webhook-signatures).
- **Webhooks only fire in the environment they were created in.** A test-environment destination
  never sees production events.
- Engagement statuses (`OPENED`, `CLICKED`) can arrive **before** `DELIVERED`, or without it ever
  arriving. Don't assume ordering.

Bounces and spam complaints have no dedicated event type. They arrive as `message:updated` with
`data.status` of `UNDELIVERABLE`, the aggregate cause in `data.reason`, and the provider's message
in `data.providers[].error`.

## Related

- [Webhooks](./webhooks.md) - Outbound event handling and inbound webhooks
- [Multi-Channel](./multi-channel.md) - Fallback routing
- [Throttling](./throttling.md) - Rate limiting and frequency control
- [Batching](./batching.md) - Combining notifications
- [Transactional](../transactional.md) - Critical notification patterns
- [Billing](../transactional.md) - Dunning retry strategies
