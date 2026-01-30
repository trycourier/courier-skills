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
- Using deprecated v7 packages (`@trycourier/react-provider`, `@trycourier/react-inbox`) instead of v8 (`@trycourier/courier-react`)
- Using deprecated clientKey instead of JWT authentication
- Exposing Courier API key in client-side code
- Generating JWT client-side (must be server-side)
- Not calling `inbox.startListening()` after auth (required for real-time updates in v8)
- Sending individual notifications instead of batching
- Missing deep link data (user clicks, nothing happens)
- Not syncing read state across channels
- Forgetting to mark inbox as read when user engages via email

### Templates

**Server-Side JWT Generation:**
```typescript
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

**React Setup (v8):**
```tsx
import { useCourier, CourierInbox } from "@trycourier/courier-react";

const courier = useCourier();
courier.shared.signIn({ userId: "user-123", jwt: courierToken });

return <CourierInbox />;
```

**Send to Inbox:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "NEW_COMMENT",
    routing: { method: "single", channels: ["inbox"] }
  }
});
```

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
  // Appearance - use lightTheme/darkTheme for v8
  lightTheme={{
    brand: {
      colors: {
        primary: "#9121C2"
      }
    }
  }}
  
  // Behavior
  onClickMessage={(message) => console.log('Message clicked', message)}
  onClickAction={(action, message) => console.log('Action clicked', action)}
  
  // Custom list item renderer
  renderListItem={(message) => (
    <CustomMessage message={message} />
  )}
/>
```

### Toast Notifications

Toasts are short-lived notifications that appear temporarily to alert users. They share the same message feed as Inbox - when a message arrives, it can trigger both a toast and appear in the inbox.

**When to use toasts:**
- Time-sensitive alerts that need immediate attention
- Confirmations of user actions
- Real-time updates (new message, status change)
- Complement inbox for users who aren't actively viewing notifications

#### Basic Setup

```tsx
import { useCourier, CourierToast } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();
  
  useEffect(() => {
    courier.shared.signIn({ userId: "user-123", jwt: courierToken });
  }, [courierToken]);

  return (
    <>
      <CourierToast position="top-right" />
      {/* Your app */}
    </>
  );
}
```

#### Auto-Dismiss Configuration

Use auto-dismiss for non-critical notifications. A countdown bar shows time remaining:

```tsx
<CourierToast
  position="top-right"
  autoClose={true}           // Enable auto-dismiss
  timeout={5000}             // Dismiss after 5 seconds
  hideProgressBar={false}    // Show countdown bar
/>
```

#### Click Handling

Handle clicks on toast items and action buttons:

```tsx
<CourierToast
  onClickItem={(event) => {
    // event.message contains the full message object
    console.log('Toast clicked:', event.message.title);
    navigation.navigate(event.message.data.screen);
  }}
  onClickAction={(event) => {
    // event.action contains the clicked action
    // event.message contains the parent message
    console.log('Action clicked:', event.action.content);
    handleAction(event.action.href);
  }}
/>
```

#### Toast Theming

Style toasts to match your app with `lightTheme` and `darkTheme`:

```tsx
<CourierToast
  lightTheme={{
    toast: {
      backgroundColor: "#FFFFFF",
      borderRadius: "8px",
      boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
    },
    title: {
      color: "#1A1A1A",
      fontWeight: "600"
    },
    body: {
      color: "#666666"
    },
    progressBar: {
      backgroundColor: "#9121C2"
    }
  }}
  darkTheme={{
    toast: {
      backgroundColor: "#2A2A2A",
      borderRadius: "8px"
    },
    title: {
      color: "#FFFFFF"
    },
    body: {
      color: "#AAAAAA"
    }
  }}
/>
```

#### Custom Toast Rendering

**Custom content only** (keeps dismiss button and auto-dismiss):

```tsx
<CourierToast
  renderItemContent={(props) => (
    <div className="custom-toast-content">
      <Avatar src={props.message.data.avatarUrl} />
      <div>
        <strong>{props.message.title}</strong>
        <p>{props.message.body}</p>
      </div>
    </div>
  )}
/>
```

**Fully custom toast items** (complete control):

```tsx
<CourierToast
  renderItem={(props) => (
    <div className="custom-toast" onClick={() => props.dismiss()}>
      <img src={props.message.icon} alt="" />
      <div>
        <h4>{props.message.title}</h4>
        <p>{props.message.body}</p>
      </div>
      <button onClick={(e) => { e.stopPropagation(); props.dismiss(); }}>
        ✕
      </button>
    </div>
  )}
/>
```

#### Handling Async Initialization

If toasts display immediately on page load, use `onReady` to ensure initialization is complete:

```tsx
function App() {
  const [toastReady, setToastReady] = useState(false);
  const courier = useCourier();

  useEffect(() => {
    if (toastReady) {
      courier.shared.signIn({ userId: "user-123", jwt: courierToken });
    }
  }, [toastReady, courierToken]);

  return <CourierToast onReady={() => setToastReady(true)} />;
}
```

#### Toast Best Practices

- **Auto-dismiss for non-critical**: Background task completions, status updates
- **Persistent for actions**: Require user to acknowledge or take action
- **Combine with Inbox**: Toasts alert, inbox provides persistent access
- **Keep content brief**: Title under 50 chars, body under 100 chars
- **Include actions sparingly**: 1-2 actions maximum per toast

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

Courier Inbox uses WebSocket for real-time updates. In v8, you must call `inbox.startListening()` after authentication to enable real-time functionality:

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

### Custom Message Renderer

```tsx
import { CourierInbox } from "@trycourier/courier-react";

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
/>
```

### Theming

In v8, use `lightTheme` and `darkTheme` props for automatic theme switching:

```tsx
import { CourierInbox } from "@trycourier/courier-react";

<CourierInbox
  lightTheme={{
    brand: {
      colors: {
        primary: "#9121C2",
        secondary: "#F5F5F5"
      }
    },
    message: {
      unread: {
        backgroundColor: "#F0E6F7"
      }
    },
    header: {
      fontFamily: "Inter, sans-serif"
    }
  }}
  darkTheme={{
    brand: {
      colors: {
        primary: "#B366D9",
        secondary: "#2A2A2A"
      }
    },
    message: {
      unread: {
        backgroundColor: "#3D2A47"
      }
    }
  }}
/>
```

## Best Practices

### Content Design

- **Title:** Clear, specific, actionable (under 50 chars)
- **Body:** Additional context, preview text (under 150 chars)
- **Actions:** 1-2 clear CTAs maximum
- **Data:** Include deep link info for navigation

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
