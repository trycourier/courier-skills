# Courier Inbox for React

### Installation

```bash
# React 18+
npm install @trycourier/courier-react

# React 17
npm install @trycourier/courier-react-17
```

### Basic Setup (v8)

v8 uses `useCourier()` hook + `courier.shared.signIn()`, no provider wrapper needed:

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
// useCourierToken — see auth.md, "JWT Refresh Strategy".

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

v8 uses native theming via `lightTheme`/`darkTheme` props, no styled-components dependency:

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
// useCourierToken — defined in auth.md, "JWT Refresh Strategy"; fetches a
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
