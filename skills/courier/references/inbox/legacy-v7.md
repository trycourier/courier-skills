# In-App Inbox, v7 Legacy Reference

> **For new projects: use v8.** See [rendering.md](./rendering.md). Only read this file when you are confirming that existing code is on v7 **and** the user has an explicit blocker preventing upgrade (e.g., Pins, or adding and removing tags from the client, neither of which v8 supports yet).

**Contents:** [Quick Reference](#quick-reference) · [Version Detection](#version-detection) · [v7 Shape (for recognition only)](#v7-shape-for-recognition-only) · [Key v7 → v8 Differences](#key-v7--v8-differences) · [Migration Path](#migration-path)

## Quick Reference

### Rules for v7 work

- **In v6 and v7, pass the JWT as `authorization`** on `<CourierProvider>` (`@trycourier/react-provider`), not `authentication`: `<CourierProvider authorization={jwt} userId="user-123">`. Mint it with `user_id:<id>`, `inbox:read:messages` and `inbox:write:events`. If the Courier Inbox integration has JWT or HMAC turned on in its settings, the client must authenticate that way
- **v7 renders markdown when the Courier Inbox integration's Markdown Rendering setting is on**; v8 has no built-in markdown. A word with underscores inside it (`test_table_name_`) turns italic with markdown-to-jsx before v9, which is what v7 and the v8 migration guide use. Set the integration to plain text, or render with markdown-to-jsx v9 in a v8 custom list item
- Client Keys are still accepted by v7 but JWT is strongly preferred. If a codebase passes a `clientKey` prop, recommend moving to JWT as part of the next meaningful touch.

### Common Mistakes

- **v7 reads auth once, on mount.** A token that arrives later is ignored, so the provider must be gated on having it. Mount unconditionally with an async token and you get a permanently empty inbox and no error.
- **A freshly sent message can take about a minute to appear** in v7's default feed, while the message is already retrievable. Not your code. A new integration therefore looks broken for its first minute, and auth is the natural but wrong suspect.
- **Action clicks need `onRouteChange`.** The built-in handler awaits `markMessageRead` and `trackClick` before calling `window.open`, by which point it has lost user activation and popup blockers drop the navigation silently.
- **A single action renders no button.** The whole row becomes the click target. That is intended in v7, but v8 draws a visible button for the identical payload, so migrating changes the look of every single-action message with no content change.
- **A client key is base64 of `<tenant>/<env>`, and that env must match the API key's env.** An `env_01k...` segment is rejected with `403`; a `test` segment against an env-scoped API key returns `200` with an empty node list and no error, so auth looks fine and the inbox is simply empty.
- Keeping only the v7 CSP hosts in a v8 app. v8 also needs `https://api.courier.com` and `wss://realtime.courier.io`, see [Content Security Policy](./rendering.md#content-security-policy).

## Version Detection

v8 vs v7 signals are in [rendering.md](./rendering.md#version-check-before-you-write-code). `@trycourier/react-toast`, `@trycourier/react-hooks`, and `useInbox()` also mean v7; `@trycourier/courier-ui-inbox` means v8.

## v7 Shape (for recognition only)

A typical v7 setup uses three separate packages and a provider wrapper:

```tsx
// v7 — legacy, do not use for new code
import { CourierProvider } from "@trycourier/react-provider";
import { Inbox } from "@trycourier/react-inbox";

export default function App() {
  return (
    <CourierProvider
      clientKey={process.env.NEXT_PUBLIC_COURIER_CLIENT_KEY}
      userId="user-123"
    >
      <Inbox />
    </CourierProvider>
  );
}
```

## Key v7 → v8 Differences

| Concern | v7 | v8 |
|---------|----|----|
| Packages | `@trycourier/react-provider` + `@trycourier/react-inbox` + `@trycourier/react-toast` (+ `@trycourier/react-hooks`) | Single: `@trycourier/courier-react` |
| Wrapping | `<CourierProvider>` | No provider; `useCourier()` hook |
| Auth | `clientKey` prop accepted (JWT preferred) | JWT required |
| Sign in | Implicit via provider props | Explicit: `courier.shared.signIn({ userId, jwt })` |
| Real-time | Auto | Auto for `<CourierInbox />`. A custom UI calls `inbox.listenForUpdates()` |
| Tags / Pins | Supported, including client-side `addTag` / `removeTag` | Tags are set on the send and filtered by tabs, with no client-side edits. Pins **not yet** |
| CSP hosts | `https://inbox.courier.com`, `wss://realtime.courier.com` | `https://api.courier.com`, `https://inbox.courier.com`, `wss://realtime.courier.io`, `wss://realtime.courier.com` |

## Migration Path

Follow the [v8 migration guide](https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide): swap the v7 packages for `@trycourier/courier-react` and `<Inbox />` for `<CourierInbox />`. The steps that bite:

1. Remove `<CourierProvider>` and call `courier.shared.signIn({ userId, jwt })` in an effect once the JWT is available, served by a backend endpoint ([auth.md](./auth.md)).
2. A custom UI on `useCourier()` needs the three post-sign-in calls in [rendering.md](./rendering.md#the-model). `<CourierInbox />` needs none.
3. Theming is a different API in v8; restyle with `lightTheme` / `darkTheme`.
4. **Update the CSP.** Add `wss://realtime.courier.io` and `https://api.courier.com`, keep
   `wss://realtime.courier.com`, and confirm `style-src` allows `'unsafe-inline'`. Missing this leaves an
   inbox that loads but never updates in real time, or renders unstyled, with no error either way.
