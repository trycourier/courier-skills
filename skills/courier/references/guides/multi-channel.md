# Multi-Channel Routing

**Contents:** [Quick Reference](#quick-reference) · [Routing Methods](#routing-methods) · [Escalation Patterns](#escalation-patterns) · [Channel-Specific Formatting](#channel-specific-formatting) · [User Preferences Integration](#user-preferences-integration) · [Cross-Channel Coordination](#cross-channel-coordination) · [Provider Failover](#provider-failover) · [Monitoring & Analytics](#monitoring--analytics) · [Related](#related)

## Quick Reference

### Rules
- `method: "single"`: Try channels in order until one succeeds (use for most cases)
- `method: "all"`: Send to all channels simultaneously (use for critical alerts)
- Each channel requires user to have valid contact info (email, phone, push token)
- Channel order in array = priority order for fallbacks
- Courier auto-checks user preferences when configured
- Use idempotency keys to prevent duplicate sends across retries

### Channel Selection by Use Case
| Use Case | Method | Channels |
|----------|--------|----------|
| OTP/2FA | single | [sms, email] |
| Password reset | single | [email] |
| Order confirmation | single | [email] |
| Order shipped | all | [email, push] |
| Security alert | all | Tiered by severity, see [Security Alert Channels](../transactional.md#security-alert-channels). Lowest tier: `[email, push]`; highest tier: `[email, push, sms, inbox]` |
| Activity mention | all | [push, inbox] |
| Weekly digest | single | [email] |

Rationale for "order shipped": email is the durable record; push is the awareness nudge. `method: "all"` automatically skips channels where the user has no contact info (no push token = push skipped (`INCOMPLETE_PROFILE_DATA` in the log), email still sent). Inbox is intentionally omitted, a shipping notification doesn't need in-app persistence.

### Routing Edge Cases
| Situation | Behavior |
|-----------|----------|
| `user_id` has no email, email is first in `channels` | Skips email, tries next channel |
| `user_id` has no contact info at all | The message ends `UNROUTABLE`, and each skipped provider shows `INCOMPLETE_PROFILE_DATA` in the log. An `inbox` channel in the route needs no contact info, so it can still send. |
| User opted out of a channel via preferences | Channel skipped automatically |
| `routing` omitted entirely | Courier uses channels configured in the template |
| Provider returns 5xx | Courier retries, then tries next provider in priority order |
| All providers for a channel fail | With `method: "single"`, falls through to next channel |

---

## Routing Methods

Courier provides two core routing methods:

### Single Channel (`method: "single"`)

Try channels in priority order until one succeeds. Best for most notifications where you want exactly one delivery.

**TypeScript (generic fallback, email first):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbzj3q6x9v2d5c8n1w4ht",
    routing: {
      method: "single",
      channels: ["email", "sms"]
    }
  }
});
```

**Behavior:**
1. Attempt the first channel
2. If it fails (no contact info, provider error), try the next
3. Stop after first successful delivery

### All Channels (`method: "all"`)

Send to all specified channels simultaneously. Best for critical notifications.

**TypeScript:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrc06x1q5v8d2c6n4w9hj",
    routing: {
      method: "all",
      channels: ["email", "push", "sms"]
    }
  }
});
```

**Behavior:**
- Attempts delivery to all channels in parallel
- Each channel is independent (one failure doesn't affect others)
- User receives on all channels where they have valid contact info

## Escalation Patterns

### Time-Based Escalation

Start with less intrusive channel, escalate if no engagement:

```
T+0:      In-app notification
T+15min:  Push notification (if unread)
T+1hr:    Email (if still unread)
T+24hr:   SMS (if critical and still unread)
```

Build it as a [journey](./journeys.md): send (inbox) → `delay` `PT15M` → `fetch` your app's read state → `branch` (read → `exit`; otherwise send push → `delay` `PT1H` → send email). Node shapes and a worked delay → fetch → branch → exit journey: [journeys.md](./journeys.md#delay-fetch-branch-and-exit-nodes).

The fetch checks inbox read state in your own app, so keep it for an in-app first step: a read is not
a click. When the earlier step is an email, push, or SMS and a click is the engagement you care about,
branch on its send status instead (`["send_status.<nodeId>", "was not", "CLICKED"]`). See
[Branching on an earlier send](./journeys.md#branching-on-an-earlier-send).

### Delivery-Based Escalation

**What triggers fallback:** a channel fails, and `single` moves to the next one, when the recipient has no address for it (no email, no phone, no push token) or every provider on it has failed. Courier retries transient provider errors before moving on. A bounce or other recipient-level failure reported after the provider accepted the message doesn't trigger fallback (see [When Failover Triggers](#when-failover-triggers)).

## Channel-Specific Formatting

Same notification, optimized for each channel:

### Complete Multi-Channel Example

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: {
      orderNumber: "12345",
      carrier: "FedEx",
      trackingNumber: "TRACK123",
      estimatedDelivery: "Thursday, January 30",
      items: [
        { name: "Widget Pro", quantity: 2 }
      ]
    },
    routing: {
      method: "all",
      channels: ["email", "push", "inbox"]
    },
    channels: {
      email: {
        override: {
          subject: "Your order #12345 has shipped!"
        }
      },
      push: {
        override: {
          title: "Order shipped! 📦",
          body: "Arriving Thursday. Tap to track.",
          data: {
            deepLink: "acme://orders/12345",
            image: "https://acme.com/images/package.png"
          }
        }
      }
    }
  }
});
```

## User Preferences Integration

Courier checks the user's preferences on every send. An opt-out of the template's topic stops the send. A user's per-topic channel choice (`custom_routing`) **replaces** the template's routing when `has_custom_routing` is true and the topic has channel selection enabled; without both, the template's routing applies. Topics, sections and the preference shape: [preferences.md](./preferences.md).

## Cross-Channel Coordination

### Read State Sync

To stop a follow-up after the user engages, cancel that follow-up by its own message ID while it is still pending (for example a delayed send), or branch in a journey. `client.messages.cancel` can't retract a message that already reached the feed.

Don't key escalation or suppression on `OPENED`: image-proxy prefetch fires it for recipients who never saw the message. Use `CLICKED`, in-app read state, or an action in your product (see [reliability.md](./reliability.md)).

### Cancellation

With [Journeys](./journeys.md), build exit logic directly into the DAG using branch nodes and exit nodes, the journey checks conditions before each step and exits early when appropriate. See [Patterns, Sequence Cancellation](./patterns.md#sequence-cancellation) for details.

## Provider Failover

### Setup (Dashboard)

1. Go to **Channels** in the [Courier dashboard](https://app.courier.com/channels)
2. Add multiple providers for the same channel type (e.g., two email providers)
3. Drag to set priority order. Courier tries top-to-bottom
4. Each provider needs its own credentials (API key, etc.)

### Setup (API)

The same setup can be done over the API, configure the provider integrations via `/providers`, then define priority order per channel via a routing strategy's `channels.{channel}.providers` array. The position of a provider key in that array is the drag-to-reorder equivalent.

- See [providers.md](./providers.md) for configuring provider integrations (catalog discovery, key rotation, per-provider `settings`).
- See [routing-strategies.md](./routing-strategies.md) for the full routing strategy CRUD, per-provider `override`/`if`/`timeouts`, and how to link the resulting `rs_...` to templates via `routing.strategy_id`.

### When Failover Triggers

Courier fails over to the next provider when:
- Provider returns a 5xx error (after built-in retries)
- Provider is slower than its timeout. Setting `timeout.provider` or `timeout.channel` on a send returns `402` below the Business tier
- Provider-specific permanent error (e.g., invalid credentials)
- Provider rate-limits the send, once Courier's retries (up to 24 hours) run out

Courier does NOT fail over for:
- Recipient-level failures (invalid email, bounced)
- Template rendering errors

### Checking Which Provider Was Used

Inspect the message delivery history to see which provider handled a send:

```bash
courier messages history --message-id "1-abc123" --format json
```

The history shows each provider attempt with timestamps and status.

### Provider-Specific Overrides

Per-send `providers.{key}.override` changes one provider's request without touching its stored config. See [providers.md](./providers.md#per-send-provider-overrides-recap).

## Monitoring & Analytics

### Track Per Channel

| Metric | What It Tells You | Where it comes from |
|--------|-------------------|---------------------|
| Delivery rate | % successfully delivered | `sent` and `delivered` from [metrics.md](./metrics.md) |
| Open/read rate | User engagement | `opened`, structurally `0` on channels with no open tracking |
| Click-through rate | Action taken | `clicked` |
| Bounce/failure rate | Data quality issues | `errors` and `undeliverable` |
| Unsubscribe rate | Channel fatigue | Not in the metrics API. Track your own opt-outs, see [preferences.md](./preferences.md) |

### Track Routing Effectiveness

Don't hand-roll these numbers. `GET /notifications/{id}/metrics` returns them per provider and channel, per bucket:

```typescript
const metrics = await client.notifications.getMetrics(templateId, {
  lookback: "P30D",
  granularity: "DAY",
});

const byChannel: Record<string, number> = {};
for (const bucket of metrics.series) {
  for (const row of bucket.data) {
    byChannel[row.channel] = (byChannel[row.channel] ?? 0) + row.clicked;
  }
}
// e.g. { email: 2000, push: 3500 } -> push out-engages email here, consider making it primary
```

Compare on `clicked`, not `opened`: `opened` is structurally `0` on channels with no open tracking. Full parameters and response shape in [metrics.md](./metrics.md).

## Related

- [Routing Strategies](./routing-strategies.md) - Create/replace stored `rs_...` strategies via API
- [Providers](./providers.md) - Configure provider integrations via API (catalog, settings, rotation)
- [Preferences](./preferences.md) - User channel preferences
- [Reliability](./reliability.md) - Failover and retry logic
- [Batching](./batching.md) - Combining notifications
- [Throttling](./throttling.md) - Rate limiting per channel
- [Email](../channels/email.md) - Email-specific guidance
- [SMS](../channels/sms.md) - SMS-specific guidance
- [Push](../channels/push.md) - Push notification guidance
- [Inbox](../channels/inbox.md) - In-app notifications
- [Slack](../channels/slack.md) - Slack integration
- [MS Teams](../channels/ms-teams.md) - Teams integration
- [WhatsApp](../channels/whatsapp.md) - WhatsApp integration
