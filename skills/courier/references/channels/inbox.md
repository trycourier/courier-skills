# Inbox Channel

Sending to Courier's in-app inbox. The inbox is a delivery channel like email or SMS. You address it the same way, and Courier stores the message for the user to read in your app.

**Rendering the inbox in your app is a separate concern**, JWT auth, the React / Web Component / React Native / iOS / Android / Flutter SDKs, read state, and real-time updates all live in [inbox/rendering.md](../inbox/rendering.md).

## Quick Reference

### Rules

- Title under 50 characters; body under 150
- 1–2 actions maximum
- Always include deep-link data in `data`, a click with nowhere to go is a dead end
- Batch similar events rather than sending ten "liked your post" messages
- No OS permission needed, so the inbox reaches every user. It is the safe default channel

### Common mistakes

- Sending one message per event instead of batching
- Omitting deep-link data, so the click does nothing
- Not archiving the inbox copy when the user engages via email or push

---

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

## Related

- [Push](./push.md), pair inbox with push so the message reaches users who aren't in the app
- [Multi-Channel](../guides/multi-channel.md), inbox in routing strategies
- [Batching](../guides/batching.md), aggregating events into one inbox message
- [Preferences](../guides/preferences.md), letting users turn inbox categories off
- [Elemental](../guides/elemental.md), content that renders in the inbox
