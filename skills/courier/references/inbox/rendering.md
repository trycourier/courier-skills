# Rendering the Inbox

The in-app notification center. Unlike every other Courier channel, the inbox renders **in your application**, so this is client-side work: authenticating a browser or device, mounting a component, and keeping read state in sync.

Sending a message *to* the inbox is server-side. See [inbox.md](../channels/inbox.md).

## The Model

Courier stores each user's inbox server-side. Your client authenticates as that user with a short-lived JWT, mounts a prebuilt component, and opens a WebSocket for live updates.

```
your server ──generates JWT──▶ your client ──signIn(jwt)──▶ Courier
                                    │
                                    ├── <CourierInbox />      renders the feed
                                    └── listenForUpdates()    WebSocket, live arrivals
```

Three things always happen, in this order. Skipping the third is the most common integration bug, messages arrive but the UI never changes until reload.

1. `shared.signIn({ userId, jwt })`
2. `inbox.registerFeeds(defaultFeeds())`
3. `inbox.listenForUpdates()`

## Which SDK

| Platform | Package | Depth here |
|---|---|---|
| React 17+ | `@trycourier/courier-react` | [react.md](./react.md) |
| Vue, Angular, Svelte, vanilla JS | `@trycourier/courier-ui-inbox` | [web-components.md](./web-components.md) |
| React Native | `@trycourier/courier-react-native` | [react-native.md](./react-native.md) |
| iOS (Swift) | `Courier_iOS` | [SDK docs](https://www.courier.com/docs/sdk-libraries/ios) |
| Android (Kotlin) | `courier-android` | [SDK docs](https://www.courier.com/docs/sdk-libraries/android) |
| Flutter | `courier_flutter` | [SDK docs](https://www.courier.com/docs/sdk-libraries/flutter) |

## Version Check Before You Write Code

This documents **v8**. Check what the project is on before adding anything.

| Import you see | Version | What to do |
|---|---|---|
| `@trycourier/courier-react`, `<CourierInbox />`, `useCourier()` | **v8** | Continue here |
| `@trycourier/react-provider`, `@trycourier/react-inbox`, `<CourierProvider>`, `<Inbox />`, a `clientKey` prop | **v7 (legacy)** | Read [legacy-v7.md](./legacy-v7.md) first |

Do not write new v7 code. If the project is on v7, propose migrating before adding features, the [migration guide](https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide) is step-by-step.

## Universal Rules

- **JWT only.** v8 requires it. Generate it server-side from your API key, an API key in client code grants full workspace access to anyone who opens devtools.
- **Scopes:** `user_id:{id} inbox:read:messages inbox:write:events read:preferences`
- **JWTs expire.** Refresh before expiry rather than letting the socket drop. See [auth.md](./auth.md).
- **Call `listenForUpdates()` after `signIn()`**, or nothing updates in real time.
- **Never call `signIn` with a JWT minted for a different user.** Sign out on user switch.

## Read State and Unread Counts

Read state lives client-side, synced across the user's devices by Courier.

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

From your backend you can only **archive** (`client.requests.archive(requestId)`), useful for clearing the inbox copy once the user acts on the email or push version of the same notification.

## Organizing the Feed

Filter tabs on `data` fields set at send time. Have the sender include a `category` and the client can split the feed without a schema change:

```jsonc
{ "category": "social", "actorId": "user-42", "targetId": "post-7" }
```

See [Feeds and Tabs](./react.md) for wiring tabs to those fields.

## Debugging

| Symptom | Cause to check first |
|---|---|
| Empty inbox, no errors | `signIn()` never resolved, or the JWT's `user_id` scope doesn't match the recipient |
| Messages appear only after reload | `listenForUpdates()` was never called |
| Works, then silently stops | JWT expired; no refresh in place |
| 401 from the SDK | JWT minted with missing scopes, or generated client-side |
| Message sent but never arrives | Server-side, the send never reached the `inbox` channel. Work the [delivery-failure ladder](../../SKILL.md#debugging-a-delivery-failure); check the [inbox channel](../channels/inbox.md) and preferences |
| Send succeeded, message invisible in a multi-tenant app | The send carried a `tenant_id` but `signIn` didn't (or vice versa). Tenant-scoped messages only show when the signed-in `tenantId` matches. See [tenants.md](../guides/tenants.md#auto-infer-and-two-silent-gotchas) |

## Where to Look

| Task | File |
|---|---|
| Generating and refreshing JWTs | [auth.md](./auth.md) |
| React: setup, popup, feeds, tabs, theming, custom components, toasts, hooks, SSR | [react.md](./react.md) |
| Vue / Angular / Svelte / vanilla JS | [web-components.md](./web-components.md) |
| React Native | [react-native.md](./react-native.md) |
| Recognizing and migrating v7 | [legacy-v7.md](./legacy-v7.md) |
| Sending *to* the inbox | [inbox.md](../channels/inbox.md) |
