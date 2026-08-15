# Tenants

A tenant is a workspace/account in a B2B app, a customer of your customer. Attach users to a tenant,
and one template renders per-tenant: the tenant's brand, preference defaults, and context apply
automatically when a send carries its `tenant_id`.

## Create or update a tenant (upsert)

`update` upserts by the id you choose; `name` is required.

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

- **Four layers load per send, as a sliding window.** In a deeper tree, loading a tenant's context
  starts at most three ancestors up, not at the root. A five-deep hierarchy silently drops the
  topmost tenant's settings for leaf sends
- **Merging is parent first, child overwrites per key.** `brand_id` and `user_profile` keys from a
  child win over the parent's
- **Profile precedence at send time:** tenant-hierarchy `user_profile` merge, then the user's stored
  Courier profile, then the send call's own `profile`, which wins

**Per-tenant provider credentials** are the reason `user_profile` exists on a tenant: store each
customer org's own Slack `access_token` or Teams webhook there, and every send carrying that
`tenant_id` routes through that org's workspace with no per-user token management:

```json
{ "user_profile": { "slack": { "access_token": "xoxb-..." } } }
```

### Auto-infer, and two silent gotchas

- **Auto-infer tenant context:** when a user belongs to exactly one tenant and the send names none,
  Courier loads that tenant's context automatically (toggle in workspace settings). Useful for
  Studio, list, and audience sends; surprising when you didn't expect tenant branding to apply
- **Tenant-scoped Inbox messages are invisible outside their tenant.** A send with `tenant_id:
  "acme"` only appears when the client signed in with that same `tenantId`. Sign in without it and
  the message simply never shows, with nothing failing. See
  [inbox/rendering.md](../inbox/rendering.md)

| Operation | Node |
|---|---|
| Get | `client.tenants.retrieve(tenantId)` |
| List | `client.tenants.list()` |
| Delete | `client.tenants.delete(tenantId)` |
| List users in a tenant | `client.tenants.listUsers(tenantId)` |

## Associate users, then send

```ts
await client.users.tenants.addSingle("acme-corp", { user_id: "user-123" });

await client.send.message({
  message: {
    to: { user_id: "user-123", tenant_id: "acme-corp" },   // or message.context.tenant_id
    template: "invoice-ready",
    data: { amount: "$1,200" },
  },
});
```

When the send carries `tenant_id`, Courier applies that tenant's `brand_id` and preference defaults to
the rendered template automatically. `tenant_id` is valid on the recipient (`to.tenant_id`) or in
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

## Tenant-scoped templates

Content that overrides the default template for one tenant (`tenants.templates`):

```ts
await client.tenants.templates.list("acme-corp");                              // tenant id positional
await client.tenants.templates.retrieve("nt_01k…", { tenant_id: "acme-corp" });
await client.tenants.templates.replace("nt_01k…", { tenant_id: "acme-corp" /* + content */ });
await client.tenants.templates.publish("nt_01k…", { tenant_id: "acme-corp" });
```

Confirm exact request bodies (brand `settings`, template content) against the installed types under
`resources/tenants/`. For the multi-tenant design pattern end-to-end, see [patterns.md](./patterns.md);
for brand shapes, [brands.md](./brands.md).
