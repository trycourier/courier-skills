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

**Send with Idempotency Key:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_CONFIRMATION",
    data: { orderId: "12345" }
  }
}, {
  idempotencyKey: `order-confirmation-12345`
});
```

**Webhook Handler:**
```typescript
app.post('/webhooks/courier', async (req, res) => {
  res.sendStatus(200); // Respond immediately
  
  // Process async
  await queue.add('process-webhook', req.body);
});
```

**Retry with Backoff:**
```typescript
const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
await sleep(delay + Math.random() * 1000);
```

---

Ensure notifications are delivered reliably with idempotency, retry logic, and error handling.

## Idempotency

### Why It Matters

Without idempotency, you might send duplicate notifications if:
- Network timeout occurs but request succeeded
- Your application retries a failed request
- Webhook is delivered multiple times

### Courier Idempotency Keys

Add the `Idempotency-Key` header to your API requests. Courier stores keys for 24 hours and returns cached responses for duplicate requests.

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_CONFIRMATION",
    data: { orderId: "12345" }
  }
}, {
  idempotencyKey: `order-confirmation-12345`
});
```

Or with raw HTTP:

```bash
curl -X POST https://api.courier.com/send \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-confirmation-12345" \
  -d '{"message": {...}}'
```

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

### Receiving Courier Webhooks

Process delivery events, bounces, complaints from Courier:

1. **Verify signature:** Ensure webhook is from Courier
2. **Respond quickly:** Return 200 before heavy processing
3. **Process asynchronously:** Queue work for background processing
4. **Handle duplicates:** Webhooks may be delivered multiple times

### Common Webhook Events

- `message.delivered` - Message was delivered
- `message.bounced` - Email bounced
- `message.complained` - User marked as spam
- `message.opened` - Email was opened
- `message.clicked` - Link was clicked

### Webhook Best Practices

1. Respond immediately with 200 OK
2. Process in background queue
3. Use idempotent processing (check if already handled)
4. Verify webhook signatures

## Dead Letter Queue

### Handle Permanently Failed Notifications

When a notification exceeds maximum retries:
1. Move to dead letter queue
2. Mark as permanently failed
3. Alert operations team
4. Log for debugging

### Monitor Dead Letter Queue

Set up alerts when DLQ grows beyond threshold. Items in DLQ need manual investigation.

## Circuit Breaker

### Prevent Cascade Failures

If Courier (or any downstream service) is experiencing issues, a circuit breaker prevents overwhelming it:

**States:**
- **Closed:** Normal operation, requests go through
- **Open:** Service is down, requests fail fast (don't wait)
- **Half-Open:** Testing if service recovered

**Transitions:**
- Closed → Open: After N consecutive failures
- Open → Half-Open: After timeout period
- Half-Open → Closed: On successful request
- Half-Open → Open: On failed request

## Monitoring

### Key Metrics

- **Send success rate:** % of sends that succeed
- **Delivery rate:** % delivered (not bounced)
- **Latency:** Time from trigger to delivery
- **Retry rate:** How often retries are needed
- **DLQ size:** Items in dead letter queue

### Alerting

Set up alerts for:
- Success rate below 95%
- Latency exceeds 5 seconds
- Dead letter queue exceeds threshold
- Circuit breaker opens

## Best Practices

### Always Use Idempotency Keys

Every notification send should include an idempotency key to prevent duplicates.

### Log for Debugging

Log every send attempt with:
- Notification ID
- Template name
- Result (success/failure)
- Duration
- Error details (if failed)

### Graceful Degradation

If primary channel fails, fall back to secondary:
1. Try primary channel (e.g., push)
2. If failed, try fallback (e.g., email)
3. Log which channel succeeded

## Related

- [Multi-Channel](./multi-channel.md) - Fallback routing
- [Throttling](./throttling.md) - Rate limiting and frequency control
- [Batching](./batching.md) - Combining notifications
- [Transactional](../transactional/index.md) - Critical notification patterns
- [Billing](../transactional/billing.md) - Dunning retry strategies
