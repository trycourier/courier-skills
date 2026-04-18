# Reliability

> **Reading order:** This file covers **concepts and failure modes** (idempotency semantics, retry strategy, webhook delivery guarantees, provider failover). For **copy-paste code** implementing these patterns in TypeScript, Python, CLI, and curl, see [Patterns](./patterns.md).

## Quick Reference

### Rules
- ALWAYS use idempotency keys for transactional notifications
- Courier stores idempotency keys for 24 hours
- Don't retry 4xx errors (client errors) - fix the issue instead
- DO retry 5xx errors with exponential backoff
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

Use a **request id** (the unique id of the OTP/reset attempt from your own system) rather than a timestamp — it's deterministic on retry, so the second attempt of the *same* OTP request gets deduped while a legitimate *new* OTP request gets a fresh key.

### Common Mistakes
- Missing idempotency keys (causes duplicate notifications)
- Static idempotency keys for notifications that should repeat (OTP needs a unique per-request ID, not a fixed key)
- Retrying 4xx errors (they won't succeed, fix the issue)
- Blocking on webhook processing (should be async)
- Not handling webhook duplicates
- No fallback providers configured
- No alerting on high failure rates

### Templates

See [Patterns](./patterns.md) for full copy-paste implementations: [Idempotency Keys](./patterns.md#idempotency-keys), [Webhook Handler](./patterns.md#webhook-handler), [Retry with Backoff](./patterns.md#retry-with-exponential-backoff).

### Message Status Glossary

The value returned as `message.status` from `client.messages.retrieve` (and the `status` field on `messages list` rows and webhook events). Happy-path progression is roughly `ENQUEUED → ROUTED → SENT → DELIVERED`; terminal failures are `UNROUTABLE`, `UNDELIVERABLE`, and `FAILED`.

| Status | Meaning | Typical cause / next step |
|--------|---------|---------------------------|
| `ENQUEUED` | Courier has accepted the request and queued it for routing. | Transient — re-check in a few seconds. |
| `PROCESSED` | Internal processing step (event mapping, template resolution). You may see this briefly on list rows. | Transient. |
| `ROUTED` | Routing decision made; message is ready to hand to a provider. | Transient. |
| `SENT` | At least one provider accepted the payload for delivery. For email this means the provider returned 2xx; for Inbox it means the message is visible in the feed. | Transient on the way to `DELIVERED`, or terminal for Inbox/webhook channels. |
| `DELIVERED` | Provider confirmed the message reached the recipient (e.g. email DSN, SMS carrier report). | Terminal success. |
| `OPENED` / `CLICKED` | Engagement signals for email (requires open/click tracking). | Terminal success with engagement. |
| `UNMAPPED` | The `event` on the send didn't map to any notification/template in this workspace. Common for bulk sends with a typo'd `event` value. | Fix the event ID or create an event mapping in Settings. |
| `UNROUTABLE` | Routing failed — no channel/provider combination could accept the send. Check `reason` and `error` for detail (e.g. `reason: "PROVIDER_ERROR"` with message `"No provider(s) resend in the list of message channel provider(s): postmark."` means the channel's routing list references a provider that isn't installed). | Fix provider configuration in [Integrations](https://app.courier.com/integrations), adjust `routing.channels`, or populate the user's contact info. |
| `UNDELIVERABLE` | All providers attempted returned a terminal failure (bounce, invalid number, suppressed). | Verify the recipient's contact info; inspect `providers[].providerResponse` for the specific error. |
| `FAILED` | Platform-side error (rare). | Retry; if persistent, contact Courier support with the `id`. |

Statuses are returned verbatim on webhooks and on `GET /messages/{id}`. For list/bulk sends, a single `requestId` can fan out to many per-recipient `message_id`s, each with its own status — look them up via `courier messages list --trace-id "<requestId>"` (see [CLI debugging](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id)).

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

### Courier's Built-In Retry

Courier automatically retries failed sends. You can configure:
- Number of retries
- Retry intervals
- Which errors to retry

### Custom Retry for Your Backend

If your call to Courier fails, implement retry with exponential backoff:

1. Don't retry client errors (4xx) - fix the issue instead
2. Retry server errors (5xx) and network errors
3. Use exponential backoff: 2s, 4s, 8s...
4. Add jitter to prevent thundering herd
5. Set a maximum retry count

### Exponential Backoff

Calculate delay as: `min(baseDelay * 2^(attempt-1), maxDelay) + random jitter`

Example: 1s base, 30s max → delays of ~1s, ~2s, ~4s, ~8s, ~16s, ~30s

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

### Setup

1. Go to **Settings > Webhooks** in the [Courier dashboard](https://app.courier.com/settings/webhooks)
2. Add your endpoint URL (e.g., `https://api.acme.com/webhooks/courier`)
3. Copy the **signing secret** — you'll use it to verify payloads
4. Select which events to subscribe to (or receive all)

Courier retries failed webhook deliveries (non-2xx response) with exponential backoff for up to 24 hours.

### Verify Webhook Signatures

Courier signs every webhook payload with an HMAC-SHA256 signature in the `courier-signature` header. The header value has the form:

```
t=<unix_timestamp_ms>,signature=<hex_hmac_sha256>
```

The signed payload is `${timestamp}.${raw_request_body}`. Always verify in production — and also reject old timestamps (default tolerance 5 minutes) to prevent replay attacks.

**TypeScript (Express):**

Use `express.raw()` on the webhook route so you verify against the exact bytes Courier sent, not a re-serialized version:

```typescript
import crypto from "crypto";
import express from "express";

function parseCourierSignature(header: string | undefined) {
  if (!header) return null;
  const parts = header.split(",").reduce<Record<string, string>>((acc, part) => {
    const [k, v] = part.split("=");
    if (k && v) acc[k.trim()] = v.trim();
    return acc;
  }, {});
  if (!parts.t || !parts.signature) return null;
  return { timestamp: parts.t, signature: parts.signature };
}

function verifyWebhookSignature(
  rawBody: Buffer,
  header: string | undefined,
  secret: string,
  toleranceMs = 5 * 60 * 1000
): boolean {
  const parsed = parseCourierSignature(header);
  if (!parsed) return false;

  const ts = Number(parsed.timestamp);
  if (!Number.isFinite(ts) || Math.abs(Date.now() - ts) > toleranceMs) {
    return false;
  }

  const expectedHex = crypto
    .createHmac("sha256", secret)
    .update(`${parsed.timestamp}.${rawBody.toString("utf8")}`, "utf8")
    .digest("hex");

  const a = Buffer.from(parsed.signature, "hex");
  const b = Buffer.from(expectedHex, "hex");
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

app.post(
  "/webhooks/courier",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["courier-signature"] as string | undefined;
    if (
      !verifyWebhookSignature(
        req.body,
        signature,
        process.env.COURIER_WEBHOOK_SECRET!
      )
    ) {
      return res.sendStatus(401);
    }

    const payload = JSON.parse(req.body.toString("utf8"));
    res.sendStatus(200);
    queue.add("process-webhook", payload);
  }
);
```

**Python (Flask):**

Use `request.get_data()` to get the raw bytes before Flask parses JSON:

```python
import hmac
import hashlib
import os
import time


def parse_courier_signature(header: str | None):
    if not header:
        return None
    parts = {}
    for chunk in header.split(","):
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            parts[k.strip()] = v.strip()
    if "t" not in parts or "signature" not in parts:
        return None
    return parts["t"], parts["signature"]


def verify_webhook_signature(
    raw_body: bytes,
    header: str | None,
    secret: str,
    tolerance_ms: int = 5 * 60 * 1000,
) -> bool:
    parsed = parse_courier_signature(header)
    if not parsed:
        return False
    timestamp, signature = parsed

    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs(int(time.time() * 1000) - ts) > tolerance_ms:
        return False

    signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}"
    expected = hmac.new(
        secret.encode(), signed_payload.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@app.route("/webhooks/courier", methods=["POST"])
def courier_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("courier-signature")
    if not verify_webhook_signature(
        raw_body, signature, os.environ["COURIER_WEBHOOK_SECRET"]
    ):
        return "", 401

    queue.enqueue("process_webhook", request.get_json())
    return "", 200
```

### Common Webhook Events

Courier webhook events use **colon notation** in the `type` field and carry event-specific data under `data`. For `message:updated`, the delivery stage is in `data.status` (one of `ENQUEUED`, `SENT`, `DELIVERED`, `OPENED`, `CLICKED`, `UNDELIVERABLE`, `UNROUTABLE`).

| `type` | `data.status` / trigger | Useful for |
|--------|-------------------------|------------|
| `message:updated` | `DELIVERED` — message reached recipient | Delivery tracking |
| `message:updated` | `UNDELIVERABLE` — all channels/providers failed (check `data.reason`) | Alerting, fallback logic |
| `message:updated` | `UNROUTABLE` — no eligible channel/provider for recipient | Data quality, profile fixes |
| `message:updated` | `OPENED` — email open pixel tracked | Engagement metrics |
| `message:updated` | `CLICKED` — tracked link clicked | Conversion tracking |
| `notification:submitted` | Template submitted for review | Approval workflows |
| `notification:published` | Template published | Cache invalidation, audit logging |
| `audiences:user:matched` / `audiences:user:unmatched` | User entered/left an audience | Sync downstream systems |

> **Note on bounces/complaints:** Courier does not emit dedicated `message:bounced` or `message:complained` events. Hard bounces and spam complaints typically surface as `UNDELIVERABLE` `message:updated` events with the provider-specific reason in `data.providers[].error` and the aggregated reason in `data.reason`. Inspect those fields to drive list-hygiene logic.

### Webhook Best Practices

1. Respond immediately with 200 OK
2. Process in background queue
3. Use idempotent processing (check if already handled)
4. Verify webhook signatures
5. Store the signing secret in environment variables, never in code

## Related

- [Multi-Channel](./multi-channel.md) - Fallback routing
- [Throttling](./throttling.md) - Rate limiting and frequency control
- [Batching](./batching.md) - Combining notifications
- [Transactional](../transactional/index.md) - Critical notification patterns
- [Billing](../transactional/billing.md) - Dunning retry strategies
