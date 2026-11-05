# Reusable Patterns

Copy-paste code for cross-cutting concerns. The concepts and failure modes behind them are in [Reliability](./reliability.md).

**Contents:** [Quick Reference](#quick-reference) · [Idempotency Keys](#idempotency-keys) · [Multi-Channel Fallback](#multi-channel-fallback) · [Webhook Handler](#webhook-handler) · [Retries (the SDK already does this)](#retries-the-sdk-already-does-this) · [Sequence Cancellation](#sequence-cancellation) · [Lists and Audience Sends](#lists-and-audience-sends) · [Related](#related)

## Quick Reference

### Rules
- **Idempotency keys travel as the `Idempotency-Key` HTTP header**, never inside `message`. In Node pass `"Idempotency-Key": "..."` next to `message`. In Python pass `idempotency_key="..."`. In the CLI pass `--idempotency-key`. With curl, set the header. The Node `idempotencyKey` request option is not wired up, so don't use it. Keys last 25 hours by default. `{ headers: { "Idempotency-Key": … } }` as the second argument (Node) or `extra_headers=` (Python) sends the same header and also works. For a longer expiry use `"x-idempotency-expiration"` / `x_idempotency_expiration=` / `--x-idempotency-expiration`.

## Idempotency Keys

Node and Python: SKILL.md's [Canonical SDK Shape](../../SKILL.md#canonical-sdk-shape). CLI: `--idempotency-key order-confirmation-12345`. curl: `-H "Idempotency-Key: order-confirmation-12345"`. Every form, and the longer-expiry header, is in the [Rules](#rules). Key off a deterministic id from your own system (`otp-{userId}-{otpRequestId}`, not a timestamp), see [Reliability](./reliability.md#idempotency-key-patterns).

## Multi-Channel Fallback

`routing: { method: "single", channels: ["push", "email", "sms"] }` tries the channels in order until one succeeds; `method: "all"` sends to every channel at once. TypeScript and Python examples, escalation, and provider failover are in [Multi-Channel](./multi-channel.md).

## Webhook Handler

Acknowledge with a 2xx inside 10 seconds and process asynchronously. Dedupe on `data.id` **plus** status, since `data.id` is the resource id and repeats across a message's events. The full Express and Flask handlers, with signature verification, are in [Webhooks](./webhooks.md#verify-webhook-signatures).

## Retries (the SDK already does this)

**Don't hand-roll retry around a Courier SDK call.** Both SDKs retry `408`, `409`, `429`, `5xx`, and connection errors with backoff (see [Reliability](./reliability.md#retry-logic)), so your own loop multiplies attempts: your 3 tries times the SDK's 3 is 9 requests for one send. Tune it per client or per request instead:

```typescript
const client = new Courier({ maxRetries: 4 });            // default 2

await client.send.message({ message }, { maxRetries: 0 }); // disable for one call
```

```python
client = Courier(max_retries=4)

# Per-request, via with_options (message() itself takes no max_retries kwarg)
client.with_options(max_retries=0).send.message(message=...)
```

## Sequence Cancellation

Stop a sequence when the user does what it was nudging toward:

- **Inside a journey:** a `fetch` of the user's state and a `branch` to an `exit` before the next step end the run early. See the [fetch, branch and exit example](./journeys.md#delay-fetch-branch-and-exit-nodes).
- **From your app:** set a `cancelation_token` on the journey and call `client.journeys.cancel({ cancelation_token })` on the success event. See [Cancelling Runs](./journeys.md#cancelling-runs).
- **A single delayed send** (`message.delay`): cancel it with `client.messages.cancel(messageId)` while it's still pending.

## Lists and Audience Sends

Send to a group with one call. Courier fans out to every recipient.

### Lists

**TypeScript:**
```typescript
await client.lists.update("beta-testers", { name: "Beta Testers" });

// Add a single user to a list (additive; does not overwrite existing subscribers).
await client.lists.subscriptions.subscribeUser("user-123", { list_id: "beta-testers" });
await client.lists.subscriptions.subscribeUser("user-456", { list_id: "beta-testers" });

// Or replace the full subscriber set in one call:
// await client.lists.subscriptions.subscribe("beta-testers", {
//   recipients: [{ recipientId: "user-123" }, { recipientId: "user-456" }],
// });

await client.send.message({
  message: {
    to: { list_id: "beta-testers" },
    template: "nt_01kmrbs3q6w9x2c5v8n1d4tjh",
    data: { feature: "Design Studio" },
  },
});
```

Python uses snake_case: `client.lists.subscriptions.subscribe_user("user-123", list_id="beta-testers")`.

Send to every list matching a pattern with `to: { list_pattern: "eng.*" }`.

### Many recipients

Three ways to reach a lot of people. Pick by whether the recipient set is already modeled in Courier.

| Approach | Use when | Ceiling |
|---|---|---|
| `to: { list_id }` / `to: { audience_id }` | The set is already a list or audience | None; Courier fans out server-side |
| `to: [ ... ]` (multi-recipient send) | A handful of ad-hoc recipients | **500 recipients**, hard cap |
| [Bulk API](./bulk.md) | A large ad-hoc set, or you want per-recipient data and job-level progress | Ingest in batches of ≤1000 per call |

To upsert many profiles first, call `client.profiles.create` per user with a bounded worker pool.

## Related

- [CLI](./cli.md) - CLI for ad-hoc operations and debugging
- [Quickstart](./quickstart.md) - Send your first notification
- [Multi-Channel](./multi-channel.md) - Routing strategies
- [Reliability](./reliability.md) - Idempotency and retry details
- [Throttling](./throttling.md) - Rate limiting details
- [Batching](./batching.md) - Aggregation strategies
- [Preferences](./preferences.md) - User preference management
