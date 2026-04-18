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
- **ALWAYS use v8 SDK** for new projects — v7 is legacy and should not be used for new integrations
- If the user is on v7, guide them to upgrade to v8; do not write new v7 code

### Version Detection

This file documents **v8, the current version**. Write v8 code for all new integrations.

Quick v7 vs v8 sniff: if the codebase imports `@trycourier/courier-react` or uses `<CourierInbox />` / `useCourier()`, it's v8 — continue with this file. If it imports `@trycourier/react-provider` / `@trycourier/react-inbox` / `@trycourier/react-toast` or uses `<CourierProvider>` / `<Inbox />` / a `clientKey` prop, it's **v7 (legacy)** — see [inbox-v7-legacy.md](./inbox-v7-legacy.md) for recognition patterns and migration guidance before touching the code.

**Do not write new v7 code.** If the existing project is on v7, propose migration to v8 before adding features. The v7 file exists only to help maintain existing code and guide upgrades.

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
- React Native (`@trycourier/courier-react-native`) — see [React Native Integration](#react-native-integration) below
- iOS (Swift) — see the [Courier iOS SDK docs](https://www.courier.com/docs/sdk-libraries/ios)
- Android (Kotlin) — see the [Courier Android SDK docs](https://www.courier.com/docs/sdk-libraries/android)
- Flutter — see the [Courier Flutter SDK docs](https://www.courier.com/docs/sdk-libraries/flutter)

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

JWT is required for Inbox. Generate tokens server-side using your API key. The SDKs expose the issue-token endpoint directly — prefer that over raw HTTP.

**TypeScript (`@trycourier/courier`):**

```typescript
import Courier from "@trycourier/courier";
const client = new Courier(); // reads COURIER_API_KEY

const { token } = await client.auth.issueToken({
  scope: "user_id:user-123 inbox:read:messages inbox:write:events read:preferences",
  expires_in: "7 days",
});
```

**Python (`trycourier`):**

```python
from courier import Courier
client = Courier()  # reads COURIER_API_KEY

resp = client.auth.issue_token(
    scope="user_id:user-123 inbox:read:messages inbox:write:events read:preferences",
    expires_in="7 days",
)
token = resp.token
```

**Raw HTTP** (for languages without a Courier SDK):

```bash
curl -X POST https://api.courier.com/auth/issue-token \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scope":"user_id:user-123 inbox:read:messages inbox:write:events read:preferences","expires_in":"7 days"}'
```

### JWT Refresh Strategy

JWTs expire based on `expires_in`. Build a refresh mechanism to avoid broken inbox connections:

```typescript
import Courier from "@trycourier/courier";
const courier = new Courier();

app.get("/api/courier-token", authenticate, async (req, res) => {
  const { token } = await courier.auth.issueToken({
    scope: `user_id:${req.user.id} inbox:read:messages inbox:write:events read:preferences`,
    expires_in: "7 days",
  });
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
import { useEffect } from "react";
import { CourierInboxPopupMenu, useCourier } from "@trycourier/courier-react";
// See the "JWT Refresh Strategy" section above for useCourierToken.

export default function App() {
  const courier = useCourier();
  const courierToken = useCourierToken("user-123");

  useEffect(() => {
    if (!courierToken) return;
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
import { useEffect } from "react";
import { CourierToast, useCourier } from "@trycourier/courier-react";
// useCourierToken defined earlier in the "JWT Refresh Strategy" section — fetches a
// short-lived JWT from your backend and refreshes before expiry.

function App() {
  const courier = useCourier();
  const courierToken = useCourierToken("user-123");

  useEffect(() => {
    if (!courierToken) return;
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
  const { shared, inbox } = useCourier();

  useEffect(() => {
    shared.signIn({
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

## v8 Web Components / Vanilla JS Integration

Web Components work with **any framework or no framework at all** — Vue, Angular, Svelte, vanilla JS, server-rendered HTML, WordPress, etc. They use the same v8 SDK and real-time infrastructure as the React components.

### Installation

**With a bundler (npm):**

```bash
npm install @trycourier/courier-ui-inbox @trycourier/courier-ui-toast
```

**Without a bundler (CDN script tag):**

```html
<script type="module" src="https://unpkg.com/@trycourier/courier-ui-inbox@latest/dist/courier-ui-inbox/courier-ui-inbox.esm.js"></script>
<script type="module" src="https://unpkg.com/@trycourier/courier-ui-toast@latest/dist/courier-ui-toast/courier-ui-toast.esm.js"></script>
```

The CDN approach requires no build step — add the script tags and use the custom elements immediately.

### Basic Setup

**With npm / bundler:**

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

**With CDN (no build step):**

```html
<!DOCTYPE html>
<html>
<head>
  <script type="module" src="https://unpkg.com/@trycourier/courier-ui-inbox@latest/dist/courier-ui-inbox/courier-ui-inbox.esm.js"></script>
</head>
<body>
  <courier-inbox id="inbox"></courier-inbox>

  <script type="module">
    const { Courier } = await import('https://unpkg.com/@trycourier/courier-ui-inbox@latest/dist/courier-ui-inbox/courier-ui-inbox.esm.js');

    const jwt = await fetch('/api/courier-token')
      .then(r => r.json())
      .then(d => d.token);

    Courier.shared.signIn({ userId: 'user-123', jwt });
  </script>
</body>
</html>
```

### Popup Menu

```html
<courier-inbox-popup-menu></courier-inbox-popup-menu>

<script type="module">
  import { Courier } from '@trycourier/courier-ui-inbox';
  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

### Toast Notifications

```html
<courier-toast auto-dismiss="true" auto-dismiss-timeout-ms="5000"></courier-toast>

<script type="module">
  import { Courier } from '@trycourier/courier-ui-toast';

  const toast = document.querySelector('courier-toast');

  toast.onToastItemClick(({ message }) => {
    window.location.href = message.data?.deepLink;
  });

  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

### Feeds, Tabs, and Theming

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

  inbox.setDarkTheme({
    inbox: {
      list: { item: { unreadIndicatorColor: "#bb86fc" } }
    }
  });

  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

### Event Handling

All the same callbacks available in React are available on the Web Component elements:

```html
<courier-inbox id="inbox"></courier-inbox>

<script type="module">
  import { Courier } from '@trycourier/courier-ui-inbox';

  const inbox = document.getElementById('inbox');

  inbox.onMessageClick(({ message, index }) => {
    window.location.href = message.data?.deepLink;
  });

  inbox.onMessageActionClick(({ message, action, index }) => {
    window.open(action.href);
  });

  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

### Unread Badge (Vanilla JS)

Build a custom notification bell with unread count without any framework:

```html
<button id="notif-bell">
  🔔 <span id="badge" style="display:none;"></span>
</button>
<courier-inbox id="inbox" style="display:none;"></courier-inbox>

<script type="module">
  import { Courier } from '@trycourier/courier-ui-inbox';

  const inbox = document.getElementById('inbox');
  const badge = document.getElementById('badge');
  const bell = document.getElementById('notif-bell');

  // Toggle inbox visibility
  bell.addEventListener('click', () => {
    inbox.style.display = inbox.style.display === 'none' ? 'block' : 'none';
  });

  // Poll for unread count updates
  function updateBadge() {
    const count = inbox.unreadMessageCount ?? 0;
    badge.textContent = count > 99 ? '99+' : count;
    badge.style.display = count > 0 ? 'inline' : 'none';
  }

  // Check periodically (WebSocket handles real-time, this catches edge cases)
  setInterval(updateBadge, 2000);

  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

### Web Components API Reference

| Element | Description |
|---------|-------------|
| `<courier-inbox>` | Full inbox list with feeds, tabs, and theming |
| `<courier-inbox-popup-menu>` | Bell icon with dropdown popup |
| `<courier-toast>` | Toast notification overlay |

| Method / Property | Available On | Description |
|-------------------|-------------|-------------|
| `setFeeds(feeds)` | `courier-inbox` | Configure feeds and tabs |
| `setLightTheme(theme)` | `courier-inbox`, `courier-toast` | Set light mode theme |
| `setDarkTheme(theme)` | `courier-inbox`, `courier-toast` | Set dark mode theme |
| `onMessageClick(cb)` | `courier-inbox` | Handle message click |
| `onMessageActionClick(cb)` | `courier-inbox` | Handle action button click |
| `onToastItemClick(cb)` | `courier-toast` | Handle toast click |
| `unreadMessageCount` | `courier-inbox` | Current unread count (read-only) |

---

## React Native Integration

### Installation

```bash
npm install @trycourier/courier-react-native
```

### Setup

```tsx
import { useEffect, useState } from "react";
import { useNavigation } from "@react-navigation/native";
import { Courier, CourierInboxView } from "@trycourier/courier-react-native";

// Fetches a short-lived Courier JWT from your backend. The React Native
// signIn API uses the parameter name `accessToken` (it's the same JWT as
// the web `jwt` field — just named differently in the RN SDK).
function useCourierToken(userId: string): string | null {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    fetch("https://api.example.com/courier-token")
      .then((r) => r.json())
      .then((d) => setToken(d.token));
  }, [userId]);

  return token;
}

function App() {
  const navigation = useNavigation();
  const courierToken = useCourierToken("user-123");

  useEffect(() => {
    if (!courierToken) return;
    Courier.shared.signIn({
      accessToken: courierToken,
      userId: "user-123",
    });
  }, [courierToken]);

  return (
    <CourierInboxView
      onClickMessageAtIndex={(message, _index) => {
        if (message.data?.screen) navigation.navigate(message.data.screen);
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

## Read State Management

### How It Works

- Courier tracks read/unread state per message
- State syncs across devices via WebSocket
- Badge count updates automatically

### Client-Side Read State (v8)

```tsx
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

The Node SDK's `client.messages` resource exposes `retrieve`, `list`, `cancel`, `content`, and `history` — there is **no `archive` method**. To archive an inbox message from the server, call the REST endpoint directly using the same API key:

```typescript
await fetch(`https://api.courier.com/messages/${messageId}/archive`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.COURIER_API_KEY}`,
  },
});
```

Read state is managed client-side through the Inbox SDK. Use the REST archive endpoint from the backend to remove messages from the inbox when the user engages via another channel.

## Real-Time Updates (v8)

Courier Inbox uses WebSocket for real-time updates. You **must** call `inbox.listenForUpdates()` after authentication:

```tsx
import { useEffect } from "react";
import { useCourier, CourierInbox, defaultFeeds } from "@trycourier/courier-react";
// See the "JWT Refresh Strategy" section above for useCourierToken.

function App() {
  const { shared, inbox } = useCourier();
  const courierToken = useCourierToken("user-123");

  useEffect(() => {
    if (!courierToken) return;
    shared.signIn({ userId: "user-123", jwt: courierToken });
    inbox.registerFeeds(defaultFeeds());
    inbox.listenForUpdates();
  }, [courierToken, shared, inbox]);

  return <CourierInbox />;
}
```

## Customization

### Notification Categories

Organize notifications by type in data and use feeds/tabs to filter:

```jsonc
// Include `category` in message.data so feeds/tabs can filter on it.
{
  "category": "social", // or "orders", "account", etc.
  "actorId": "user-42",
  "targetId": "post-7"
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

  // Archive the inbox message since user engaged via email.
  // The Node SDK does not expose archive — call the REST endpoint directly.
  await fetch(`https://api.courier.com/messages/${messageId}/archive`, {
    method: "POST",
    headers: { Authorization: `Bearer ${process.env.COURIER_API_KEY}` },
  });
});
```

## Related

- [Push](./push.md) — Complement inbox with push notifications
- [Multi-Channel](../guides/multi-channel.md) — Inbox in routing strategies
- [Batching](../guides/batching.md) — Combining notifications
- [Throttling](../guides/throttling.md) — Controlling frequency
- [Engagement](../growth/engagement.md) — Activity notification patterns
- [Preferences](../guides/preferences.md) — User notification preferences
- [Inbox (v7 legacy)](./inbox-v7-legacy.md) — Recognition patterns and migration guidance for existing v7 code
- [v8 Migration Guide](https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide) — Step-by-step upgrade from v7

<!-- Target line budget: <= 850 lines. v7-specific content lives in inbox-v7-legacy.md; do not re-inline it here. If this file creeps past the budget, consider splitting v8 Web Components into its own file (inbox-web-components.md). -->
