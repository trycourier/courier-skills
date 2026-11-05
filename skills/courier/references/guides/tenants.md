# Tenants

A tenant is one of your customer organizations: the company, account, or workspace a group of your users belongs to. Attach users to it and store that customer's settings on it; one template then renders per tenant when a send carries its `tenant_id`.

What lives where on a tenant:

| What you store | Field |
|---|---|
| Logo, colors, email chrome | `brand_id`, referencing a [brand](./brands.md) |
| What's on/off for everyone at that company | `default_preferences`, plus per-topic overrides |
| Plan, region, support address, account manager | `properties`, readable from template content |
| Their own edited version of one of your templates | A [tenant-scoped template](#tenant-scoped-templates) |
| Their Slack bot token or Teams Bot Framework credentials | `user_profile` |
| Their position under a parent org | `parent_tenant_id` |

A tenant is not a recipient group (use a list or audience) and not a permissions system. A user can belong to many tenants, with independent preferences, branding, and Inbox feeds in each: the user decides who receives, the tenant decides which context builds the message.

To segment delivery data by customer, filter the message log by tenant: `GET /messages?tenant_id=acme-corp`. Don't use `providers[].reference` for this. Its contents are provider-specific, and the `tenantId` the MS Teams provider records there is the *Microsoft* tenant, not yours.

**Contents:** [Quick Reference](#quick-reference) · [Create or replace a tenant](#create-or-replace-a-tenant) · [Associate users, then send](#associate-users-then-send) · [Per-tenant preference overrides](#per-tenant-preference-overrides) · [Tenant-scoped templates](#tenant-scoped-templates)

## Quick Reference

### Rules
- `tenants.update` creates or replaces by the id you choose; `name` is required. It replaces the whole tenant: `properties`, `brand_id`, `user_profile`, and `default_preferences` you leave out are cleared, so send every field you want to keep.
- `brand_id: null` returns `400`, even though the SDK types allow `null`. To remove a brand, omit `brand_id`.
- Four layers load per send, as a sliding window; merging is parent first, child overwrites per key. `default_preferences` is the exception: a child with any items replaces the parent's whole list, see [Hierarchy and merging](#hierarchy-and-merging).
- An inbox client signed in with a `tenantId` shows only that tenant's messages. Signed in without one, it shows only messages sent without a tenant. Sign in with the `tenantId` the send carried.

### Common Mistakes
- Relying on auto-inferred tenant context for users who belong to more than one tenant.

## Create or replace a tenant

```ts
// Node
await client.tenants.update("acme-corp", {
  name: "Acme Corp",
  brand_id: "brand_acme",                 // optional, per-tenant branding (see brands.md)
  properties: { plan: "enterprise" },     // arbitrary metadata, available in templates as context
  // default_preferences, parent_tenant_id, user_profile also accepted
});
```

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

Other calls: `client.tenants.retrieve(id)`, `list()`, `delete(id)`, `listUsers(id)`. Python uses the same names in snake_case.

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
  template: { content: { version: "2022-01-01", elements: [/* channel-wrapped Elemental, see elemental.md */] } },
});
await client.tenants.templates.publish("nt_01k…", { tenant_id: "acme-corp" });
```

Send it with `template: "tenant/<template_id>"` and the tenant in `context`. `tenant` is the literal word, not the tenant id. Without the prefix the send succeeds with the workspace template, so the tenant's content never appears:

```ts
await client.send.message({
  message: { to: { user_id: "user-123" }, template: "tenant/nt_01k…", context: { tenant_id: "acme-corp" } },
});
```
