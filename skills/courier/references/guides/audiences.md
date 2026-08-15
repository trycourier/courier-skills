# Audiences

An audience is a **filter Courier evaluates and keeps current**. Send to `audience_id` and Courier
resolves the matching users at send time and fans out. Use it for dynamic segments (trial users, a
plan tier, an activity cohort); use a **list** when you want an explicit, managed set of subscribers.

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

`filter.filters` is an array of rules; each rule is a single condition (`operator` is a comparison
like `EQ`, `NEQ`, `GT`, `LT`, `GTE`, `LTE` with a `path` + `value`) or a nested group (`operator`
`AND`/`OR` with its own `filters`). `path` is an attribute on the user profile. Confirm the full
operator set against the [API reference](https://www.courier.com/docs/api-reference/), the SDK types
type `operator` as a string.

## Read, list, members, delete

| Operation | Node | Python |
|---|---|---|
| Get | `client.audiences.retrieve(audienceId)` | `client.audiences.retrieve(audience_id)` |
| List all | `client.audiences.list()` | `client.audiences.list()` |
| List members (who currently matches) | `client.audiences.listMembers(audienceId)` | `client.audiences.list_members(audience_id)` |
| Delete | `client.audiences.delete(audienceId)` | `client.audiences.delete(audience_id)` |

`listMembers` is how you inspect who an audience resolves to right now, membership is computed from
the filter, not stored, so it reflects the latest profiles.

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

Audience vs list: an **audience** is a live filter (membership recomputed each send); a **list** is an
explicit subscriber set you add/remove from. See [patterns.md](./patterns.md) for list sends.

If the recipient set isn't modeled as an audience or a list, reach for the
[Bulk API](./bulk.md) rather than a multi-recipient send. A plain `to` array is capped
at 500 recipients.
