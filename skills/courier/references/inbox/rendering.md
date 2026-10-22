# Rendering the Inbox

The in-app notification center. Unlike every other Courier channel, the inbox renders **in your application**, so this is client-side work: authenticating a browser or device, mounting a component, and keeping read state in sync.

Sending a message *to* the inbox is server-side. See [inbox.md](../channels/inbox.md).

## Quick Reference

### Common Mistakes

- Working the auth ladder before ruling out CSP. Every auth symptom has a quieter CSP twin, see [Debugging](#debugging).
- Skipping `listenForUpdates()` in a custom UI built on `useCourier()` or `CourierInboxDatastore`. The built-in components call it themselves.
- Shipping an API key to the client instead of a JWT.
- Using US hosts for an EU workspace, or expecting a `region` option that doesn't exist, see [EU and regional hosts](#eu-and-regional-hosts).
- Writing new v7 code because the project already has some, see [legacy-v7.md](./legacy-v7.md).

## The Model

Courier stores each user's inbox server-side. Your client authenticates as that user with a short-lived JWT, mounts a prebuilt component, and opens a WebSocket for live updates.

```
your server ──generates JWT──▶ your client ──signIn(jwt)──▶ Courier
                                    │
                                    ├── <CourierInbox />      renders the feed
                                    └── listenForUpdates()    WebSocket, live arrivals (custom UI only)
```

With a built-in component, `signIn()` is the only call. After sign-in it loads its feeds and opens the realtime socket itself.

A custom UI on `useCourier()` or `CourierInboxDatastore` makes three calls after `signIn()`, in this order:

1. `inbox.registerFeeds(defaultFeeds())`
2. `inbox.listenForUpdates()`
3. `inbox.load()`

On the web components' datastore the same calls are `CourierInboxDatastore.shared.registerFeeds(defaultFeeds())`, then `listenForUpdates()`, then `load()`.

Skipping the second means messages arrive but the UI never changes until reload.

## Which SDK

| Platform | Package | Depth here |
|---|---|---|
| React 18+ | `@trycourier/courier-react` | [react.md](./react.md) |
| React 17 | `@trycourier/courier-react-17` | [react.md](./react.md) |
| Vue 3.3+ | `@trycourier/courier-vue` | [SDK docs](https://www.courier.com/docs/sdk-libraries/courier-vue-web) |
| Angular 17+ | `@trycourier/courier-angular` | [SDK docs](https://www.courier.com/docs/sdk-libraries/courier-angular-web) |
| Svelte, vanilla JS, other frameworks | `@trycourier/courier-ui-inbox` | [web-components.md](./web-components.md) |
| React Native | `@trycourier/courier-react-native` | [react-native.md](./react-native.md) |
| iOS (Swift) | `Courier_iOS` | [SDK docs](https://www.courier.com/docs/sdk-libraries/ios) |
| Android (Kotlin) | `courier-android` | [SDK docs](https://www.courier.com/docs/sdk-libraries/android) |
| Flutter | `courier_flutter` | [SDK docs](https://www.courier.com/docs/sdk-libraries/flutter) |

## Version Check Before You Write Code

This documents **v8**, the `@trycourier/courier-react` 8.x and 9.x releases. Check what the project is on before adding anything.

| Import you see | Version | What to do |
|---|---|---|
| `@trycourier/courier-react`, `<CourierInbox />`, `useCourier()` | **v8** | Continue here |
| `@trycourier/react-provider`, `@trycourier/react-inbox`, `<CourierProvider>`, `<Inbox />`, a `clientKey` prop | **v7 (legacy)** | Read [legacy-v7.md](./legacy-v7.md) first |

Do not write new v7 code. If the project is on v7, propose migrating before adding features, the [migration guide](https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide) is step-by-step.

<a id="universal-rules"></a>

### Rules

- **JWT only.** v8 requires it. Generate it server-side from your API key, an API key in client code grants full workspace access to anyone who opens devtools.
- **Scopes:** `user_id:{id} inbox:read:messages inbox:write:events`, plus `read:preferences write:preferences` if you also mount preferences. See [auth.md](./auth.md)
- **JWTs expire.** Refresh before expiry rather than letting the socket drop. See [auth.md](./auth.md).
- **Built-in components need only `signIn()`.** A custom UI also calls `listenForUpdates()`, or nothing updates in real time.
- **Never call `signIn` with a JWT minted for a different user.** Sign out on user switch.
- **Allow the Courier hosts in your CSP** before you debug anything else. A blocked host or a blocked
  inline style looks exactly like an auth failure. See [Content Security Policy](#content-security-policy).
- **EU workspaces need different hosts.** There is no `region` option; pass `apiUrls`. See
  [EU and regional hosts](#eu-and-regional-hosts).

## Read State and Unread Counts

Courier stores read state. The SDK changes it from the client, and Courier syncs it to every device where the user is signed in.

```tsx
import { useCourier } from "@trycourier/courier-react";

// Reads the shared datastore. Mount <CourierInbox /> or <CourierInboxPopupMenu /> on the page, or run registerFeeds → listenForUpdates → load first.
function NotificationBell() {
  const { inbox } = useCourier();
  // One tab's count. totalUnreadCount sums every tab, so overlapping tabs count a message twice.
  const unreadCount = inbox.feeds["all_messages"]?.unreadCount ?? 0;

  return (
    <button onClick={() => inbox.readAllMessages()}>
      🔔 {unreadCount > 0 && <Badge count={unreadCount} />}
    </button>
  );
}
```

From your backend you can only **archive** (`client.requests.archive(requestId)`), useful for clearing the inbox copy once the user acts on the email or push version of the same notification.

## Organizing the Feed

Tabs filter on `tags`, `status`, `archived`, and `from`, never on `data` fields. A message gets its tags from `metadata.tags` at send time, so have the sender tag it for its tab:

```jsonc
{ "metadata": { "tags": ["social"] } }
```

A filter can't add a tag later. See [Feeds and Tabs](./react.md#feeds-and-tabs-v8) for wiring tabs to those tags.

## Debugging

**Rule out CSP first.** Every auth symptom below has a CSP twin, and CSP failures are quieter.

| Symptom | Cause to check first |
|---|---|
| Inbox renders, but completely unstyled | `style-src` (really `style-src-elem`) without `'unsafe-inline'`. The components inject `<style>` elements and there is no nonce or hash API |
| Messages arrive only on reload, console shows a blocked WebSocket | `connect-src` missing `wss://realtime.courier.io`. Note `.io`; allow `.com` as well |
| Empty inbox, network requests blocked in devtools | `connect-src` missing `https://api.courier.com` or `https://inbox.courier.com` |
| A `message-click`, `message-action-click`, or `message-long-press` HTML attribute never fires | `script-src` without `'unsafe-eval'`. Use the element method or the `CustomEvent` instead, both CSP-safe |
| Empty inbox, no errors | `signIn()` never ran, the JWT is expired or lacks `inbox:read:messages` / `inbox:write:events`, or its `user_id` doesn't match the recipient. Check the CSP rows above first, they present identically |
| Messages appear only after reload | The WebSocket is CSP-blocked, see above. In a custom UI, `listenForUpdates()` was never called |
| Works, then silently stops | JWT expired; no refresh in place |
| Empty inbox or `401`s on an EU workspace | Region mismatch. Mint at `https://api.eu.courier.com/auth/issue-token` (Node: `new Courier({ baseURL: "https://api.eu.courier.com" })`) and pass `apiUrls: getCourierApiUrlsForRegion("eu")` to `signIn`, see [EU and regional hosts](#eu-and-regional-hosts) |
| Message sent but never arrives | Server-side, the send never reached the `inbox` channel. Work the [delivery-failure ladder](../../SKILL.md#debugging-a-delivery-failure); check the [inbox channel](../channels/inbox.md) and preferences |
| Send succeeded, message invisible in a multi-tenant app | Sign in with the same `tenantId` the send carried. A different `tenantId` hides the message. See [tenants.md](../guides/tenants.md#auto-infer-and-two-silent-gotchas) |

## Content Security Policy

If the app sets a CSP, the inbox needs these directives. A missing one fails quietly, so check this before working the auth ladder.

### connect-src

| Region | Hosts |
|---|---|
| US (default) | `https://api.courier.com` `https://inbox.courier.com` `wss://realtime.courier.io` `wss://realtime.courier.com` |
| EU | `https://api.eu.courier.com` `https://inbox.eu.courier.io` `wss://realtime.eu.courier.io` |

**Every v8 release opens its WebSocket on `realtime.courier.io`, with `.io`.** Everything else on US is `.com`. Courier's CSP list also names `wss://realtime.courier.com`, the v7 host. Allowing it is harmless, so allow both. A migration that keeps only the v7 host has a dead realtime connection, and the inbox only updates on reload.

### style-src

Needs `'unsafe-inline'`. The components inject `<style>` elements at runtime, both into shadow roots and into `document.head`, which puts them under `style-src-elem`. **The packages expose no nonce or hash API**, so `'unsafe-inline'` is currently the only way to style the inbox. Without it the inbox renders, unstyled, with no error.

### script-src

Nothing extra for a bundled npm install. There is no `eval`, no `Worker`, and no injected `<script>`. Two exceptions:

- **`'unsafe-eval'` is required only if you use the HTML string attributes** `message-click`, `message-action-click`, or `message-long-press` on `<courier-inbox>` or `<courier-inbox-popup-menu>`. Those are compiled with `new Function()`, and under a normal CSP the throw is caught and logged, so the handler simply never fires. Prefer the element methods (`inbox.onMessageClick(fn)`) or the dispatched `CustomEvent`s of the same names, which need no `'unsafe-eval'`. Vue's `@message-click` already uses the event path.
- **Loading the components from a CDN** instead of bundling needs that CDN host, e.g. `script-src https://unpkg.com`, plus an import map for the packages' bare imports. See [web-components.md](./web-components.md#installation).

### img-src

The inbox itself draws only inline SVG, so it needs nothing. Preference components are different: `courier-ui-preferences` and `courier-react` set an `<img>` source from `brand.logo.image`, so if you render preferences, `img-src` has to allow whatever host serves your brand logo.

### frame-src

Only needed if you embed the hosted preference center in an iframe, which serves from `https://view.notificationcenter.app`. Not needed for the inbox.

## EU and regional hosts

There is **no `region` option** on `signIn()`. Pass `apiUrls`:

```typescript
signIn({ userId: "user-123", jwt, apiUrls: getCourierApiUrlsForRegion("eu") }); // 'us' | 'eu', default 'us'
```

Import `getCourierApiUrlsForRegion` (or the `EU_COURIER_API_URLS` / `DEFAULT_COURIER_API_URLS` objects) from the package you installed, `@trycourier/courier-react` or `@trycourier/courier-ui-inbox`. Both re-export it. Don't import from `@trycourier/courier-js`: it's a transitive dependency and won't resolve under pnpm or Yarn PnP.

Mint the JWT in the same region. A US-minted token won't authenticate against EU hosts.

React reaches `signIn` via `useCourier()` (`courier.shared.signIn`); web components use the exported `Courier` class (`Courier.shared.signIn`). See [react.md](./react.md), [web-components.md](./web-components.md).

Getting the region wrong looks like an empty inbox. Update the CSP to the EU hosts at the same time.

## Where to Look

| Task | File |
|---|---|
| Generating and refreshing JWTs | [auth.md](./auth.md) |
| React: setup, popup, feeds, tabs, theming, custom components, toasts, hooks, SSR | [react.md](./react.md) |
| Vue | [SDK docs](https://www.courier.com/docs/sdk-libraries/courier-vue-web) |
| Angular | [SDK docs](https://www.courier.com/docs/sdk-libraries/courier-angular-web) |
| Svelte, vanilla JS | [web-components.md](./web-components.md) |
| React Native | [react-native.md](./react-native.md) |
| Recognizing and migrating v7 | [legacy-v7.md](./legacy-v7.md) |
| Sending *to* the inbox | [inbox.md](../channels/inbox.md) |
