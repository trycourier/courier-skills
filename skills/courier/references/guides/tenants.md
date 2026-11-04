# Tenants

A tenant is one of your customer organizations: the company, account, or workspace a group of your
users belongs to. If you sell to businesses, you almost certainly have this object in your own
database already. Attach users to a tenant, store everything specific to that customer on it, and
one template renders per-tenant: the brand, preference defaults, properties, and credentials apply
automatically when a send carries its `tenant_id`.

What lives where on a tenant:

| What you store | Field |
|---|---|
| Logo, colors, email chrome | `brand_id`, referencing a [brand](./brands.md) |
| What's on/off for everyone at that company | `default_preferences`, plus per-topic overrides |
| Plan, region, support address, account manager | `properties`, readable from template content |
| Their own edited version of one of your templates | A [tenant-scoped template](#tenant-scoped-templates) |
| Their Slack bot token or Teams Bot Framework credentials | `user_profile` |
| Their position under a parent org | `parent_tenant_id` |

Two things tenants are **not**: a way to group recipients (use a list or audience for "send this to
these people" — tenants isolate customers, they don't gather people), and a permissions system
(authorization stays in your application). A user can belong to many tenants, with independent
preferences, branding, and Inbox feeds in each; a send names both the `user_id` and a `context.tenant_id`. The
user determines who receives, the tenant determines which context builds the message.

To segment delivery data by customer afterwards, filter the message log by tenant:
`GET /messages?tenant_id=acme-corp` ("messages sent with the context of a tenant"). Don't reach for
`providers[].reference` for this — its contents are provider-specific, and the `tenantId` the MS Teams
provider records there is the *Microsoft* tenant, not yours.

**Contents:** [Quick Reference](#quick-reference) · [Create or replace a tenant](#create-or-replace-a-tenant) · [Associate users, then send](#associate-users-then-send) · [Per-tenant preference overrides](#per-tenant-preference-overrides) · [Tenant-scoped templates](#tenant-scoped-templates)

## Quick Reference

### Rules
- `tenants.update` creates or replaces by the id you choose; `name` is required. It replaces the whole tenant: `properties`, `brand_id`, `user_profile`, and `default_preferences` you leave out are cleared, so send every field you want to keep.
- `brand_id: null` returns `400`, even though the SDK types allow `null`. To remove a brand, omit `brand_id`.
- Four layers load per send, as a sliding window; merging is parent first, child overwrites per key. `default_preferences` is the exception: a child with any items replaces the parent's whole list, see [Hierarchy and merging](#hierarchy-and-merging).
- An inbox client signed in with a `tenantId` shows only that tenant's messages. Signed in without one, it shows only messages sent without a tenant. Sign in with the `tenantId` the send carried.
- Pass the tenant on the recipient (`to.context.tenant_id`) or in `message.context.tenant_id`, and use one form consistently. `to: { user_id, tenant_id }` returns `400`, even though the SDK types allow it. `to: { tenant_id }` alone sends to every member of the tenant.

### Common Mistakes
- Signing the inbox client in without a `tenantId`, or with a different one, after a tenant-scoped send. The message never shows and nothing fails.
- Relying on auto-inferred tenant context for users who belong to more than one tenant.

## Create or replace a tenant

`update` creates or replaces by the id you choose (`PUT /tenants/{id}`); `name` is required. It replaces the whole tenant, so a field you leave out (`properties`, `brand_id`, `user_profile`, `default_preferences`) is cleared. To change one field, read the tenant first and send everything back. To remove a brand, omit `brand_id`: `brand_id: null` returns `400`.

```ts
// Node
await client.tenants.update("acme-corp", {
  name: "Acme Corp",
  brand_id: "brand_acme",                 // optional, per-tenant branding (see brands.md)
  properties: { plan: "enterprise" },     // arbitrary metadata, available in templates as context
  // default_preferences, parent_tenant_id, user_profile also accepted
});
```

```python
# Python
client.tenants.update("acme-corp", name="Acme Corp", brand_id="brand_acme",
                      properties={"plan": "enterprise"})
```

A tenant carries `name`, `brand_id`, `default_preferences`, `properties`, `parent_tenant_id`, and
`user_profile`. A **child** tenant (`parent_tenant_id` set) inherits the parent's brand and defaults.

### Hierarchy and merging

- **Four levels load, as a sliding window.** Courier starts at most three ancestors above the tenant a send names, not at the root, so in a five-deep hierarchy the root's settings never reach a leaf send. Keep the tree to four levels
- **A tenant's `user_profile` merges into the recipient's profile, not into `data`.** Interpolate it
  as `{{profile.key}}`; `{{key}}` renders empty
- **Merging is parent first, child overwrites per key.** `brand_id` and `user_profile` keys from a
  child win over the parent's
- **`default_preferences` inherits as one list, not per topic.** A child with no items uses its
  parent's list. A child with any items replaces it, and topics missing from the child's list fall
  back to their workspace default, not the parent's
- **Profile precedence at send time:** tenant-hierarchy `user_profile` merge, then the user's stored
  Courier profile, then the send call's own `profile`, which wins

**Per-tenant provider credentials** are the reason `user_profile` exists on a tenant: store each
customer org's own Slack `access_token` or Teams Bot Framework fields (`service_url`, `tenant_id`)
there, and every send carrying that
`tenant_id` routes through that org's workspace with no per-user token management:

```json
{ "user_profile": { "slack": { "access_token": "xoxb-..." } } }
```

This is also how one [journey](./journeys.md) serves every customer: a send node carries
`message.context.tenant_id` and its Slack/Teams sends pick up that tenant's stored credentials —
see [Slack and Teams sends](./journeys.md#slack-and-teams-sends) for the reference forms and rules.

### Auto-infer and other send gotchas

- **Auto-infer tenant context:** when a user belongs to exactly one tenant and the send names none,
  Courier loads that tenant's context automatically (toggle in workspace settings). Useful for
  Studio, list, and audience sends; surprising when you didn't expect tenant branding to apply
- **A user in two or more tenants needs `context.tenant_id` on every send.** Without it the send
  fails with `Tenant Context Not Found`
- **Membership isn't required to send in a tenant's context.** A user who isn't a member still gets
  the tenant's brand and credentials when the send names the tenant
- **A tenant fan-out uses the named tenant's preferences.** Sending to `{ tenant_id, include_children: true }`
  checks every member, including members of child tenants, against the `default_preferences` of the
  tenant you sent to, not their own tenant's. When child tenants keep their own preferences, send to
  each child tenant directly
- **Sign the inbox in with the `tenantId` the send carried.** A send with `tenant_id: "acme"` shows
  only for a client signed in with `tenantId: "acme"`. A client signed in without a `tenantId` shows
  only messages sent without a tenant. Signed in without one or with another, the tenant-scoped
  message never shows, and nothing fails. With no
  `tenantId`, the unread count can still include tenant-scoped messages the list doesn't show. See
  [inbox/rendering.md](../inbox/rendering.md)

| Operation | Node | Python |
|---|---|---|
| Get | `client.tenants.retrieve(tenantId)` | `client.tenants.retrieve(tenant_id)` |
| List | `client.tenants.list()` | `client.tenants.list()` |
| Delete | `client.tenants.delete(tenantId)` | `client.tenants.delete(tenant_id)` |
| List users in a tenant | `client.tenants.listUsers(tenantId)` | `client.tenants.list_users(tenant_id)` |

## Associate users, then send

```ts
await client.users.tenants.addSingle("acme-corp", { user_id: "user-123" });

await client.send.message({
  message: {
    to: { user_id: "user-123", context: { tenant_id: "acme-corp" } },   // or message.context.tenant_id
    template: "invoice-ready",
    data: { amount: "$1,200" },
  },
});
```

When the send carries `tenant_id`, Courier applies that tenant's `brand_id` and preference defaults to
the rendered template automatically. `tenant_id` is valid in the recipient's context (`to.context.tenant_id`) or in
`message.context.tenant_id`. Pick one and use it consistently.

## Per-tenant preference overrides

Set a topic's default status for everyone in the tenant (`tenants.preferences.items`):

```ts
await client.tenants.preferences.items.update("topic-abc", {
  tenant_id: "acme-corp",
  status: "OPTED_OUT",                    // 'OPTED_IN' | 'OPTED_OUT' | 'REQUIRED'
  has_custom_routing: true,               // optional
  custom_routing: ["inbox", "email"],     // optional, channels for this topic
});
await client.tenants.preferences.items.delete("topic-abc", { tenant_id: "acme-corp" });
```

On a child tenant, the first `items.update` starts the child's own list, so every topic the parent
set and the child doesn't falls back to its workspace default. To change one topic and keep the
rest, write the parent's other items to the child too, and update the child when the parent's list
changes.

## Tenant-scoped templates

Content that overrides the default template for one tenant (`tenants.templates`):

```ts
await client.tenants.templates.list("acme-corp");                              // tenant id positional
await client.tenants.templates.retrieve("nt_01k…", { tenant_id: "acme-corp" });
await client.tenants.templates.replace("nt_01k…", {
  tenant_id: "acme-corp",
  template: {
    content: {
      version: "2022-01-01",
      elements: [
        {
          type: "channel",
          channel: "email",
          elements: [
            { type: "meta", title: "Welcome to Acme" },
            { type: "text", content: "Hi from Acme" },
          ],
        },
      ],
    },
  },
});
await client.tenants.templates.publish("nt_01k…", { tenant_id: "acme-corp" });
```

Confirm exact request bodies (brand `settings`, template content) against the installed types under
`resources/tenants/`. For the multi-tenant design pattern end-to-end, see [patterns.md](./patterns.md);
for brand shapes, [brands.md](./brands.md).
