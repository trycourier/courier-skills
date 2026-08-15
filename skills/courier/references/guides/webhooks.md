# Webhooks

Two separate features that share a settings page and nothing else.

| Direction | What it is | Configure at |
|---|---|---|
| **[Outbound](#outbound-webhooks)** | Courier `POST`s workspace events (message delivered, template published, audience changed) to *your* endpoint | Settings → Webhooks → Outbound Webhooks |
| **[Inbound](#inbound-webhooks)** | *Your* systems `POST` JSON to a Courier-generated URL; the events can start journeys | Settings → Webhooks → Inbound Webhooks |

Both live under [Settings > Webhooks](https://app.courier.com/settings/webhooks), under **Developers**.

Neither is a send path. To *send* a notification over an HTTP callback, that's the webhook
*channel* on a template, which is a different thing again.

<a id="outbound-webhooks"></a>

## Outbound Webhooks

### Setup

1. Settings → Webhooks → **Outbound Webhooks** → **Add**.
2. Name it and give it a URL that accepts `POST`.
3. Set a **secret** if you want signed payloads. Without one, Courier sends no signature header.

> **Webhooks are scoped to the environment they're created in.** A webhook created in test only
> fires for test events, and never for production ones. If you need both, create a destination in
> each environment. This is the most common "my webhook never fires" cause.

### Event Types

Every payload is `{ "type": "...", "data": { ... } }`. Branch on `type`, and ignore unknown
values, since more types get added over time.

| Event type | Fired when |
|---|---|
| `message:updated` | A message changes status |
| `notification:submitted` | A template is submitted for review |
| `notification:submission_canceled` | A pending submission is canceled before publishing |
| `notification:published` | A template is published (directly, or when a submission is approved) |
| `audiences:updated` | An audience is created or updated |
| `audiences:user:matched` | A user starts matching an audience filter |
| `audiences:user:unmatched` | A user stops matching an audience filter |
| `audiences:calculated` | Courier finishes recalculating an audience |

There is no `message:bounced` or `message:complained`. Hard bounces and spam complaints arrive as
`message:updated` with `data.status` of `UNDELIVERABLE`, the aggregate cause in `data.reason`, and
the provider's own message in `data.providers[].error`. Drive list hygiene off those fields.

The three `notification:*` events are the hook for TMS integrations and custom approval workflows.
`notification:published` is the one to listen for if you sync template content to an external system.

`audiences:user:matched` is the same event behind the journey Audience trigger. React to it with a
webhook, or start a journey, whichever fits.

### Responding

Courier gives your endpoint **10 seconds**. Acknowledge first, then do the real work in a queue or
background job. A slow dependency on your side turns into a delivery failure on Courier's.

Retries, when the failure looks temporary:

| Outcome | Retried |
|---|---|
| Network error, or no response inside 10 seconds | Yes |
| `408`, `429`, or any `5xx` | Yes |
| Any other `4xx` | No |

Retries continue for roughly a day, then Courier gives up.

**Events can arrive more than once, so handlers must be idempotent.** Note that `data.id` identifies
the *resource*, not the event. One message emits several events that all carry the same `data.id`.
Deduplicate on `data.id` **plus** `data.status` (or the event type), never on `data.id` alone.

### message:updated Payloads

Timestamp fields accumulate as the message progresses, so a `CLICKED` event still carries
`enqueued`, `sent`, `delivered`, and `opened`.

| Status | What it adds to `data` |
|---|---|
| `ENQUEUED` | `enqueued` |
| `SENT` | `sent`, plus `sent` on the matching entry in `providers` |
| `DELIVERED` | `delivered`, plus `delivered` on the matching entry in `providers` |
| `OPENED` | `opened` |
| `CLICKED` | `clicked` |
| `UNROUTABLE` | `reason` (e.g. `NO_PROVIDERS`) and `error`. `providers` is empty. |
| `UNDELIVERABLE` | `reason` (e.g. `UNSUBSCRIBED`) and `error`, plus `error` on the failing provider entry |

`data` matches what [`GET /messages/{id}`](https://www.courier.com/docs/api-reference/sent-messages/get-message)
returns, and carries any metadata on the message: `trace_id`, `tags`, `event`, and `utm`.

```json
{
  "type": "message:updated",
  "data": {
    "id": "1-612fa552-15f7d6ba51bf229857c037a7",
    "status": "DELIVERED",
    "enqueued": 1630512466717,
    "sent": 1630512468691,
    "delivered": 1630512501708,
    "event": "SFTYJKSF0241SVH2TWY97TTFFTQG",
    "notification": "SFTYJKSF0241SVH2TWY97TTFFTQG",
    "recipient": "b19fb0e0-8cd6-4337-b41c-92c780c80d1a",
    "providers": [
      {
        "provider": "slack",
        "status": "DELIVERED",
        "channel": { "key": "direct_message:slack", "name": "Slack" },
        "sent": 1630512468691,
        "delivered": 1630512501708
      }
    ]
  }
}
```

Delivery statuses like `DELIVERED` depend on the provider confirming asynchronously, while
engagement statuses (`OPENED`, `CLICKED`) are tracked by Courier directly. **Engagement events can
arrive before delivery confirmation, or without it ever arriving.** Don't write a state machine that
assumes `DELIVERED` precedes `OPENED`.

For the full status list and what each one means, see [reliability.md](./reliability.md#message-status-glossary).

<a id="verify-webhook-signatures"></a>

### Verifying Signatures

Set a secret on the destination and Courier signs every event with HMAC-SHA256 in a
`courier-signature` header:

```
t=1631816343012,signature=33777cdae0468ff0939b3609d02d14e6e80ca093c2ea233455f0767055218875
```

`t` is when Courier signed the event, in **milliseconds** since the epoch. `signature` is a
hex-encoded HMAC-SHA256 over `${t}.${raw_body}`, keyed with the webhook secret.

Four steps: split the header on `,` then each part on `=`; build `signed_payload` as
`timestamp + "." + raw body`; compute the HMAC; compare in constant time. Also reject events whose
timestamp falls outside a tolerance window you pick, which bounds how long a captured request stays
replayable.

> **Verify against the raw bytes, not a re-serialized object.** `JSON.stringify` on a parsed body
> can reorder keys or change whitespace, producing a hash that never matches. Configure the
> framework to keep the raw body: `express.raw()`, or Next.js with the body parser disabled.

**TypeScript (Express):**

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
    res.sendStatus(200);              // ack inside 10s
    queue.add("process-webhook", payload);
  }
);
```

**Python (Flask):**

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
    raw_body = request.get_data()          # raw bytes, before Flask parses JSON
    signature = request.headers.get("courier-signature")
    if not verify_webhook_signature(
        raw_body, signature, os.environ["COURIER_WEBHOOK_SECRET"]
    ):
        return "", 401

    queue.enqueue("process_webhook", request.get_json())
    return "", 200
```

### Checklist

1. Acknowledge with a 2xx inside 10 seconds; process asynchronously.
2. Deduplicate on `data.id` plus status. Redelivery is expected, and `data.id` alone is not unique per event.
3. Verify the signature against raw bytes, in constant time, with a timestamp tolerance.
4. Ignore unrecognized `type` values instead of erroring.
5. Keep the secret in an environment variable.
6. Create the destination in **every environment** you need it in.

<a id="inbound-webhooks"></a>

## Inbound Webhooks

The other direction: Courier hands you a URL, third-party systems `POST` JSON to it, and the events
that arrive can start journeys. Use one when a system can fire an HTTP request but can't call the
Courier API.

### Setup

1. Settings → Webhooks → **Inbound Webhooks** → **Add**.
2. Give it a name and description, and save.
3. Courier generates the URL: `https://api.courier.com/inbound/webhook/<token>`.

**The name is permanent.** You select the webhook by name wherever you consume its events, and its
events are tied to that name, so pick something recognizable.

```bash
curl -X POST https://api.courier.com/inbound/webhook/YOUR_WEBHOOK_TOKEN \
  -H "Content-Type: application/json" \
  -d '{
    "event": "order-shipped",
    "userId": "user_123",
    "properties": { "order_id": "ORD-9042", "carrier": "UPS" }
  }'
```

No API key and no auth header. The token in the URL identifies the workspace, **so treat the URL as
a secret**. Anyone holding it can push events into the workspace. If it leaks, delete the webhook
and create a new one to get a fresh URL.

### Payload Rules

Courier accepts any payload up to **6 MB** and answers `202` once accepted. A `404` means the URL is
wrong or the webhook was deleted.

| Payload | What Courier does |
|---|---|
| JSON object | Parses it and exposes the fields as data |
| JSON array | Unpacks it, and each object becomes its own event |
| Anything else | Keeps the payload as a string on a `raw` field and names the event `custom` |

Two reserved fields:

| Field | Purpose |
|---|---|
| `event` | Event name, used to pick which events start a journey. Must be a string. Absent → the event is named `custom`. |
| `userId` | Identifies the recipient. Courier resolves the user and loads their profile. String or number, coerced to string. |

Every other field passes through as data.

> **`userId` must match an existing Courier user.** Without a resolvable recipient there is nothing
> to send to, so the event will not start a journey. This is the most common reason an inbound
> event lands but nothing happens.

### Using the Events

Point a journey's **Webhook trigger** at the webhook by name, then optionally narrow to a single
`event` name. Leave it empty to start on any event from that source. Payload fields become
`data.<field>` on the run.

> **Send real traffic before you build.** Courier learns event names and payload shape from events
> it has actually received. Until at least one event arrives, the event picker and variable hints
> are empty. The editor infers fields flattened four levels deep; anything nested deeper shows up as
> a single object field. Without a selected event name, the editor unions fields across every event
> seen on that source, so a suggested field may not exist on every payload.

**The Webhook trigger is Design Studio only.** The Journeys API exposes just two `trigger_type`
values, `api-invoke` and `segment`. There is no webhook trigger node you can `POST`, so build these
journeys in the UI. See [journeys.md](./journeys.md#triggers).

## Related

- [reliability.md](./reliability.md): delivery statuses, idempotency, retries
- [patterns.md](./patterns.md#webhook-handler): copy-paste handler skeleton
- [journeys.md](./journeys.md): trigger types and journey structure
- [Outbound Webhooks](https://www.courier.com/docs/platform/workspaces/outbound-webhooks) · [Inbound Webhooks](https://www.courier.com/docs/platform/workspaces/inbound-webhooks)
