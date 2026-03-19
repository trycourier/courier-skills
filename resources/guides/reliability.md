# Reliability

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
| Password reset | `password-reset-{userId}-{timestamp}` |
| Payment receipt | `payment-receipt-{paymentId}` |
| Shipping update | `shipping-{shipmentId}-{status}` |
| OTP code | `otp-{userId}-{timestamp}` |
| Welcome email | `welcome-{userId}` |

### Common Mistakes
- Missing idempotency keys (causes duplicate notifications)
- Static idempotency keys for notifications that should repeat (OTP needs timestamp)
- Retrying 4xx errors (they won't succeed, fix the issue)
- Blocking on webhook processing (should be async)
- Not handling webhook duplicates
- No fallback providers configured
- No alerting on high failure rates

### Templates

See [Patterns](./patterns.md) for full copy-paste implementations: [Idempotency Keys](./patterns.md#idempotency-keys), [Webhook Handler](./patterns.md#webhook-handler), [Retry with Backoff](./patterns.md#retry-with-exponential-backoff).

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

| Notification Type | Idempotency Key Pattern |
|-------------------|------------------------|
| Order confirmation | `order-confirmation-{orderId}` |
| Password reset | `password-reset-{userId}-{timestamp}` |
| Payment receipt | `payment-receipt-{paymentId}` |
| Shipping update | `shipping-{shipmentId}-{status}` |
| OTP code | `otp-{userId}-{timestamp}` |

### Don't Over-Dedupe

Some notifications should be sent multiple times:

- **OTP codes:** User might request multiple. Use timestamp to allow new sends.
- **Welcome messages:** Only send once. Use static key like `welcome-{userId}`.

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

Courier signs every webhook payload with an HMAC-SHA256 signature in the request headers. Always verify in production.

**TypeScript (Express):**

Use `express.raw()` on the webhook route so you verify against the exact bytes Courier sent, not a re-serialized version:

```typescript
import crypto from "crypto";
import express from "express";

function verifyWebhookSignature(
  rawBody: Buffer,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(rawBody)
    .digest("hex");
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

app.post(
  "/webhooks/courier",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const signature = req.headers["x-courier-signature"] as string;
    if (
      !signature ||
      !verifyWebhookSignature(
        req.body,
        signature,
        process.env.COURIER_WEBHOOK_SECRET!
      )
    ) {
      return res.sendStatus(401);
    }

    const payload = JSON.parse(req.body.toString());
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

def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

@app.route("/webhooks/courier", methods=["POST"])
def courier_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("X-Courier-Signature", "")
    if not verify_webhook_signature(
        raw_body, signature, os.environ["COURIER_WEBHOOK_SECRET"]
    ):
        return "", 401

    queue.enqueue("process_webhook", request.get_json())
    return "", 200
```

### Common Webhook Events

| Event | Trigger | Useful for |
|-------|---------|------------|
| `message.delivered` | Message reached recipient | Delivery tracking |
| `message.undeliverable` | All channels/providers failed | Alerting, fallback logic |
| `message.bounced` | Email hard/soft bounce | List hygiene |
| `message.complained` | User marked as spam | Remove from lists |
| `message.opened` | Email opened (pixel tracked) | Engagement metrics |
| `message.clicked` | Link clicked | Conversion tracking |

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
