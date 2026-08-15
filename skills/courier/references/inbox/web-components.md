# Courier Inbox Web Components

Framework-agnostic custom elements, Vue, Angular, Svelte, or plain JavaScript.

Web Components work with **any framework or no framework at all**, Vue, Angular, Svelte, vanilla JS, server-rendered HTML, WordPress, etc. They use the same v8 SDK and real-time infrastructure as the React components.

### Installation

**With a bundler (npm):**

```bash
npm install @trycourier/courier-ui-inbox @trycourier/courier-ui-toast
```

**Without a bundler (CDN script tag):**

```html
<script type="module" src="https://unpkg.com/@trycourier/courier-ui-inbox@latest/dist/index.mjs"></script>
<script type="module" src="https://unpkg.com/@trycourier/courier-ui-toast@latest/dist/index.mjs"></script>
```

The CDN approach requires no build step. Add the script tags and use the custom elements immediately.

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
  <script type="module" src="https://unpkg.com/@trycourier/courier-ui-inbox@latest/dist/index.mjs"></script>
</head>
<body>
  <courier-inbox id="inbox"></courier-inbox>

  <script type="module">
    const { Courier } = await import('https://unpkg.com/@trycourier/courier-ui-inbox@latest/dist/index.mjs');

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
