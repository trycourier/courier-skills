# Audiences

An audience is a **filter whose membership Courier stores and keeps current**. Send to `audience_id`
and Courier fans out to the stored members. Use it for dynamic segments (trial users, a
plan tier, an activity cohort); use a **list** when you want an explicit, managed set of subscribers.

## Quick Reference

### Rules
- An audience is a filter whose membership Courier stores and keeps current. Create or update it with an upsert by the id you choose.
- Send to it with `to: { audience_id: "..." }`; Courier fans out to every current member.
- Preferences still apply: a marketing audience only reaches opted-in users.

### Common Mistakes
- Treating an audience like a static list. Membership changes as user data changes.
- Expecting an audience send to bypass preferences.

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

```python
# Python
client.audiences.update(
    "trial-users-no-integration",
    name="Trial users without an integration",
    filter={"operator": "AND", "filters": [
        {"operator": "EQ", "path": "plan", "value": "trial"},
    ]},
)
```

`filter.filters` is an array of rules; each rule is a single condition (a comparison `operator` with
a `path` + `value`) or a nested group (`operator` `AND`/`OR` with its own `filters`). `path` is an
attribute on the user profile. The comparison operators:

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
Changing the filter starts a rebuild that can take many minutes, and a send during a rebuild reads a
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

One send, Courier fans out to every current member, with no cap on how many that is. A recipient's
[preferences](./preferences.md) still apply, so marketing audiences only reach opted-in users. The
`requestId` returned is a job id; resolve per-recipient message ids via
`courier messages list --trace-id "<requestId>"` (see [cli.md](./cli.md)).

Audience vs list: an **audience** is a filter whose stored membership Courier updates as profiles
change; a **list** is an explicit subscriber set you add/remove from. See [patterns.md](./patterns.md) for list sends.

If the recipient set isn't modeled as an audience or a list, reach for the
[Bulk API](./bulk.md) rather than a multi-recipient send. A plain `to` array is capped
at 500 recipients.
