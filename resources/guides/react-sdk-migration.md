# React SDK v7 → v8 Migration

## Quick Reference

### Hard Rules

- NEVER mix v7 and v8 packages. Using `@trycourier/react-provider` or `@trycourier/react-inbox` alongside `@trycourier/courier-react` causes silent failures (no errors, no messages, no WebSocket connections).
- NEVER use `<CourierProvider>` with v8. It does not exist in v8; wrapping v8 components in it breaks initialization silently.
- NEVER use `clientKey` for authentication. v8 requires JWT tokens via `courier.shared.signIn()`.
- NEVER access `inbox.messages` directly. v8 organizes messages by dataset: `inbox.feeds[datasetId].messages`.
- ALWAYS remove ALL `@trycourier/react-*` packages before installing `@trycourier/courier-react`.
- ALWAYS call `courier.shared.signIn({ userId, jwt })` before rendering `<CourierInbox>` or `<CourierToast>`.
- ALWAYS call `inbox.registerFeeds()` and `inbox.listenForUpdates()` when using hooks.
- ALWAYS run `npm dedupe` after migration to prevent duplicate package versions.

### Silent Failure Modes

These produce zero errors but a broken inbox:

| Symptom | Cause | Fix |
|---------|-------|-----|
| Inbox renders but shows no messages | v7 `<CourierProvider>` wrapping v8 `<CourierInbox>` | Remove `<CourierProvider>`, use `courier.shared.signIn()` |
| Inbox renders but shows no messages | `clientKey` used instead of JWT | Generate JWT server-side, call `courier.shared.signIn()` |
| No network requests to Courier backend | Multiple `@trycourier/` package versions installed | Remove all `@trycourier/react-*`, run `npm dedupe` |
| Messages load once but no real-time updates | Missing `listenForUpdates()` call | Call `inbox.listenForUpdates()` after `registerFeeds()` |
| `inbox.messages` is undefined | v8 uses feeds/datasets, not flat array | Use `inbox.feeds[datasetId].messages` |

---

## Package Changes

v8 consolidates multiple packages into one:

```
Remove:
  @trycourier/react-provider
  @trycourier/react-inbox
  @trycourier/react-toast
  @trycourier/react-hooks

Install ONE of:
  @trycourier/courier-react       (React 18+)
  @trycourier/courier-react-17    (React 17)
```

Both packages have identical APIs; only the peer dependency differs.

## Authentication

v7 used `clientKey` (a static identifier) passed to `<CourierProvider>`. v8 uses JWT tokens with `courier.shared.signIn()`.

### v7 (deprecated)
```tsx
import { CourierProvider } from "@trycourier/react-provider";
import { Inbox } from "@trycourier/react-inbox";

<CourierProvider clientKey="YOUR_CLIENT_KEY">
  <Inbox />
</CourierProvider>
```

### v8
```tsx
import { useEffect, useState } from "react";
import { CourierInbox, useCourier } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();
  const [jwt, setJwt] = useState<string>();

  useEffect(() => {
    fetch("/api/courier-token")
      .then(res => res.json())
      .then(data => setJwt(data.token));
  }, [userId]);

  useEffect(() => {
    if (jwt) {
      courier.shared.signIn({ userId, jwt });
    }
  }, [jwt]);

  return <CourierInbox />;
}
```

JWT must be generated server-side:
```typescript
const response = await fetch("https://api.courier.com/auth/issue-token", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.COURIER_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    scope: "user_id:USER_ID inbox:read:messages inbox:write:events read:preferences write:preferences read:brands",
    expires_in: "7 days",
  }),
});
const { token } = await response.json();
```

## Component Mapping

| v7 | v8 | Notes |
|----|-----|-------|
| `<CourierProvider>` | Removed | Use `courier.shared.signIn()` instead |
| `<Inbox>` from `@trycourier/react-inbox` | `<CourierInbox>` | Standalone; no wrapper needed |
| `<Toast>` from `@trycourier/react-toast` | `<CourierToast>` | Standalone; no wrapper needed |
| `useInbox()` | `useCourier().inbox` | Hook renamed |
| `useToast()` | `useCourier().toast` | Hook renamed |
| `clientKey` prop | `courier.shared.signIn({ userId, jwt })` | JWT required |
| `renderMessage` | `renderListItem` | Prop renamed |
| `renderNoMessages` | `renderEmptyState` | Prop renamed |
| `inbox.messages` | `inbox.feeds[datasetId].messages` | Messages organized by dataset |
| `inbox.fetchMessages()` | `inbox.load()` | Method renamed |
| `inbox.markMessageRead(id)` | `inbox.readMessage(message)` | Takes full message object |
| `inbox.markMessageUnread(id)` | `inbox.unreadMessage(message)` | Takes full message object |
| `inbox.markMessageArchived(id)` | `inbox.archiveMessage(message)` | Takes full message object |
| `inbox.markAllAsRead()` | `inbox.readAllMessages()` | Method renamed |
| `toast(message)` | `toast.addMessage(message)` | Method renamed |
| Tags / Pins | Not yet supported in v8 | Stay on v7 if required |
| Markdown rendering | Not built-in | Use `markdown-to-jsx` with `renderListItem` |

## Feeds and Tabs (New in v8)

v8 introduces feeds and tabs for organizing messages into filtered views.

```tsx
import { CourierInbox, type CourierInboxFeed } from "@trycourier/courier-react";

const feeds: CourierInboxFeed[] = [
  {
    feedId: "notifications",
    title: "Notifications",
    tabs: [
      { datasetId: "all", title: "All", filter: {} },
      { datasetId: "unread", title: "Unread", filter: { status: "unread" } },
    ],
  },
];

<CourierInbox feeds={feeds} />
```

When using hooks, register feeds explicitly:
```tsx
const { inbox } = useCourier();

useEffect(() => {
  inbox.registerFeeds(feeds);
  inbox.listenForUpdates();
  inbox.load();
}, []);

const messages = inbox.feeds["all"]?.messages || [];
```

## Theming

v8 removes `styled-components` and supports theming natively with `lightTheme` / `darkTheme` props.

```tsx
import { CourierInbox, type CourierInboxTheme } from "@trycourier/courier-react";

const theme: CourierInboxTheme = {
  inbox: {
    header: { backgroundColor: "#0f0f0f" },
    list: { backgroundColor: "#1a1a1a" },
    item: {
      backgroundColor: "#222",
      hoverBackgroundColor: "#333",
    },
  },
};

<CourierInbox lightTheme={theme} darkTheme={darkTheme} mode="system" />
```

Key differences:
- `background` → `backgroundColor`
- `message.container` → `inbox.item`
- `footer` → removed (Courier watermark removed in v8)
- Dark mode: use `mode="system"` for automatic switching

## Toast Changes

```tsx
import { CourierToast, useCourier } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();

  useEffect(() => {
    courier.shared.signIn({ userId, jwt });
  }, [jwt]);

  return (
    <CourierToast
      autoDismiss={true}
      autoDismissTimeoutMs={5000}
      onToastItemClick={({ message }) => handleClick(message)}
    />
  );
}
```

Key prop changes:
- `autoClose` → `autoDismiss` + `autoDismissTimeoutMs`
- `onClick` → `onToastItemClick`
- `position` → use `style` prop
- `theme` → `lightTheme` / `darkTheme`

## Features Not Yet in v8

If your app requires any of these, stay on v7:
- **Tags** (message categorization)
- **Pins** (pinning messages to top)
- **Built-in Markdown rendering** (can be added via `renderListItem` + `markdown-to-jsx`)

## Troubleshooting

**No requests to Courier backend after upgrading:**
Multiple versions of `@trycourier/` packages installed. Run `npm dedupe` or check `node_modules` for duplicates. See [courier-web#92](https://github.com/trycourier/courier-web/issues/92).

**Must migrate Inbox and Toast together:**
v8 depends on a newer `@trycourier/courier-js` than v7. Running both on the same page causes conflicts.

## Related

- [Inbox channel guide](../channels/inbox.md) — best practices for in-app notifications
- [Full migration reference](https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide) — complete v8 migration docs with diff examples
