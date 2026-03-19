# In-App Inbox

## Quick Reference

### Rules
- MUST use JWT authentication (v8 requires JWT; v7 also accepted client keys but JWT is preferred)
- Generate JWT server-side using Courier API key — never expose API key to client
- JWT scopes needed: `user_id:{id} inbox:read:messages inbox:write:events read:preferences`
- Title: under 50 characters
- Body: under 150 characters
- Actions: 1-2 CTAs maximum
- Always include deep link data for navigation
- Batch similar notifications (don't send 10 separate "liked your post")
- No permission required — works for all users
- **Default to v8 SDK** for all new projects. Check the user's version before providing code.

### Version Detection

Before writing any Inbox code, determine the SDK version:

| Signal | Version |
|--------|---------|
| `@trycourier/courier-react` or `@trycourier/courier-react-17` in package.json | **v8** |
| `@trycourier/courier-ui-inbox` (Web Components) in package.json | **v8** |
| `<CourierInbox />`, `useCourier()`, `courier.shared.signIn()` | **v8** |
| `@trycourier/react-provider`, `@trycourier/react-inbox`, `@trycourier/react-toast` in package.json | **v7** |
| `<CourierProvider>`, `<Inbox />`, `useInbox()`, `clientKey` prop | **v7** |
| New project / no existing code | **Use v8** |

If the user is on v7, **do not use the v8 patterns in this file**. Instead, work with their existing v7 code and recommend upgrading. To help them migrate, fetch the migration guide: `https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide.md`

### Common Mistakes
- Not using JWT authentication (JWT is required in v8)
- Exposing Courier API key in client-side code
- Generating JWT client-side (must be server-side)
- Not calling `inbox.listenForUpdates()` after auth (required for real-time updates in v8)
- Sending individual notifications instead of batching
- Missing deep link data (user clicks, nothing happens)
- Not syncing read state across channels
- Forgetting to mark inbox as read when user engages via email
- Using v7 packages (`@trycourier/react-inbox`) in a new project instead of v8 (`@trycourier/courier-react`)

---

Best practices for building in-app notification centers using Courier Inbox.

## Why In-App Inbox?

- **Always available** — No permission required, works for all users
- **Persistent** — Users can return to read later
- **Rich content** — Full formatting, images, actions
- **Cross-device sync** — Read state persists across sessions
- **Low friction** — Complements push without notification fatigue

## Courier Inbox Components

Courier provides pre-built, customizable inbox components for:

- React (v8: `@trycourier/courier-react`)
- Web Components (v8: `@trycourier/courier-ui-inbox` — works with Vue, Angular, Svelte, vanilla JS)
- React Native (`@trycourier/courier-react-native`)
- iOS (Swift)
- Android (Kotlin)
- Flutter

---

## v8 React Integration (Recommended)

v8 is a single-package SDK with a smaller bundle, no third-party dependencies, built-in dark mode, and a modern default UI.

### Installation

```bash
# React 18+
npm install @trycourier/courier-react

# React 17
npm install @trycourier/courier-react-17
```

### Authentication

Courier uses three types of credentials in different contexts:

| Credential | Where used | Exposure |
|------------|-----------|----------|
| **API Key** | Server-side SDK, CLI, raw HTTP (`COURIER_API_KEY` env var) | Never expose to client |
| **Client Key** | Deprecated v7 setups only | Safe for client-side, limited scope |
| **JWT** | Inbox, Preferences, Toast components | Generated server-side, passed to client |

The API Key is the same key regardless of which env var you store it in. The SDK and CLI just look for different variable names by convention.

JWT is required for Inbox. Generate tokens server-side using your API key:

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

### JWT Refresh Strategy

JWTs expire based on `expires_in`. Build a refresh mechanism to avoid broken inbox connections:

```typescript
// Server-side endpoint
app.get("/api/courier-token", authenticate, async (req, res) => {
  const response = await fetch("https://api.courier.com/auth/issue-token", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.COURIER_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      scope: `user_id:${req.user.id} inbox:read:messages inbox:write:events read:preferences`,
      expires_in: "7 days",
    }),
  });
  const { token } = await response.json();
  res.json({ token });
});
```

```tsx
// Client-side: refresh before expiry
function useCourierToken(userId: string) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const fetchToken = () =>
      fetch("/api/courier-token")
        .then((r) => r.json())
        .then((d) => setToken(d.token));

    fetchToken();
    const interval = setInterval(fetchToken, 6 * 24 * 60 * 60 * 1000); // refresh 1 day before 7-day expiry
    return () => clearInterval(interval);
  }, [userId]);

  return token;
}
```

### Basic Setup (v8)

v8 uses `useCourier()` hook + `courier.shared.signIn()` — no provider wrapper needed:

```tsx
import { useEffect } from "react";
import { CourierInbox, useCourier } from "@trycourier/courier-react";

export default function App() {
  const courier = useCourier();

  useEffect(() => {
    fetch("/api/courier-token")
      .then((res) => res.json())
      .then((data) => {
        courier.shared.signIn({ userId: "user-123", jwt: data.token });
      });
  }, []);

  return <CourierInbox />;
}
```

### Popup Menu (v8)

```tsx
import { CourierInboxPopupMenu, useCourier } from "@trycourier/courier-react";

export default function App() {
  const courier = useCourier();

  useEffect(() => {
    courier.shared.signIn({ userId: "user-123", jwt: courierToken });
  }, [courierToken]);

  return <CourierInboxPopupMenu />;
}
```

### Feeds and Tabs (v8)

v8 introduces feeds and tabs for organizing messages into logical groups and filtered views:

```tsx
import { CourierInbox, type CourierInboxFeed } from "@trycourier/courier-react";

const feeds: CourierInboxFeed[] = [
  {
    feedId: "notifications",
    title: "Notifications",
    tabs: [
      { datasetId: "all", title: "All", filter: {} },
      { datasetId: "unread", title: "Unread", filter: { status: "unread" } },
      { datasetId: "important", title: "Important", filter: { tags: ["important"] } },
      { datasetId: "archived", title: "Archived", filter: { archived: true } },
    ],
  },
];

<CourierInbox feeds={feeds} />;
```

Filter options per tab:

| Filter Property | Type | Description |
|----------------|------|-------------|
| `tags` | `string[]` | Messages with any of the specified tags |
| `archived` | `boolean` | Include archived messages (defaults to `false`) |
| `status` | `'read' \| 'unread'` | Filter by read/unread status |

### Customized Inbox (v8)

v8 uses native theming via `lightTheme`/`darkTheme` props — no styled-components dependency:

```tsx
import { CourierInbox, type CourierInboxTheme } from "@trycourier/courier-react";

const theme: CourierInboxTheme = {
  inbox: {
    header: {
      filters: { unreadIndicator: { backgroundColor: "#9121C2" } },
    },
    list: {
      item: { unreadIndicatorColor: "#9121C2" },
    },
  },
};

<CourierInbox lightTheme={theme} darkTheme={theme} mode="light" />;
```

Dark mode switches automatically with `mode="system"`, or force with `mode="light"` / `mode="dark"`.

### Custom Components (v8)

Override individual parts with render props:

| Render Prop | Type Signature |
|-------------|----------------|
| `renderListItem` | `(props: CourierInboxListItemFactoryProps) => ReactNode` |
| `renderHeader` | `(props: CourierInboxHeaderFactoryProps) => ReactNode` |
| `renderMenuButton` | `(props: CourierInboxMenuButtonFactoryProps) => ReactNode` |
| `renderLoadingState` | `(props: CourierInboxStateLoadingFactoryProps) => ReactNode` |
| `renderEmptyState` | `(props: CourierInboxStateEmptyFactoryProps) => ReactNode` |
| `renderErrorState` | `(props: CourierInboxStateErrorFactoryProps) => ReactNode` |
| `renderPaginationItem` | `(props: CourierInboxPaginationItemFactoryProps) => ReactNode` |

```tsx
import { CourierInbox, type CourierInboxListItemFactoryProps } from "@trycourier/courier-react";

<CourierInbox
  renderListItem={({ message, index }: CourierInboxListItemFactoryProps) => (
    <div className="custom-message">
      <strong>{message.title}</strong>
      <p>{message.body}</p>
      <time>{message.created}</time>
    </div>
  )}
/>;
```

### Click Handlers (v8)

| Callback Prop | Type Signature |
|---------------|----------------|
| `onMessageClick` | `(props: CourierInboxListItemFactoryProps) => void` |
| `onMessageActionClick` | `(props: CourierInboxListItemActionFactoryProps) => void` |
| `onMessageLongPress` | `(props: CourierInboxListItemFactoryProps) => void` |

```tsx
<CourierInbox
  onMessageClick={({ message, index }) => {
    router.push(message.data?.deepLink);
  }}
  onMessageActionClick={({ message, action, index }) => {
    window.open(action.href);
  }}
/>
```

### Toast Notifications (v8)

Toasts are short-lived notifications connected to the Inbox message feed:

```tsx
import { CourierToast, useCourier } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();

  useEffect(() => {
    courier.shared.signIn({ userId: "user-123", jwt: courierToken });
  }, [courierToken]);

  return (
    <>
      <CourierToast
        autoDismiss={true}
        autoDismissTimeoutMs={5000}
        onToastItemClick={({ message }) => navigation.navigate(message.data.screen)}
      />
      {/* Your app */}
    </>
  );
}
```

Use `lightTheme` and `darkTheme` props for styling. Use `renderToastItem` or `renderToastItemContent` for fully custom rendering.

#### Toast Best Practices

- **Auto-dismiss for non-critical**: Background task completions, status updates
- **Persistent for actions**: Require user to acknowledge or take action
- **Combine with Inbox**: Toasts alert, inbox provides persistent access
- **Keep content brief**: Title under 50 chars, body under 100 chars

### useCourier Hook (v8)

For custom UIs and programmatic control:

```tsx
import { useEffect } from "react";
import { useCourier, type InboxMessage, defaultFeeds } from "@trycourier/courier-react";

export default function App() {
  const { auth, inbox } = useCourier();

  useEffect(() => {
    auth.signIn({
      userId: "user-123",
      jwt: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    });
    loadInbox();
  }, []);

  async function loadInbox() {
    inbox.registerFeeds(defaultFeeds());
    await inbox.listenForUpdates();
    await inbox.load();
  }

  const unreadCount = inbox.totalUnreadCount ?? 0;
  const messages = inbox.feeds["all_messages"]?.messages ?? [];

  return (
    <div>
      <div>Unread: {unreadCount}</div>
      <ul>
        {messages.map((msg: InboxMessage) => (
          <li key={msg.messageId} style={{
            backgroundColor: msg.read ? "transparent" : "#fee2e2",
          }}>
            {msg.title}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

You **must** call `inbox.listenForUpdates()` after authentication to enable real-time updates.

Key hook methods:

| Method | Description |
|--------|-------------|
| `inbox.registerFeeds(feeds)` | Register feeds and tabs with the datastore |
| `inbox.listenForUpdates()` | Start WebSocket connection for real-time updates |
| `inbox.load()` | Load messages (supports `{ canUseCache, datasetIds }`) |
| `inbox.readMessage(message)` | Mark as read |
| `inbox.unreadMessage(message)` | Mark as unread |
| `inbox.archiveMessage(message)` | Archive |
| `inbox.unarchiveMessage(message)` | Unarchive |
| `inbox.readAllMessages()` | Mark all as read |
| `inbox.fetchNextPageOfMessages({ datasetId })` | Fetch next page |

### Next.js / SSR (v8)

Courier components only render client-side. In Next.js 13+, add `'use client'`:

```tsx
"use client";

import { CourierInbox } from "@trycourier/courier-react";

export default function Page() {
  // Authentication code...
  return <CourierInbox />;
}
```

---

## v8 Web Components Integration

For non-React projects (Vue, Angular, Svelte, vanilla JS), use the Web Components SDK:

### Installation

```bash
npm install @trycourier/courier-ui-inbox @trycourier/courier-ui-toast
```

### Basic Setup

```html
<body>
  <courier-inbox id="inbox"></courier-inbox>

  <script type="module">
    import { Courier } from '@trycourier/courier-ui-inbox';

    Courier.shared.signIn({
      userId: 'user-123',
      jwt: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    });
  </script>
</body>
```

### Feeds, Theming, and Custom Elements

```html
<courier-inbox id="inbox"></courier-inbox>

<script type="module">
  import { Courier } from '@trycourier/courier-ui-inbox';

  const inbox = document.getElementById('inbox');

  inbox.setFeeds([
    {
      feedId: 'notifications',
      title: 'Notifications',
      tabs: [
        { datasetId: 'all', title: 'All', filter: {} },
        { datasetId: 'unread', title: 'Unread', filter: { status: 'unread' } }
      ]
    }
  ]);

  inbox.setLightTheme({
    inbox: {
      list: { item: { unreadIndicatorColor: "#9121C2" } }
    }
  });

  inbox.onMessageClick(({ message, index }) => {
    window.location.href = message.data?.deepLink;
  });

  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

---

## React Native Integration

### Installation

```bash
npm install @trycourier/courier-react-native
```

### Setup

```tsx
import { Courier, CourierInboxView } from "@trycourier/courier-react-native";

function App() {
  const courierToken = useCourierToken();

  useEffect(() => {
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

---

## Sending to Inbox

### Basic Inbox Message

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

await client.send.message({
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
    template: "ORDER_SHIPPED",
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

## Read State Management

### How It Works

- Courier tracks read/unread state per message
- State syncs across devices via WebSocket
- Badge count updates automatically

### Client-Side Read State (v8)

```typescript
import { useCourier } from "@trycourier/courier-react";

function NotificationBell() {
  const { inbox } = useCourier();

  const unreadCount = inbox.totalUnreadCount ?? 0;

  return (
    <button onClick={() => inbox.readAllMessages()}>
      🔔 {unreadCount > 0 && <Badge count={unreadCount} />}
    </button>
  );
}
```

### Server-Side State

```typescript
// Archive a message (removes from inbox)
await client.messages.archive(messageId);
```

Read state is managed client-side through the Inbox SDK. Use `messages.archive()` from the backend to remove messages from the inbox when the user engages via another channel.

## Real-Time Updates (v8)

Courier Inbox uses WebSocket for real-time updates. You **must** call `inbox.listenForUpdates()` after authentication:

```tsx
import { useCourier, CourierInbox, defaultFeeds } from "@trycourier/courier-react";

function App() {
  const { auth, inbox } = useCourier();

  useEffect(() => {
    auth.signIn({ userId: "user-123", jwt: courierToken });
    inbox.registerFeeds(defaultFeeds());
    inbox.listenForUpdates();
  }, [courierToken]);

  return <CourierInbox />;
}
```

## Customization

### Notification Categories

Organize notifications by type in data and use feeds/tabs to filter:

```typescript
// Include category in data for filtering
data: {
  category: "social", // or "orders", "account", etc.
  ...
}
```

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

  // Archive the inbox message since user engaged via email
  await client.messages.archive(messageId);
});
```

## Related

- [Push](./push.md) — Complement inbox with push notifications
- [Multi-Channel](../guides/multi-channel.md) — Inbox in routing strategies
- [Batching](../guides/batching.md) — Combining notifications
- [Throttling](../guides/throttling.md) — Controlling frequency
- [Engagement](../growth/engagement.md) — Activity notification patterns
- [Preferences](../guides/preferences.md) — User notification preferences
- [v8 Migration Guide](https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide) — Step-by-step upgrade from v7
