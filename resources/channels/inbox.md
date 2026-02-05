# In-App Inbox

## Quick Reference

### Rules
- MUST use JWT authentication (clientKey is deprecated)
- Generate JWT server-side using Courier API key - never expose API key to client
- JWT scopes needed: `user_id:{id} inbox:read:messages inbox:write:events read:preferences`
- Title: under 50 characters
- Body: under 150 characters
- Actions: 1-2 CTAs maximum
- Always include deep link data for navigation
- Batch similar notifications (don't send 10 separate "liked your post")
- No permission required - works for all users

### Common Mistakes
- Using deprecated clientKey instead of JWT authentication
- Exposing Courier API key in client-side code
- Generating JWT client-side (must be server-side)
- Not calling `inbox.startListening()` after auth (required for real-time updates)
- Sending individual notifications instead of batching
- Missing deep link data (user clicks, nothing happens)
- Not syncing read state across channels
- Forgetting to mark inbox as read when user engages via email

---

Best practices for building in-app notification centers using Courier Inbox.

## Why In-App Inbox?

- **Always available** - No permission required, works for all users
- **Persistent** - Users can return to read later
- **Rich content** - Full formatting, images, actions
- **Cross-device sync** - Read state persists across sessions
- **Low friction** - Complements push without notification fatigue

## Courier Inbox Components

Courier provides pre-built, customizable inbox components for:

- React
- React Native
- iOS (Swift)
- Android (Kotlin)
- Flutter
- JavaScript (vanilla)

## React Integration

### Installation

```bash
npm install @trycourier/courier-react
```

### Authentication

Courier Inbox uses JWT (JSON Web Token) authentication. Generate tokens server-side using your API key:

```typescript
// Server-side: Generate JWT for user
const response = await fetch('https://api.courier.com/auth/issue-token', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.COURIER_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    scope: 'user_id:user-123 inbox:read:messages inbox:write:events read:preferences',
    expires_in: '7 days'
  })
});
const { token } = await response.json();
```

### Basic Setup

```tsx
import { useCourier, CourierInbox } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();
  // Get JWT from your backend (see authentication section above)
  const [courierToken, setCourierToken] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/courier-token')
      .then(res => res.json())
      .then(data => setCourierToken(data.token));
  }, []);

  useEffect(() => {
    if (courierToken) {
      // Authenticate the user with Courier
      courier.shared.signIn({ userId: "user-123", jwt: courierToken });
    }
  }, [courierToken]);

  if (!courierToken) return null;

  return <CourierInbox />;
}
```

### Customized Inbox

```tsx
import { CourierInbox } from "@trycourier/courier-react";

<CourierInbox
  lightTheme={{ brand: { colors: { primary: "#9121C2" } } }}
  onClickMessage={(message) => console.log('Message clicked', message)}
  onClickAction={(action, message) => console.log('Action clicked', action)}
  renderListItem={(message) => <CustomMessage message={message} />}
/>
```

### Toast Notifications

Toasts are short-lived notifications that appear temporarily. They share the same message feed as Inbox.

**When to use:** Time-sensitive alerts, action confirmations, real-time updates.

```tsx
import { useCourier, CourierToast } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();
  
  useEffect(() => {
    courier.shared.signIn({ userId: "user-123", jwt: courierToken });
  }, [courierToken]);

  return (
    <>
      <CourierToast
        position="top-right"
        autoClose={true}
        timeout={5000}
        hideProgressBar={false}
        onClickItem={(event) => navigation.navigate(event.message.data.screen)}
        onClickAction={(event) => handleAction(event.action.href)}
      />
      {/* Your app */}
    </>
  );
}
```

Use `lightTheme` and `darkTheme` props for styling. Use `renderItem` for fully custom rendering.

#### Toast Best Practices

- **Auto-dismiss for non-critical**: Background task completions, status updates
- **Persistent for actions**: Require user to acknowledge or take action
- **Combine with Inbox**: Toasts alert, inbox provides persistent access
- **Keep content brief**: Title under 50 chars, body under 100 chars

## React Native Integration

### Installation

```bash
npm install @trycourier/courier-react-native
```

### Setup

```tsx
import { Courier, CourierInboxView } from "@trycourier/courier-react-native";

function App() {
  // Get JWT from your backend (see React authentication section)
  const courierToken = useCourierToken(); // Your custom hook
  
  useEffect(() => {
    // Authenticate the user
    Courier.shared.signIn({
      accessToken: courierToken,
      userId: "user-123",
    });
  }, [courierToken]);

  return (
    <CourierInboxView 
      onClickMessageAtIndex={(message, index) => {
        navigation.navigate(message.data.screen);
      }}
    />
  );
}
```

## Sending to Inbox

### Basic Inbox Message

```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "NEW_COMMENT",
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
await courier.send({
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
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_SHIPPED",
    data: {
      orderNumber: "12345",
      trackingUrl: "https://acme.co/track/12345"
    },
    routing: {
      method: "all", // Send to all channels
      channels: ["inbox", "push"]
    }
  }
});
```

## Read State Management

### How It Works

- Courier tracks read/unread state per message
- State syncs across devices via WebSocket
- Badge count updates automatically

### Client-Side Read State

```typescript
// React hook
import { useCourier } from "@trycourier/courier-react";

function NotificationBell() {
  const { inbox } = useCourier();
  
  // Access unread count from datasets
  const unreadCount = inbox.datasets?.default?.unreadCount ?? 0;
  
  return (
    <button onClick={() => inbox.markAllAsRead()}>
      🔔 {unreadCount > 0 && <Badge count={unreadCount} />}
    </button>
  );
}
```

### Server-Side Read State

```typescript
// Mark message as read
await courier.messages.read(messageId);

// Mark all as read for user
await courier.messages.readAll(userId);
```

## Real-Time Updates

Courier Inbox uses WebSocket for real-time updates. You must call `inbox.startListening()` after authentication to enable real-time functionality:

```tsx
import { useCourier, CourierInbox } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();
  const { inbox } = courier;

  useEffect(() => {
    if (courierToken) {
      courier.shared.signIn({ userId: "user-123", jwt: courierToken });
      // Start listening for real-time updates
      inbox.startListening();
    }
  }, [courierToken]);

  return <CourierInbox />;
}
```

## Message Lifecycle

### Archive/Delete

```typescript
// Archive (hide from inbox but keep)
await courier.messages.archive(messageId);

// Delete permanently
await courier.messages.delete(messageId);
```

### Click Tracking

```typescript
// Track when user clicks a message
await courier.messages.track(messageId, 'clicked');
```

## Customization

Use `renderListItem` for custom message rendering and `lightTheme`/`darkTheme` for theming:

```tsx
<CourierInbox
  renderListItem={(message) => (
    <div className="custom-message">
      <Avatar src={message.data.avatarUrl} />
      <div>
        <strong>{message.title}</strong>
        <p>{message.body}</p>
        <time>{formatDate(message.created)}</time>
      </div>
    </div>
  )}
  lightTheme={{
    brand: { colors: { primary: "#9121C2" } },
    message: { unread: { backgroundColor: "#F0E6F7" } }
  }}
/>
```

## Best Practices

### Notification Categories

Organize notifications by type:

```typescript
// Include category in data for filtering
data: {
  category: "social", // or "orders", "account", etc.
  ...
}
```

Enable client-side filtering with tabs:

```tsx
import { CourierInbox } from "@trycourier/courier-react";

<CourierInbox
  tabs={[
    { label: "All", filter: {} },
    { label: "Social", filter: { tags: ["social"] } },
    { label: "Orders", filter: { tags: ["orders"] } },
    { label: "Unread", filter: { isRead: false } }
  ]}
/>
```

### Batching and Digests

Don't send individual notifications for each event:

```typescript
// Instead of 10 separate notifications:
// "Jane liked your post"
// "Bob liked your post"
// ...

// Send one batched notification:
await courier.send({
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
  
  // Mark corresponding inbox message as read
  await courier.messages.read(messageId);
});
```

## Related

- [Push](./push.md) - Complement inbox with push notifications
- [Multi-Channel](../guides/multi-channel.md) - Inbox in routing strategies
- [Batching](../guides/batching.md) - Combining notifications
- [Throttling](../guides/throttling.md) - Controlling frequency
- [Engagement](../growth/engagement.md) - Activity notification patterns
- [Preferences](../guides/preferences.md) - User notification preferences
