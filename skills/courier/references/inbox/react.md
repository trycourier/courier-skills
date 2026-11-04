# Courier Inbox for React

**Contents:** [Quick Reference](#quick-reference) · [Installation](#installation) · [Basic Setup (v8)](#basic-setup-v8) · [Popup Menu (v8)](#popup-menu-v8) · [Feeds and Tabs (v8)](#feeds-and-tabs-v8) · [Customized Inbox (v8)](#customized-inbox-v8) · [Custom Components (v8)](#custom-components-v8) · [Click Handlers (v8)](#click-handlers-v8) · [Toast Notifications (v8)](#toast-notifications-v8) · [useCourier Hook (v8)](#usecourier-hook-v8) · [Next.js / SSR (v8)](#nextjs--ssr-v8)

## Quick Reference

### Rules
- v8 is `useCourier()` plus `courier.shared.signIn()`. No provider wrapper.
- `<CourierInbox />` and `<CourierInboxPopupMenu />` stay live on their own after `signIn()`. A custom UI on `useCourier()` must call `inbox.listenForUpdates()`, or messages arrive but the UI never changes until reload.
- Components render client-side only. In Next.js 13+, add `'use client'`.

### Common Mistakes

- Calling `signIn` before the JWT exists, or on every render. Gate it on having a token and call it once per user session.
- Rendering the inbox without allowing the Courier hosts in the CSP, or without `style-src 'unsafe-inline'`. The failure looks like an auth problem, see [Content Security Policy](./rendering.md#content-security-policy).
- Assuming a US workspace's hosts work for an EU workspace, see [EU and regional hosts](./rendering.md#eu-and-regional-hosts).

### Installation

```bash
# React 18+
npm install @trycourier/courier-react

# React 17
npm install @trycourier/courier-react-17
```

On React 17, import from `@trycourier/courier-react-17` wherever this file says `@trycourier/courier-react`. The exports are the same.

### Basic Setup (v8)

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

Same sign-in; render `<CourierInboxPopupMenu />` instead of `<CourierInbox />` for a bell icon with a dropdown. Gate `signIn` on the token, e.g. with `useCourierToken` from [auth.md](./auth.md#jwt-refresh-strategy).

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
| `archived` | `boolean` | `true` shows only archived messages. Unset or `false` shows only unarchived ones, so no single tab mixes both |
| `status` | `'read' \| 'unread'` | Filter by read/unread status |
| `from` | `string` | ISO 8601 datetime. Only messages created at or after it |

A message's tags come from `metadata.tags` on the send, see [Organizing the Feed](./rendering.md#organizing-the-feed).

### Customized Inbox (v8)

v8 uses native theming via `lightTheme`/`darkTheme` props, no styled-components dependency:

```tsx
import { CourierInbox, type CourierInboxTheme } from "@trycourier/courier-react";

const theme: CourierInboxTheme = {
  inbox: {
    header: {
      feeds: { button: { unreadCountIndicator: { backgroundColor: "#9121C2" } } },
      tabs: {
        default: { unreadIndicator: { backgroundColor: "#9121C2" } },
        selected: { unreadIndicator: { backgroundColor: "#9121C2" } },
      },
    },
    list: {
      item: { unreadIndicatorColor: "#9121C2" },
    },
  },
};

<CourierInbox lightTheme={theme} darkTheme={theme} mode="light" />;
```

With the default feeds, or any feed with one tab, the tab bar is hidden and the count sits on the feed button, so `tabs.*.unreadIndicator` shows nothing. Style it with `inbox.header.feeds.button.unreadCountIndicator`.

Dark mode switches automatically with `mode="system"`, or force with `mode="light"` / `mode="dark"`.

### Custom Components (v8)

Override parts with render props: `renderListItem`, `renderHeader`, `renderMenuButton` (popup menu only), `renderLoadingState`, `renderEmptyState`, `renderErrorState`, `renderPaginationItem`. Each receives the matching `CourierInbox…FactoryProps` (e.g. `CourierInboxListItemFactoryProps`), which can be `undefined` or `null`, so check before reading fields:

```tsx
import { CourierInbox, type CourierInboxListItemFactoryProps } from "@trycourier/courier-react";

<CourierInbox
  renderListItem={(props: CourierInboxListItemFactoryProps | undefined | null) => {
    if (!props) return null;
    const { message } = props;
    return (
      <div className="custom-message">
        <strong>{message.title}</strong>
        <p>{message.body}</p>
        <time>{message.created}</time>
      </div>
    );
  }}
/>;
```

### Click Handlers (v8)

`onMessageClick` and `onMessageLongPress` receive `{ message, index }`; `onMessageActionClick` receives `{ message, action, index }`.

```tsx
<CourierInbox
  onMessageClick={({ message, index }) => {
    if (message.data?.deepLink) router.push(message.data.deepLink);
  }}
  onMessageActionClick={({ message, action, index }) => {
    window.open(action.href);
  }}
/>
```

### Toast Notifications (v8)

Toasts are short-lived notifications connected to the Inbox message feed. Mount one beside your app; it uses the same `signIn` as the inbox:

```tsx
import { CourierToast } from "@trycourier/courier-react";

<CourierToast
  autoDismiss={true}
  autoDismissTimeoutMs={5000}
  onToastItemClick={({ message }) => { if (message.data?.deepLink) window.location.href = message.data.deepLink; }}
/>;
```

Use `lightTheme` and `darkTheme` props for styling. Use `renderToastItem` or `renderToastItemContent` for fully custom rendering.

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

  // One tab's count. totalUnreadCount sums every tab, so overlapping tabs count a message twice.
  const unreadCount = inbox.feeds["all_messages"]?.unreadCount ?? 0;
  const messages = inbox.feeds["all_messages"]?.messages ?? [];

  return (
    <ul aria-label={`${unreadCount} unread`}>
      {messages.map((msg: InboxMessage) => (
        <li key={msg.messageId}>{msg.read ? "" : "• "}{msg.title}</li>
      ))}
    </ul>
  );
}
```

Key hook methods:

| Method | Description |
|--------|-------------|
| `inbox.registerFeeds(feeds)` | Register feeds and tabs with the datastore |
| `inbox.listenForUpdates()` | Start WebSocket connection for real-time updates |
| `inbox.load()` | Load messages (supports `{ canUseCache }`) |
| `inbox.readMessage(message)` | Mark as read |
| `inbox.unreadMessage(message)` | Mark as unread |
| `inbox.archiveMessage(message)` | Archive |
| `inbox.unarchiveMessage(message)` | Unarchive |
| `inbox.readAllMessages()` | Mark all as read |
| `inbox.fetchNextPageOfMessages({ datasetId })` | Fetch next page |

### Next.js / SSR (v8)

Courier components only render client-side. In Next.js 13+, put `"use client";` at the top of any file that renders them.

---
