# Bulk API

Build a job, ingest recipients into it in batches, run it once. Use it for a large recipient set
that isn't already a list or audience.

## Quick Reference

### Rules
- **`message.event` is required on create.** A notification ID works as the value, but the key must be `event`. `template` and `content` are optional overrides on top of it, never substitutes.
- **Ingest is `POST /bulk/{jobId}`** with no `/users` suffix. Only the read is `GET /bulk/{jobId}/users`.
- **Batch ingest at 1000 users or fewer per call.** Call it as many times as you need before running.
- **Email jobs need `profile.email` on every user.** `to.email` alone does not route, and the failure is silent.
- **A job runs once.** After `runJob` the job is closed; more users need a new job.
- **Poll `retrieveJob` for progress**, not `messages.retrieve`. The job id is not a message id.

### When to reach for what

| Approach | Use when | Ceiling |
|---|---|---|
| `to: { list_id }` / `to: { audience_id }` | The set is already a list or audience | None; Courier fans out server-side |
| `to: [ ... ]` (multi-recipient send) | A handful of ad-hoc recipients | **500**, hard cap |
| **Bulk API** | A large ad-hoc set, per-recipient data, or you want job-level progress | ≤1000 per ingest call, unlimited calls |

If the set is already modeled in Courier, send to it directly ([patterns.md](./patterns.md#lists-and-audience-sends),
[audiences.md](./audiences.md)). Bulk exists for the case where it isn't.

### Common Mistakes
- Omitting `event` and passing only `template` (returns `400 The 'event' parameter is required.`)
- `POST /bulk/{jobId}/users` to ingest (404; that path is the read)
- Putting the email on `to.email` instead of `profile.email` for an email job
- Ingesting more than ~1000 users in a single call (502)
- Expecting `runJob` to pick up users added afterwards
- Passing the job id to `messages.retrieve` (404; it is a job id, not a message id)

## The Flow

Four calls: create, ingest, run, then poll.

**TypeScript:**
```typescript
// 1. Create. `message.event` is REQUIRED: an event ID or a notification ID.
const { jobId } = await client.bulk.createJob({
  message: {
    event: "monthly-digest",                    // required
    template: "nt_01kmrbs3q6w9x2c5v8n1d4tjh",   // optional; overrides the event's notification
    data: { month: "August" },                  // global data, merged into every recipient
    brand: "bnd_01kx4mrd0pfzw8wt7pn7p2fzag",    // optional
  },
});

// 2. Ingest. Repeat as needed; batch at 1000 or fewer per call.
await client.bulk.addUsers(jobId, {
  users: [
    { profile: { email: "jane@example.com" }, to: { user_id: "user-1" }, data: { highlights: 12 } },
    { profile: { email: "sam@example.com" }, to: { user_id: "user-2" }, data: { highlights: 4 } },
  ],
});

// 3. Run. One-way door: a job can only be run once.
await client.bulk.runJob(jobId);

// 4. Poll.
const { job } = await client.bulk.retrieveJob(jobId);
// job.status:  CREATED | PROCESSING | COMPLETED | ERROR
// job.received / job.enqueued / job.failures

// Per-recipient outcomes, paginated.
const { items, paging } = await client.bulk.listUsers(jobId);
// items[].status: PENDING | ENQUEUED | ERROR
// items[].messageId is the same id a single send would return
```

**Python:**
```python
job = client.bulk.create_job(
    message={
        "event": "monthly-digest",
        "data": {"month": "August"},
    }
)

client.bulk.add_users(
    job.job_id,
    users=[
        {"profile": {"email": "jane@example.com"}, "to": {"user_id": "user-1"}, "data": {"highlights": 12}},
    ],
)

client.bulk.run_job(job.job_id)

status = client.bulk.retrieve_job(job.job_id)
users = client.bulk.list_users(job.job_id)
```

**curl** (useful when the installed SDK predates the bulk restore, see [Version note](#version-note)):
```bash
# 1. Create
curl -X POST https://api.courier.com/bulk \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message":{"event":"monthly-digest","data":{"month":"August"}}}'
# -> 201 {"jobId":"1-6a7e474b-..."}

# 2. Ingest (note: no /users suffix)
curl -X POST https://api.courier.com/bulk/JOB_ID \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"users":[{"profile":{"email":"jane@example.com"},"to":{"user_id":"user-1"}}]}'
# -> 200 {"errors":[],"total":1}

# 3. Run
curl -X POST https://api.courier.com/bulk/JOB_ID/run \
  -H "Authorization: Bearer $COURIER_API_KEY"

# 4. Poll
curl https://api.courier.com/bulk/JOB_ID   -H "Authorization: Bearer $COURIER_API_KEY"
curl https://api.courier.com/bulk/JOB_ID/users -H "Authorization: Bearer $COURIER_API_KEY"
```

**CLI:** see [cli.md](./cli.md#lists-and-bulk) for `courier bulk create-job / add-users / run-job /
retrieve-job / list-users`.

**MCP:** `create_bulk_job` → `add_bulk_users` → `run_bulk_job`, plus `get_bulk_job` and
`list_bulk_users`. See [mcp.md](./mcp.md#bulk).

## Gotchas

Worth knowing up front, since several of these fail quietly or with a generic error.

- **`message.event` is required.** Passing `message.template` alone returns
  `400 {"message":"The 'event' parameter is required."}`. The value can be a notification ID, so
  `{ event: "<notification-id>" }` works, but the key must be `event`.
- **Ingest is `POST /bulk/{jobId}`, with no `/users` suffix.** `POST /bulk/{jobId}/users` returns
  404. Only the *read* is `GET /bulk/{jobId}/users`. Easy to get backwards.
- **Batch at 1000 users or fewer per ingest call.** 1000 returns `200 {"errors":[],"total":1000}`;
  5000 and above return `502`. Ingest as many batches as you like before running.
- **Email jobs need `profile.email` on each user.** `to.email` alone is not enough for provider
  routing and the message will not deliver, with no error at ingest time. Same shape for SMS and
  push: contact info goes on `profile`, not `to`. This is the single most common bulk failure.
- **A job runs once.** After `runJob`, ingesting more users into it does nothing. Create a new job.
- **Ingest reports partial failures rather than failing the call.** The response is
  `{"errors":[...],"total":N}` with a 200. Duplicates land in `errors` while the rest succeed, so
  check it instead of relying on the status code.
- **Global `data` is merged into every recipient and overridden per user.** Which per-user field
  wins is ambiguous in the current docs: both `user.data` and `user.to.data` exist, the API
  reference attaches merge behavior to `user.data`, and the tutorial uses `to.data`. Prefer
  `user.data` (what the SDK docstrings use) and verify against the installed types if it matters.

## Monitoring a Job

| Call | Returns |
|---|---|
| `retrieveJob(jobId)` | `{ job: { status, received, enqueued, failures, definition } }` |
| `listUsers(jobId)` | `{ items: [{ status, messageId, ... }], paging }`, paginated by cursor |

| Job status | Meaning |
|---|---|
| `CREATED` | Accepting ingested users, not yet running |
| `PROCESSING` | Running, fanning out to recipients |
| `COMPLETED` | Finished; check `failures` for partial problems |
| `ERROR` | The job itself failed |

Per-recipient status is `PENDING`, `ENQUEUED`, or `ERROR`. `COMPLETED` is not the same as
"everything delivered": it means the job finished enqueuing. Delivery status per recipient is a
message-level question, so follow `items[].messageId` into
[`messages.retrieve`](./reliability.md#message-status-glossary), or watch for
[`message:updated` webhooks](./webhooks.md#event-types).

Job-level aggregates live on `retrieveJob`, never on `client.messages.retrieve`. The job's
`requestId` is not a message ID: resolve per-recipient message IDs via
`courier messages list --trace-id "<requestId>"` (see
[CLI debugging](./cli.md#debugging-list-bulk-sends-requestid-vs-message-id)).

<a id="version-note"></a>

## Version note

Bulk was removed from the API spec, and therefore from every generated SDK, on 2026-07-23, then
restored. The REST endpoints served traffic the whole time; only the spec, the SDKs, and the
reference docs lost them.

| SDK | Missing in | Restored in |
|---|---|---|
| Node `@trycourier/courier` | 7.21.0 through 7.25.0 | **7.25.1** |
| Python `trycourier` | up to and including 7.26.0 | **7.26.1** |
| CLI | 3.12.x | **3.13.0** |

If `client.bulk` is `undefined`, that is a version problem, not a missing feature. Upgrade, or call
the REST endpoints directly with the curl above. Verify method shapes against the installed
package's own types rather than this file, per
[Verifying Against Live Sources](../../SKILL.md#verifying-against-live-sources).

> One claim worth checking before relying on it: the tutorial states that all bulk endpoints accept
> an `Idempotency-Key` header, but the API spec does not declare that header on any of the five bulk
> operations. Treat it as unverified.

## Related

- [patterns.md](./patterns.md#lists-and-audience-sends): list and audience sends, the alternative to bulk
- [audiences.md](./audiences.md): dynamic segments, which fan out without a job
- [cli.md](./cli.md#lists-and-bulk): CLI equivalents and delivery debugging
- [reliability.md](./reliability.md): delivery statuses and retry semantics
- [Create a bulk job](https://www.courier.com/docs/api-reference/bulk/create-a-bulk-job) · [Send Bulk Notifications tutorial](https://www.courier.com/docs/tutorials/sending/how-to-send-bulk-notifications)
