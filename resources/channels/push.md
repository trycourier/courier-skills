# Push Notifications

## Quick Reference

### Rules
- iOS: Permission prompt shown ONCE per app install - don't waste it
- Android 13+: Requires explicit permission (like iOS)
- Android 12 and below: Opt-out model (enabled by default)
- Title: under 50 characters
- Body: under 100 characters
- Always include deep link for navigation
- Respect quiet hours (10pm-8am local time) for non-urgent
- Batch similar notifications ("3 new messages" not 3 separate)
- Push tokens can change - always handle token refresh
- Store tokens with device/platform info for proper routing

### Common Mistakes
- Requesting iOS permission immediately on first launch (low opt-in)
- Not using pre-permission prompt to explain value first
- Sending vague titles like "New notification"
- Not handling token refresh (leads to invalid tokens)
- Storing duplicate tokens for same device
- Over-notifying (users will disable notifications)
- Ignoring quiet hours for non-urgent notifications
- Missing deep links (user taps and nothing happens)
- Not creating Android notification channels (users can't control categories)

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

**Register Push Token (Python):**
```python
client.users.tokens.add_single("device-token-abc",
    user_id="user-123",
    provider_key="apn",  # or "firebase-fcm"
    device={"app_id": "com.acme.app", "platform": "ios"},  # or "android"
)
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

**Basic Push (Python):**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "content": {
            "title": "Your order shipped",
            "body": "Arriving Thursday. Tap to track.",
        },
        "routing": {"method": "single", "channels": ["push"]},
    }
)
```

**With Deep Link:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    channels: {
      push: {
        override: {
          data: {
            deepLink: "acme://orders/12345"
          }
        }
      }
    }
  }
});
```

---

Best practices for sending push notifications that users actually want.

## Platform Overview

| Platform | Service | Permission Model | Rich Media |
|----------|---------|-----------------|------------|
| iOS | APNs (Apple Push Notification service) | Opt-in required | Images, video, custom UI |
| Android | FCM (Firebase Cloud Messaging) | Opt-out (pre-13), Opt-in (13+) | Images, actions, styles |
| Web | Web Push (VAPID) | Opt-in required | Limited images, actions |

## iOS (APNs)

### Permission Model

- **One-time prompt:** Users only see system prompt once per app install
- **If denied:** Must manually enable in Settings (rare)
- **Provisional:** Quiet delivery without prompting (iOS 12+)

### Notification Types

| Type | Visibility | Use Case |
|------|------------|----------|
| Alert | Banner, sound, badge | User-facing notifications |
| Silent | Background only | Data sync, content refresh |
| Provisional | Notification Center only | Build trust before full permission |

### APNs Payload

```json
{
  "aps": {
    "alert": {
      "title": "Your order shipped",
      "body": "Arriving Thursday. Tap to track.",
      "subtitle": "Order #12345"
    },
    "badge": 1,
    "sound": "default",
    "mutable-content": 1,
    "category": "ORDER_UPDATE"
  },
  "data": {
    "orderId": "12345",
    "deepLink": "acme://orders/12345"
  }
}
```

## Android (FCM)

### Permission Model

- **Android 12 and below:** Opt-out (notifications enabled by default)
- **Android 13+:** Opt-in required (like iOS)
- **Notification Channels:** Users can control categories independently

### Notification Channels

```kotlin
// Create channels in your Android app
val orderChannel = NotificationChannel(
    "orders",
    "Order Updates",
    NotificationManager.IMPORTANCE_HIGH
).apply {
    description = "Shipping and delivery notifications"
}

val socialChannel = NotificationChannel(
    "social",
    "Social Activity",
    NotificationManager.IMPORTANCE_DEFAULT
).apply {
    description = "Comments, likes, and mentions"
}

notificationManager.createNotificationChannels(listOf(orderChannel, socialChannel))
```

### FCM Payload

```json
{
  "notification": {
    "title": "Your order shipped",
    "body": "Arriving Thursday. Tap to track.",
    "image": "https://acme.com/images/package.png",
    "click_action": "OPEN_ORDER"
  },
  "data": {
    "orderId": "12345",
    "type": "shipping"
  },
  "android": {
    "notification": {
      "channel_id": "orders",
      "priority": "high"
    }
  }
}
```

## Web Push

Web Push uses the Firebase Cloud Messaging (FCM) provider in Courier. Register the token the same way as Android:

```typescript
// After obtaining FCM token in the browser via Firebase SDK
await client.users.tokens.addSingle(fcmToken, {
  user_id: userId,
  provider_key: "firebase-fcm",
  device: {
    app_id: "com.acme.web",
    platform: "web",
  },
});
```

Web Push requires HTTPS and a service worker. Configure FCM credentials in the Courier dashboard under **Channels > Push > Firebase Cloud Messaging**.

## Expo Push Notifications

For React Native apps using [Expo](https://docs.expo.dev/push-notifications/overview/), register the Expo push token:

```typescript
await client.users.tokens.addSingle(expoPushToken, {
  user_id: userId,
  provider_key: "expo",
  device: {
    app_id: "com.acme.app",
    platform: "expo",
  },
});
```

Configure your Expo access token in the Courier dashboard under **Channels > Push > Expo**. Courier handles the translation from Expo tokens to APNs/FCM delivery.

## Permission Priming

### The Problem

iOS gives you **one chance**. Don't waste it.

| Approach | Opt-in Rate |
|----------|-------------|
| Immediate prompt on launch | 30-40% |
| Pre-permission screen | 50-60% |
| Contextual prompt after value | 60-70%+ |

### Pre-Permission Strategy

```
┌─────────────────────────────────────┐
│                                     │
│      🔔 Stay in the Loop            │
│                                     │
│   Get notified when:                │
│   ✓ Your order ships                │
│   ✓ Someone replies to you          │
│   ✓ Important account updates       │
│                                     │
│   [ Enable Notifications ]          │
│                                     │
│        Maybe Later                  │
│                                     │
└─────────────────────────────────────┘
```

**If user taps "Enable"** → Show system prompt
**If user taps "Maybe Later"** → Ask again after they experience value

### Best Timing

| Good | Bad |
|------|-----|
| After first purchase | Immediately on first launch |
| After account setup | Before they understand your app |
| When they enable a feature that needs it | Random prompt mid-flow |
| After they've used the app for a week | During checkout |

### Provisional Notifications (iOS)

Request provisional authorization for quiet delivery:

```swift
UNUserNotificationCenter.current().requestAuthorization(
    options: [.provisional, .alert, .sound, .badge]
) { granted, error in
    // Notifications delivered quietly to Notification Center
    // User can "Keep" or "Turn Off" from the notification
}
```

## Courier Integration

### Register Device Token

```typescript
// When your app receives a push token
async function registerPushToken(userId: string, token: string, platform: 'ios' | 'android' | 'web') {
  const providerMap = {
    ios: 'apn',
    android: 'firebase-fcm',
    web: 'firebase-fcm',  // Web Push via FCM
  } as const;

  await client.users.tokens.addSingle(token, {
    user_id: userId,
    provider_key: providerMap[platform],
    device: {
      app_id: 'com.acme.app',
      platform: platform
    }
  });
}
```

### Send Push Notification

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

// Basic push
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

### With Deep Link

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: {
      orderId: "12345",
      deliveryDate: "Thursday"
    },
    channels: {
      push: {
        override: {
          data: {
            deepLink: "acme://orders/12345"
          }
        }
      }
    }
  }
});
```

### With Image (Rich Push)

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
    channels: {
      push: {
        override: {
          data: {
            category: "DELIVERY", // Maps to registered category in app
            actions: [
              { id: "track", title: "Track" },
              { id: "delay", title: "Delay 1 Hour" }
            ]
          }
        }
      }
    }
  }
});
```

### Silent Push (Data Only)

```typescript
// Update app data without showing notification
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    channels: {
      push: {
        override: {
          data: {
            type: "sync",
            resource: "messages",
            silent: true
          },
          notification: null // No visible notification
        }
      }
    }
  }
});
```

## Token Management

### Lifecycle

```
App Launch → Check Token → Compare with Stored → Update if Changed
              ↓
Token Changes (OS update, reinstall, etc.)
              ↓
Update Courier Profile
```

### Handle Token Refresh

```typescript
// iOS - AppDelegate
func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
    sendTokenToBackend(token, platform: "ios")
}

// Android - FirebaseMessagingService
override fun onNewToken(token: String) {
    sendTokenToBackend(token, platform: "android")
}
```

### Multi-Device Support

Users may have multiple devices. Store all tokens:

```typescript
// User profile with multiple tokens
{
  user_id: "user-123",
  tokens: [
    { token: "abc...", provider: "apn", device: "iPhone" },
    { token: "xyz...", provider: "firebase-fcm", device: "Pixel" },
    { token: "123...", provider: "firebase-fcm", device: "Samsung" }
  ]
}

// Courier sends to all registered tokens
await client.send.message({
  message: {
    to: { user_id: "user-123" }, // All devices receive
    template: "nt_01kmrbvk2q5x9v1d4c7n8w6hj"
  }
});
```

### Remove Invalid Tokens

```typescript
// Handle feedback from APNs/FCM about invalid tokens
app.post('/webhooks/courier', async (req, res) => {
  const { event, error, recipient } = req.body;
  
  if (event === 'undelivered' && error?.code === 'token_expired') {
    await client.users.tokens.delete(error.token, { user_id: recipient.user_id });
  }
  
  res.sendStatus(200);
});
```

## Notification Design

### Content Guidelines

| Element | iOS Limit | Android Limit | Best Practice |
|---------|-----------|---------------|---------------|
| Title | 50 chars | 50 chars | Be specific, actionable |
| Body | 150 chars | 150 chars | Front-load important info |
| Image | 1024x1024 max | 1:1 or 2:1 ratio | Add value, not decoration |

### Examples

**Good:**
```
Title: Jane commented on your post
Body: "Great point about the API design!"
```

```
Title: Your order shipped
Body: Arriving Thursday. Tap to track.
```

```
Title: Security alert
Body: New login from Chrome on Windows
```

**Bad:**
```
Title: New notification
Body: Something happened in the app
```

```
Title: Hey there!
Body: We have some exciting news for you that we think you might like...
```

## Frequency & Timing

### Don't Over-Notify

| Type | Max Frequency |
|------|---------------|
| Activity (likes, comments) | Batch after 5min, max 10/hour |
| Transactional | As needed (but consider batching) |
| Marketing | 2-3 per week maximum |

### Quiet Hours

Don't send non-urgent push between 10 PM - 8 AM local time. See [Patterns > Quiet Hours](../guides/patterns.md#quiet-hours) for the implementation.

### Batching

```typescript
// Instead of 5 separate notifications:
// "Jane liked your post"
// "Bob liked your post"
// "Mike liked your post"
// "Sarah liked your post"
// "Tom liked your post"

// Send one batched notification:
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Your post is popular!",
      body: "Jane, Bob, and 3 others liked your post"
    }
  }
});
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Not delivered | Invalid/expired token | Re-register token on app launch |
| Delayed | Low priority | Use high priority for time-sensitive |
| Not shown (iOS) | User disabled | Check permission status, re-request |
| Not shown (Android) | Channel disabled | Guide user to notification settings |
| Duplicates | Multiple token registrations | Dedupe tokens by device ID |
| No sound | Silent mode or channel settings | Respect user preference |

### Debug Checklist

1. Token registered correctly in Courier?
2. User has push permission enabled?
3. App in foreground? (may need handling)
4. Device connected to internet?
5. APNs/FCM credentials configured correctly?
6. Payload format valid?

## Related

- [Inbox](./inbox.md) - In-app notification center as push complement
- [Multi-Channel](../guides/multi-channel.md) - Push in escalation chains
- [Batching](../guides/batching.md) - Notification batching strategies
- [Throttling](../guides/throttling.md) - Push frequency limits
- [Engagement](../growth/engagement.md) - Activity notification patterns
