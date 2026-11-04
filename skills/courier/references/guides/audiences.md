# Audiences

An audience is a **filter whose membership Courier stores and keeps current**. Send to `audience_id`
and Courier fans out to the stored members. Use it for dynamic segments (trial users, a
plan tier, an activity cohort); use a **list** when you want an explicit, managed set of subscribers.

**Contents:** [Quick Reference](#quick-reference) · [Create or update (upsert)](#create-or-update-upsert) · [Read, list, members, delete](#read-list-members-delete) · [Send to an audience](#send-to-an-audience)

## Quick Reference

### Rules
- Create or update an audience with an upsert by the id you choose. Membership is stored and changes as user data changes, so it isn't a static list.
- Send with `to: { audience_id: "..." }`; Courier fans out to every current member. Preferences still apply: a marketing audience only reaches opted-in users.
- A filter `path` is relative to the profile root: `plan` for a top-level field, `custom.plan` for one under `custom`. A `profile.` prefix silently matches no one.

## Create or update (upsert)

There is no separate `create`, `update` upserts by the id you choose.

```ts
// Node
await client.audiences.update("trial-users-no-integration", {
  name: "Trial users without an integration",
  description: "Trial-plan users who haven't connected anything yet",
  filter: {
    operator: "AND",                                   // combine the rules below
    filters: [
      { operator: "EQ", path: "plan", value: "trial" },     // profile attribute EQ value
      { operator: "EQ", path: "integrations_count", value: "0" },
    ],
  },
});
```

Python: `client.audiences.update(audience_id, name=..., filter={"operator": "AND", "filters": [...]})`.

`filter.filters` is an array of rules; each rule is a single condition (a comparison `operator` with a `path` + `value`) or a nested group (`operator` `AND`/`OR` with its own `filters`). The comparison operators:

| `operator` | Meaning |
|---|---|
| `EQ` / `NEQ` | Equals / not equal |
| `INCLUDES` / `OMIT` | Contains / doesn't contain (substring) |
| `STARTS_WITH` / `ENDS_WITH` | Prefix / suffix |
| `GT` / `GTE` / `LT` / `LTE` | Greater / greater-or-equal / less / less-or-equal |
| `IS_AFTER` / `IS_BEFORE` | After / before (dates) |
| `EXISTS` | Present |

The SDK types `operator` as a plain string, so it won't catch a typo.

## Read, list, members, delete

| Operation | Node | Python |
|---|---|---|
| Get | `client.audiences.retrieve(audienceId)` | `client.audiences.retrieve(audience_id)` |
| List all | `client.audiences.list()` | `client.audiences.list()` |
| List members (who currently matches) | `client.audiences.listMembers(audienceId)` | `client.audiences.list_members(audience_id)` |
| Delete | `client.audiences.delete(audienceId)` | `client.audiences.delete(audience_id)` |

`listMembers` shows who is in the audience now. Membership is stored, not computed at send time.
It follows profile edits within about 2 minutes. Changing the filter starts a rebuild that can take many minutes, and a send during a rebuild reads a
partly updated list, so check `listMembers` before a large send.

## Send to an audience

```ts
await client.send.message({
  message: {
    to: { audience_id: "trial-users-no-integration" },
    template: "nudge-connect-integration",
    data: { cta: "Connect your first integration" },
  },
});
```

One send, Courier fans out to every current member, with no cap on how many that is.

`context.tenant_id` on an audience send sets branding, preferences, and template variables only.
Every member still receives the message.
