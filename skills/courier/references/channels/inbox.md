# Inbox Channel

Sending to Courier's in-app inbox. The inbox is a delivery channel like email or SMS. You address it the same way, and Courier stores the message for the user to read in your app.

**Rendering the inbox in your app is a separate concern**, JWT auth, the React / Web Component / React Native / iOS / Android / Flutter SDKs, read state, and real-time updates all live in [inbox/rendering.md](../inbox/rendering.md).

## Quick Reference

### Rules

- Title under 50 characters; body under 150
- 1–2 actions maximum
- Always include deep-link data in `data`, a click with nowhere to go is a dead end
- Batch similar events rather than sending ten "liked your post" messages
- No OS permission needed, so the inbox reaches every user. It is the safe default channel **once the `courier` provider is configured**, see [Setup](#setup)

### Common mistakes

- Sending one message per event instead of batching
- Omitting deep-link data, so the click does nothing
- Not archiving the inbox copy when the user engages via email or push
- Assuming the inbox needs no configuration. It needs the `courier` provider installed, and `simple_profile_req` set, see [Setup](#setup)
- Sending a template by id with no routing strategy attached. API-created templates start with `routing: null` and fail `UNROUTABLE`, see [Troubleshooting](#troubleshooting)
- Reaching for the `{ title, body }` sugar in a stored template. That form is inline-only, see [Elemental Content for Inbox](#elemental-content-for-inbox)

---

## Setup

The inbox needs no OS permission and no third-party account, but it is **not** zero-configuration. It delivers through a built-in provider named `courier`, which has to be installed on the workspace:

```bash
curl -X POST https://api.courier.com/providers \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "courier",
    "settings": { "jwt_enabled": true, "simple_profile_req": true }
  }'
```

| Setting | Why |
|---|---|
| `jwt_enabled` | Lets browser and mobile clients authenticate with a short-lived JWT, which the v8 inbox SDKs require. See [inbox/auth.md](../inbox/auth.md) |
| `simple_profile_req` | Without it, the provider expects a `courier.channel` value inside each user's profile and sends fail with "Information required by the provider was not included." |

`simple_profile_req` is the one that affects sending: without it, sends fail `UNROUTABLE`. `jwt_enabled` affects client authentication, not delivery. See [Troubleshooting](#troubleshooting), and [providers.md](../guides/providers.md) for the provider API in general.

## Sending to Inbox

### Basic Inbox Message

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbvb7x1q5v8d2c6n4w9hj",
    data: {
      commenterName: "Jane",
      commentPreview: "Great post!",
      postId: "post-456"
    },
    routing: {
      method: "single",
      channels: ["inbox"]
    }
  }
});
```

### Inbox with Actions

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "New friend request",
      body: "Jane Doe wants to connect",
      data: {
        requestId: "req-789"
      }
    },
    channels: {
      inbox: {
        override: {
          actions: [
            {
              content: "Accept",
              href: "acme://friends/accept/req-789",
              style: "primary"
            },
            {
              content: "Decline",
              href: "acme://friends/decline/req-789",
              style: "secondary"
            }
          ]
        }
      }
    }
  }
});
```

### Inbox + Push (Multi-Channel)

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: {
      orderNumber: "12345",
      trackingUrl: "https://acme.co/track/12345"
    },
    routing: {
      method: "all",
      channels: ["inbox", "push"]
    }
  }
});
```

## Read State

Read and unread state is managed client-side by the Inbox SDK. From the server you archive, which removes the message from the user's inbox.

Archive an inbox message from the server with `client.requests.archive(requestId)`:

```typescript
await client.requests.archive(messageId);
```

Read state is managed client-side through the Inbox SDK. Archive from the backend to remove a message from the inbox when the user engages via another channel.

### Batching and Digests

Don't send individual notifications for each event:

```typescript
// Instead of 10 separate notifications, send one batched:
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Your post is getting attention!",
      body: "Jane, Bob, and 8 others liked your post"
    }
  }
});
```

See [Batching](../guides/batching.md) for comprehensive batching strategies.

## Cross-Channel Sync

When a user opens an email, mark the inbox message as read:

```typescript
// Email click webhook
app.post('/email-clicked', async (req, res) => {
  const { messageId, userId } = req.body;

  // Archive the inbox message since the user engaged via email
  await client.requests.archive(messageId);
});
```

## Elemental Content for Inbox

The `{ title, body }` shorthand used in the examples above **only works for inline sends**. It is not valid for template creation via the API ([elemental.md](../guides/elemental.md)). A stored inbox template uses Elemental, wrapped in a `channel` element, which is also the shape Design Studio writes for the inbox:

```json
{
  "version": "2022-01-01",
  "elements": [
    {
      "type": "channel",
      "channel": "inbox",
      "elements": [
        { "type": "meta", "title": "Your report is ready" },
        { "type": "text", "content": "The August usage report finished generating.", "align": "left" },
        { "type": "action", "content": "View report", "href": "{{report_url}}" }
      ]
    }
  ]
}
```

The `channel` wrapper selects which content renders on the inbox. It does not select delivery, see [the four places a channel is named](../guides/elemental.md#the-channel-element-vs-the-three-other-places-a-channel-is-named).

## Troubleshooting

| Symptom | Cause |
|---|---|
| `UNROUTABLE`, no `reason` and no `error` field | No `courier` provider on the workspace. See [Setup](#setup) |
| `UNROUTABLE`, "Information required by the provider was not included." | `courier` provider is missing `simple_profile_req` |
| `UNROUTABLE` / `PROVIDER_ERROR`, "No provider(s) courier in the list of message channel provider(s): undefined." | The template has no routing strategy attached. See below |
| Template send fails but the same content sent inline succeeds | Same cause. Inline content never consults the template's routing, so this comparison misleads rather than isolating the bug |
| Message sent, never visible in the app | Client-side. See [inbox/rendering.md](../inbox/rendering.md) |

### "No provider(s) courier ... : undefined"

The `undefined` in that error is the template's missing routing strategy: `GET /notifications/{id}` on a template that fails this way returns `routing: null`. A template in that state cannot be sent to the inbox by id, because nothing names `courier` as the inbox provider. Templates reach that state in practice, so **check `routing` with a `GET` before assuming the template is fine**, see [templates.md](../guides/templates.md).

Two ways out:

- **Attach a routing strategy** whose `channels.inbox.providers` includes `courier`, via `PUT /notifications/{id}`. This is the real fix. See [routing-strategies.md](../guides/routing-strategies.md).
- **Override on the message** with `channels: { inbox: { providers: ["courier"] } }`. This is a per-send workaround, not a general requirement, and shouldn't be copied into every send.

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbvb7x1q5v8d2c6n4w9hj",
    routing: { method: "single", channels: ["inbox"] },
    channels: { inbox: { providers: ["courier"] } }, // per-send override
  },
});
```

A strategy that names an unconfigured provider fails differently and just as quietly, see [routing-strategies.md](../guides/routing-strategies.md).

## Related

- [Push](./push.md), pair inbox with push so the message reaches users who aren't in the app
- [Multi-Channel](../guides/multi-channel.md), inbox in routing strategies
- [Batching](../guides/batching.md), aggregating events into one inbox message
- [Preferences](../guides/preferences.md), letting users turn inbox categories off
- [Elemental](../guides/elemental.md), content that renders in the inbox
