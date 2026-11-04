# Courier Inbox Web Components

**Contents:** [Quick Reference](#quick-reference) · [Installation](#installation) · [Basic Setup](#basic-setup) · [Popup Menu](#popup-menu) · [Toast Notifications](#toast-notifications) · [Feeds, Tabs, and Theming](#feeds-tabs-and-theming) · [Event Handling](#event-handling) · [Unread Badge (Vanilla JS)](#unread-badge-vanilla-js) · [Web Components API Reference](#web-components-api-reference)

## Quick Reference

### Rules
- Import `Courier` from `@trycourier/courier-ui-inbox` and call `Courier.shared.signIn()`. The elements load and open the socket themselves.

### Common Mistakes

- Using the `message-click` / `message-action-click` / `message-long-press` **HTML attributes** instead of the element methods or `CustomEvent`s. They need `script-src 'unsafe-eval'` and fail silently without it, see [Event Handling](#event-handling).
- Loading from the CDN without an import map, without `script-src https://unpkg.com` in the CSP, or with `@latest` in production.
- Omitting `style-src 'unsafe-inline'`, which renders the inbox unstyled with no error, see [Content Security Policy](./rendering.md#content-security-policy).
- Calling element methods before the custom element is defined. Await the module import first.
- Skipping `listenForUpdates()` in a custom UI built on `CourierInboxDatastore`, see [the call order](./rendering.md#the-model).

Framework-agnostic custom elements for Svelte, plain JavaScript, server-rendered HTML, or any framework without its own Courier package. Vue and Angular have wrappers built on these elements, `@trycourier/courier-vue` and `@trycourier/courier-angular`.

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

```html
<courier-inbox id="inbox"></courier-inbox>

<script type="module">
  import { Courier } from '@trycourier/courier-ui-inbox';

  const jwt = await fetch('/api/courier-token')
    .then(r => r.json())
    .then(d => d.token);

  Courier.shared.signIn({ userId: 'user-123', jwt });
</script>
```

Without a bundler, put the [import map](#installation) in `<head>` before this script. Nothing else changes.

### Popup Menu

`<courier-inbox-popup-menu>` is the bell icon with a dropdown. Sign in the same way.

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

The elements also dispatch `CustomEvent`s of the same names, with the payload in `event.detail`, which is the right hook for frameworks that bind declaratively:

```html
<courier-inbox id="inbox"></courier-inbox>

<script type="module">
  document.getElementById('inbox').addEventListener('message-click', (e) => {
    const { message, index } = e.detail;
    if (message.data?.deepLink) window.location.href = message.data.deepLink;
  });
</script>
```

**Use the methods or the events, not the HTML string attributes** of the same names. Those are compiled with `new Function()`, need `script-src 'unsafe-eval'`, and under a normal CSP never fire, with no error. Vue's `@message-click` already uses the event path.

### Unread Badge (Vanilla JS)

Build a custom notification bell with unread count without any framework:

```html
<courier-inbox id="inbox" style="display:none;"></courier-inbox>

<script type="module">
  import { Courier, CourierInboxDatastore, CourierInboxDataStoreListener } from '@trycourier/courier-ui-inbox';

  // The mounted <courier-inbox> loads the default feeds after sign-in. Count one tab:
  // totalUnreadCount also adds unread messages from the Archive tab.
  CourierInboxDatastore.shared.addDataStoreListener(
    new CourierInboxDataStoreListener({
      onUnreadCountChange: (count, datasetId) => {
        if (datasetId === 'all_messages') updateBadge(count); // your own DOM update
      },
    })
  );
  updateBadge(CourierInboxDatastore.shared.getDatasetById('all_messages')?.unreadCount ?? 0);

  Courier.shared.signIn({ userId: 'user-123', jwt: '...' });
</script>
```

### Web Components API Reference

| Method / Property | Available On | Description |
|-------------------|-------------|-------------|
| `setFeeds(feeds)` | `courier-inbox` | Configure feeds and tabs |
| `setLightTheme(theme)` | `courier-inbox`, `courier-toast` | Set light mode theme |
| `setDarkTheme(theme)` | `courier-inbox`, `courier-toast` | Set dark mode theme |
| `onMessageClick(cb)` | `courier-inbox` | Handle message click |
| `onMessageActionClick(cb)` | `courier-inbox` | Handle action button click |
| `onToastItemClick(cb)` | `courier-toast` | Handle toast click |
| `CourierInboxDatastore.shared.totalUnreadCount` | datastore | Sum of every registered tab's unread count, so overlapping tabs count a message twice. For a badge, read one tab, see [Unread Badge](#unread-badge-vanilla-js) |

---
