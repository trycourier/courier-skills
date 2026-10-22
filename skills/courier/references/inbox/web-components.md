# Courier Inbox Web Components

## Quick Reference

### Rules
- Import `Courier` from `@trycourier/courier-ui-inbox` and call `Courier.shared.signIn()`. The elements load and open the socket themselves.
- Wire click handlers with the element methods or `CustomEvent`s, not the HTML string attributes.
- Loading from a CDN needs an import map, `script-src https://unpkg.com`, and pinned versions.

### Common Mistakes

- Using the `message-click` / `message-action-click` / `message-long-press` **HTML attributes**. They compile with `new Function()`, need `script-src 'unsafe-eval'`, and fail silently without it. Use the element methods or the `CustomEvent`s, see [Event Handling](#event-handling).
- Loading from the CDN without an import map, without `script-src https://unpkg.com` in the CSP, or with `@latest` in production.
- Omitting `style-src 'unsafe-inline'`, which renders the inbox unstyled with no error, see [Content Security Policy](./rendering.md#content-security-policy).
- Calling element methods before the custom element is defined. Await the module import first.
- Skipping `listenForUpdates()` in a custom UI built on `CourierInboxDatastore`. Call `CourierInboxDatastore.shared.registerFeeds(defaultFeeds())`, then `listenForUpdates()`, then `load()`.

Framework-agnostic custom elements for Svelte, plain JavaScript, server-rendered HTML, or any framework without its own Courier package. Vue and Angular have wrappers built on these elements, `@trycourier/courier-vue` and `@trycourier/courier-angular`.

They use the same v8 SDK and real-time infrastructure as the React components.

### Installation

**With a bundler (npm):**

```bash
npm install @trycourier/courier-ui-inbox @trycourier/courier-ui-toast
```

**Without a bundler (CDN):**

The ES modules import `@trycourier/courier-js` and `@trycourier/courier-ui-core` by bare name, which a browser can't resolve alone. Put an import map before any module script, pinned to the versions each package depends on:

```html
<script type="importmap">
{
  "imports": {
    "@trycourier/courier-js": "https://unpkg.com/@trycourier/courier-js@3.7.1/dist/index.mjs",
    "@trycourier/courier-ui-core": "https://unpkg.com/@trycourier/courier-ui-core@2.5.2/dist/index.mjs",
    "@trycourier/courier-ui-inbox": "https://unpkg.com/@trycourier/courier-ui-inbox@2.7.2/dist/index.mjs",
    "@trycourier/courier-ui-toast": "https://unpkg.com/@trycourier/courier-ui-toast@2.4.2/dist/index.mjs"
  }
}
</script>
```

Still no build step. A CSP needs `script-src https://unpkg.com`, and inline scripts need a nonce or hash. When you bump a version, match `npm view @trycourier/courier-ui-inbox dependencies` so inbox and toast share one `courier-js`. A bundled npm install needs no `script-src` host, see
[Content Security Policy](./rendering.md#content-security-policy).

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
  <script type="importmap">
  {
    "imports": {
      "@trycourier/courier-js": "https://unpkg.com/@trycourier/courier-js@3.7.1/dist/index.mjs",
      "@trycourier/courier-ui-core": "https://unpkg.com/@trycourier/courier-ui-core@2.5.2/dist/index.mjs",
      "@trycourier/courier-ui-inbox": "https://unpkg.com/@trycourier/courier-ui-inbox@2.7.2/dist/index.mjs"
    }
  }
  </script>
</head>
<body>
  <courier-inbox id="inbox"></courier-inbox>

  <script type="module">
    import { Courier } from '@trycourier/courier-ui-inbox';

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
    if (message.data?.deepLink) window.location.href = message.data.deepLink;
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
    if (message.data?.deepLink) window.location.href = message.data.deepLink;
  });

  inbox.onMessageActionClick(({ message, action, index }) => {
    window.open(action.href);
  });

  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

The elements also dispatch `CustomEvent`s of the same names, which is the right hook for frameworks that
bind declaratively:

```html
<courier-inbox id="inbox"></courier-inbox>

<script type="module">
  document.getElementById('inbox').addEventListener('message-click', (e) => {
    const { message, index } = e.detail;
    if (message.data?.deepLink) window.location.href = message.data.deepLink;
  });
</script>
```

**Use the methods or the events, not the HTML string attributes.** `<courier-inbox>` and
`<courier-inbox-popup-menu>` also accept `message-click`, `message-action-click`, and `message-long-press`
as HTML attributes containing a JavaScript string, but those are compiled with `new Function()`, so they
need `script-src 'unsafe-eval'`. Under a normal CSP the failure is silent: the throw is caught and logged
and the handler never runs. The methods and the `CustomEvent`s have no such requirement. Vue's
`@message-click` already uses the event path. See
[Content Security Policy](./rendering.md#content-security-policy).

### Unread Badge (Vanilla JS)

Build a custom notification bell with unread count without any framework:

```html
<button id="notif-bell">
  🔔 <span id="badge" style="display:none;"></span>
</button>
<courier-inbox id="inbox" style="display:none;"></courier-inbox>

<script type="module">
  import {
    Courier,
    CourierInboxDatastore,
    CourierInboxDataStoreListener,
  } from '@trycourier/courier-ui-inbox';

  const inbox = document.getElementById('inbox');
  const badge = document.getElementById('badge');
  const bell = document.getElementById('notif-bell');

  bell.addEventListener('click', () => {
    inbox.style.display = inbox.style.display === 'none' ? 'block' : 'none';
  });

  function updateBadge(count) {
    badge.textContent = count > 99 ? '99+' : String(count);
    badge.style.display = count > 0 ? 'inline' : 'none';
  }

  // The mounted <courier-inbox> loads the default feeds after sign-in. Count one tab:
  // totalUnreadCount also adds unread messages from the Archive tab.
  CourierInboxDatastore.shared.addDataStoreListener(
    new CourierInboxDataStoreListener({
      onUnreadCountChange: (count, datasetId) => {
        if (datasetId === 'all_messages') updateBadge(count);
      },
    })
  );
  updateBadge(CourierInboxDatastore.shared.getDatasetById('all_messages')?.unreadCount ?? 0);

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
| `CourierInboxDatastore.shared.totalUnreadCount` | datastore | Sum of every registered tab's unread count (read-only). Overlapping tabs count a message once per tab; for a badge read one tab: `CourierInboxDatastore.shared.getDatasetById('all_messages')?.unreadCount` |

The `message-click`, `message-action-click`, and `message-long-press` `CustomEvent`s carry the same
payload as the matching `on...` method in `event.detail`. The identically named **HTML attributes** are a
third form that requires `script-src 'unsafe-eval'`; prefer the methods or events.

---
