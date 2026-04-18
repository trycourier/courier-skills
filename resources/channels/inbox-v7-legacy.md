# In-App Inbox — v7 Legacy Reference

> **For new projects: use v8.** See [inbox.md](./inbox.md). Only read this file when you are confirming that existing code is on v7 **and** the user has an explicit blocker preventing upgrade (e.g., v7-only Tags or Pins that haven't landed in v8 yet).

## Quick Reference

### When to use this file

- An existing codebase imports `@trycourier/react-provider`, `@trycourier/react-inbox`, or `@trycourier/react-toast`, **and**
- The user has asked about maintaining that code, **and**
- They cannot upgrade yet.

For every other case — including new inboxes, new features on existing inboxes, or any refactor — write v8 code per [inbox.md](./inbox.md) and help the user migrate.

### Rules for v7 work

- Avoid using v7 for new projects; default to v8 unless there's a concrete blocker.
- For net-new inbox features, prefer a v8 migration first. If migration is temporarily blocked, keep v7 changes as small and local as possible.
- Client Keys are still accepted by v7 but JWT is strongly preferred. If a codebase passes a `clientKey` prop, recommend moving to JWT as part of the next meaningful touch.
- If staying on v7, leave a migration follow-up note (issue or TODO) so the codebase does not get stuck in legacy mode.

### Quick validation checklist (before shipping a v7 change)

- Confirm this is truly v7 using package/import signals in the Version Detection table below.
- Confirm and document the migration blocker (for example, dependency on v7-only Tags or Pins).
- Keep scope to maintenance/bugfix updates; avoid introducing new v7-only architectural surface.
- Run a smoke test: inbox renders, auth succeeds, and new messages appear in the feed.
- Add a migration pointer to v8 docs in the PR or task notes.

## Version Detection

| Signal | Version |
|--------|---------|
| `@trycourier/courier-react` or `@trycourier/courier-react-17` in `package.json` | **v8** |
| `@trycourier/courier-ui-inbox` (Web Components) in `package.json` | **v8** |
| `<CourierInbox />`, `useCourier()`, `courier.shared.signIn()` | **v8** |
| `@trycourier/react-provider`, `@trycourier/react-inbox`, `@trycourier/react-toast` in `package.json` | **v7** |
| `<CourierProvider>`, `<Inbox />`, `useInbox()`, `clientKey` prop | **v7** |
| New project / no existing code | **Use v8** |

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

Contrast with the v8 shape in [inbox.md](./inbox.md): a single package (`@trycourier/courier-react`), `useCourier()` + `courier.shared.signIn()`, JWT-only, `<CourierInbox />`.

## Key v7 → v8 Differences

| Concern | v7 | v8 |
|---------|----|----|
| Packages | `@trycourier/react-provider` + `@trycourier/react-inbox` + `@trycourier/react-toast` | Single: `@trycourier/courier-react` |
| Wrapping | `<CourierProvider>` | No provider; `useCourier()` hook |
| Auth | `clientKey` prop accepted (JWT preferred) | JWT required |
| Sign in | Implicit via provider props | Explicit: `courier.shared.signIn({ userId, jwt })` |
| Real-time | Auto | Explicit: `inbox.listenForUpdates()` |
| Tags / Pins | Supported | **Not yet** — only blocker where v7 is still needed |

## Migration Path

When the user is ready to upgrade, the canonical migration is documented here: https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide

High-level steps:

1. Replace the three v7 packages with `@trycourier/courier-react`.
2. Remove `<CourierProvider>`; call `courier.shared.signIn({ userId, jwt })` inside an effect once the JWT is available.
3. Replace `<Inbox />` with `<CourierInbox />`.
4. Wire a server endpoint that issues a JWT (example in [inbox.md](./inbox.md) "Authentication").
5. After sign-in, call `inbox.registerFeeds(defaultFeeds())` and `inbox.listenForUpdates()`.
6. Migrate custom styling — v8 uses a different theming API.

## Related

- [Inbox (v8)](./inbox.md) — primary, authoritative guide
- [v8 Migration Guide](https://www.courier.com/docs/sdk-libraries/courier-react-v8-migration-guide) — official step-by-step

<!-- Target line budget: <= 200 lines. This file exists to recognize v7 and route to migration; detailed v8 content must live in inbox.md. -->
