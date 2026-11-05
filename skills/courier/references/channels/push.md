# Push Notifications

**Contents:** [Quick Reference](#quick-reference) · [Android (FCM)](#android-fcm) · [Web Push](#web-push) · [Expo Push Notifications](#expo-push-notifications) · [Courier Integration](#courier-integration) · [Token Management](#token-management) · [Troubleshooting](#troubleshooting) · [Related](#related)

## Quick Reference

### Rules
- Aggregate similar notifications with a [batch node](../guides/batching.md) rather than app-side
- Register every device's token on the user with its `provider_key` and `device.platform`, and re-register when the OS rotates it
- A user with tokens on more than one provider (APNs and FCM) gets the push on only one of them, unless the send sets `channels: { push: { routing_method: "all" } }`

### Templates

**Register Push Token (TypeScript):**
```typescript
await client.users.tokens.addSingle("device-token-abc", {
  user_id: "user-123",
  provider_key: "apn", // or "firebase-fcm"
  device: {
    app_id: "com.acme.app",
    platform: "ios" // or "android"
  }
});
```

**Basic Push (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Your order shipped",
      body: "Arriving Thursday. Tap to track."
    },
    routing: {
      method: "single",
      channels: ["push"]
    }
  }
});
```

---

## Android (FCM)

With Apply Recommended Courier Mobile SDK Formatting on (the default), Courier sends FCM no `notification` block and moves title, body and image into `data`. See [Firebase FCM](https://www.courier.com/docs/integrations/push/firebase-fcm).

## Web Push

Web Push goes through the Firebase FCM provider. Register the browser's FCM token like an Android one, with `provider_key: "firebase-fcm"` and `device.platform: "web"`. It needs HTTPS and a service worker.

## Expo Push Notifications

For React Native apps on [Expo](https://docs.expo.dev/push-notifications/overview/), register the Expo push token with `provider_key: "expo"` and `device.platform: "expo"`. The Expo integration (**Integrations → Expo**) needs no credentials: Expo delivers through APNs and FCM with your Expo project's credentials.

## Courier Integration

### With Deep Link and Image

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "New comment on your photo",
      body: "Jane: Great shot! 📸"
    },
    channels: {
      push: {
        override: {
          data: {
            image: "https://acme.com/photos/12345.jpg",
            deepLink: "acme://photos/12345"
          }
        }
      }
    }
  }
});
```

### With Action Buttons

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Delivery arriving soon",
      body: "Your package will arrive in 30 minutes"
    },
    providers: {
      // The app registers the DELIVERY category and its buttons
      apn: { override: { body: { category: "DELIVERY" } } }
    }
  }
});
```

### Silent Push (Data Only)

```typescript
// iOS: no alert, and wake the app to sync. FCM already ships data-only by
// default (Apply Recommended Courier Mobile SDK Formatting).
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: { type: "sync", resource: "messages" },
    providers: {
      apn: { override: { silent: true, body: { "content-available": 1 } } },
    },
  },
});
```

## Token Management

### Multi-Device Support

Users may have multiple devices. Store all tokens:

```typescript
// Register one token per device, all on the same user
await client.users.tokens.addSingle("abc...", { user_id: "user-123", provider_key: "apn" });          // iPhone
await client.users.tokens.addSingle("xyz...", { user_id: "user-123", provider_key: "firebase-fcm" }); // Pixel
await client.users.tokens.addSingle("123...", { user_id: "user-123", provider_key: "firebase-fcm" }); // Samsung

// The push channel stops at the first provider that works, so without this
// the iPhone (APNs) and the Android phones (FCM) don't all get it.
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbvk2q5x9v1d4c7n8w6hj",
    routing: { method: "single", channels: ["push"] },
    channels: { push: { routing_method: "all" } },
  },
});
```

### Remove Invalid Tokens

`data.providers[].error` is the provider's own message as a **string**, and the webhook does not
name which token failed. The token's own `status` is the reliable signal, so read it and drop the
dead ones.

```typescript
// Handle feedback from APNs/FCM about invalid tokens
app.post('/webhooks/courier', async (req, res) => {
  const { type, data } = req.body;

  if (type === 'message:updated' && data.status === 'UNDELIVERABLE') {
    const { tokens } = await client.users.tokens.list(data.recipient);
    for (const { token } of tokens ?? []) {
      // The SDK types status (and status_reason, the cause) only on the single-token read
      const { status } = await client.users.tokens.retrieve(token, { user_id: data.recipient });
      if (status === 'failed' || status === 'revoked') {
        await client.users.tokens.delete(token, { user_id: data.recipient });
      }
    }
  }

  res.sendStatus(200);
});
```

Token `status` is one of `active`, `unknown`, `failed`, `revoked`, with a free-text
`status_reason`. Delete on `failed` or `revoked`; leave `unknown` alone.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| APNs devices get it, FCM devices don't (or the reverse) | Push tries providers as `single` by default and stops at the first that delivers | See [Multi-Device Support](#multi-device-support) |
| OneSignal send fails for some users | No OneSignal ID on the profile, or the payload is over OneSignal's size cap. A `400` for a user whose other sends succeed points to their state in OneSignal at send time (no subscribed device for that ID), so check the user in OneSignal before the payload | Store `oneSignalExternalUserId` (or `oneSignalPlayerID`) on the profile and use data mapping. See [OneSignal](https://www.courier.com/docs/integrations/push/onesignal-push) |
| AWS SNS shows up under SMS | One AWS SNS integration serves both SMS and push | Pick it as a provider on either channel. Its Topic ARN applies to push only |

## Related

- [Inbox](./inbox.md) - In-app notification center as push complement
- [Multi-Channel](../guides/multi-channel.md) - Push in escalation chains
- [Batching](../guides/batching.md) - Notification batching strategies
- [Throttling](../guides/throttling.md) - Push frequency limits
- [Engagement](../lifecycle-marketing.md) - Activity notification patterns
