# Reliability

> **Reading order:** This file covers **concepts and failure modes** (idempotency semantics, retry strategy, delivery statuses, provider failover). For short recipes, see [Patterns](./patterns.md). For webhooks in either direction, see [Webhooks](./webhooks.md).

**Contents:** [Quick Reference](#quick-reference) · [Idempotency](#idempotency) · [Retry Logic](#retry-logic) · [Webhooks](#webhooks) · [Related](#related)

## Quick Reference

### Rules
- ALWAYS use idempotency keys for transactional notifications, so a retried request returns the first response instead of sending the message twice
- Courier keeps idempotency keys for 25 hours by default. Send `x-idempotency-expiration` as a number of seconds, not a date (`604800` is a week), to keep one up to a year
- A key replays its first response, errors included. Retry with the same key only after a connection error, a timeout, `409` or `429`, starting at 60 seconds. For any other `4xx` or `5xx`, fix the cause and send with a new key ([retry a request safely](https://www.courier.com/docs/reference/api-overview#retry-a-request-safely))
- A send made while a person waits (an HTTP request handler) sets SDK `maxRetries: 0` and retries from a queue. The SDK's own retries wait out `Retry-After` and can hold the request for up to two minutes

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
- A static idempotency key on a send that should repeat (an OTP needs a per-request key, `otp-{userId}-{otpRequestId}`)
- Wrapping an SDK call in your own retry loop, which multiplies attempts (the SDK already retries transient failures) and hits the key's 60-second hold as `409`
- Retrying a `500` or a `400` with the same key, which only replays the stored error

### Message Status Glossary

The value returned as `message.status` from `client.messages.retrieve` (and the `status` field on `messages list` rows and webhook events). Happy-path progression is roughly `ENQUEUED → ROUTED → SENT → DELIVERED`; terminal failures are `UNROUTABLE` and `UNDELIVERABLE`. A send can also settle into `CANCELED`, `THROTTLED`, `DIGESTED`, or `DELAYED` without ever reaching a provider.

| Status | Meaning | Typical cause / next step |
|--------|---------|---------------------------|
| `ENQUEUED` | Courier has accepted the request and queued it for routing. | Transient, re-check in a few seconds. |
| `ROUTED` | Routing decision made; message is ready to hand to a provider. | Transient. |
| `SENT` | At least one provider accepted the payload for delivery. For email this means the provider returned 2xx; for Inbox it means the message is visible in the feed. | Transient on the way to `DELIVERED`, but terminal for Inbox and for any provider without delivery tracking set up. Slack, Teams and webhook sends go straight to `DELIVERED`. |
| `DELIVERED` | Provider confirmed the message reached the recipient (e.g. email DSN, SMS carrier report). | Terminal success. |
| `OPENED` / `CLICKED` | Engagement signals for email (requires open/click tracking). **`OPENED` is not a reliable signal of human engagement**: privacy proxies prefetch the tracking pixel. Build logic on `CLICKED` or in-app read state. | Terminal success with engagement. |
| `UNMAPPED` | The alias in `template` (or the legacy `event`) matched no template in this environment, for example an alias that was renamed. Common for bulk sends with a typo'd `event` value. An unknown `nt_` ID ends `UNDELIVERABLE` ("Notification template not found") instead. | Use an alias that exists in this environment. Changing a template's `notification.alias` leaves the old name `UNMAPPED`. |
| `UNROUTABLE` | Routing failed, no channel/provider combination could accept the send. Check `reason` and `error`, and read `error` rather than matching its wording, which varies by release. `reason: "PROVIDER_ERROR"` usually means the channel's routing list names a provider that isn't installed. An inbox send with no `reason` and no `error` at all, or a `PROVIDER_ERROR` naming `courier` with `: undefined`, has its own causes: see [inbox.md](../channels/inbox.md#troubleshooting). | Fix provider configuration in [Integrations](https://app.courier.com/integrations), adjust `routing.channels`, or populate the user's contact info. |
| `UNDELIVERABLE` | All providers attempted returned a terminal failure (bounce, invalid number, suppressed), or the template couldn't be loaded ("Notification template not found" for an unknown `nt_` ID, "... has no published version"). | Read `error` first: a template error means fixing the ID or publishing; otherwise verify the recipient's contact info and inspect `providers[].providerResponse`. |
| `CANCELED` | The send was canceled before delivery, via `client.messages.cancel`, a journey Cancel node, or a canceled journey run. | Expected when you cancel; otherwise check what issued the cancel. |
| `THROTTLED` | Blocked by a [send limit](https://www.courier.com/docs/send/statuses#send-limits) (per user, topic, or tenant) or by the Developer plan's cap of 10,000 sends per period. It is not queued and won't send later. | If you set no limit, it is usually the plan cap. Otherwise raise the limit or widen its window. |
| `DIGESTED` / `DELAYED` | Held rather than sent now, rolled into a digest, or waiting out a `delay`. | Transient; the message sends when the digest releases or the delay elapses. |

Other statuses you may see on list rows, `FILTERED` (suppressed by a preference or condition) and `SIMULATED` (a test send that was never dispatched), are terminal and need no action.

- **A provider's `UNDELIVERABLE` isn't the message's.** In a send with several providers or channels, the message history records an `UNDELIVERABLE` event per provider before the message reaches its final status. Act on the message-level status, not on one provider's event.
- **Render errors aren't retried.** A template error such as `Missing helper: "json"` fails the message without retries. Fix the template, publish, and make a new send.

Statuses are returned verbatim on webhooks and on `GET /messages/{id}`. For list/bulk sends, a single `requestId` can fan out to many per-recipient `message_id`s, each with its own status, each id is `<requestId>:<user_id>` (see [CLI debugging](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id)).

---

## Idempotency

Send the `Idempotency-Key` header (retention is in the Rules above). A key is scoped to the endpoint it was sent to, and the stored response includes errors: a key whose first request got a `400` or a `500` keeps returning it, so use a new key after fixing the cause. Only a request that stored nothing runs again: a connection error or timeout, a `429` (answered before the request runs), or a `409` while Courier holds the key for 60 seconds. See [retry a request safely](https://www.courier.com/docs/reference/api-overview#retry-a-request-safely). Code in every language: [Patterns > Idempotency Keys](./patterns.md#idempotency-keys).

## Retry Logic

Three layers retry independently. Know which one you're looking at before adding your own.

### 1. The SDK client, for your call to Courier

Both SDKs retry automatically: `maxRetries` defaults to **2** (3 requests total), covering `408`,
`409`, `429`, `5xx`, and connection errors, with exponential backoff from 0.5s capped at 8s plus
jitter. Other `4xx` are not retried. `retry-after` is honored when the server sends it, so a
`409` or `429` can make the call wait up to 60 seconds per retry. A `5xx` retried with the same key
gets the stored `5xx` back.

That wait is fine in a background job. **In a request handler, where a person waits, set
`maxRetries: 0`** and hand failures to your queue ([layer 3](#3-your-ingest-path)). **Don't wrap an
SDK call in your own retry loop**, or the attempts multiply. Configure it instead:
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

Don't reimplement it. Courier keeps trying a message for up to 72 hours in total (24 hours is the provider-retry schedule above). To shorten that for one send, set `message.timeout.message` in milliseconds. `timeout.message`, `timeout.escalation`, and `timeout.criteria` work on every plan; `timeout.channel` and `timeout.provider` return `402` below the Business tier. `message.channels.<channel>.timeouts` returns `400` even though the SDK types it, so use `message.timeout` instead. See [routing timeouts](https://www.courier.com/docs/send/routing#timeouts). Watch it in
[Message Logs](https://www.courier.com/docs/monitor/overview) or via
`courier messages history`.

Those are both per-message views. For the aggregate trend across a whole template, use
[metrics.md](./metrics.md).

### 3. Your ingest path

The layer that is genuinely yours. If a send is part of a larger unit of work that must survive a
process crash, that belongs in your queue or job runner, not in a wrapper around the SDK. Pair it
with an [idempotency key](#idempotency) so a replay doesn't double-send. Retry with the same key
only connection errors, timeouts, `409` and `429`, and start the first retry at 60 seconds, after
Courier's hold on the key ends. Fail the job on any other error.

## Webhooks

Courier `POST`s workspace events to your endpoint. Everything about handling them is in [webhooks.md](./webhooks.md): the 10-second ack, retries for about a day, deduping on `data.id` **plus** status, verifying `courier-signature` against the raw bytes ([Verifying Signatures](./webhooks.md#verify-webhook-signatures)), per-environment destinations, engagement events arriving before `DELIVERED`, and bounces arriving as `message:updated` with `UNDELIVERABLE`.

## Related

- [Webhooks](./webhooks.md) - Outbound event handling and inbound webhooks
- [Multi-Channel](./multi-channel.md) - Fallback routing
- [Throttling](./throttling.md) - Rate limiting and frequency control
- [Batching](./batching.md) - Combining notifications
- [Transactional](../transactional.md) - Critical notification patterns
