# Bulk API

Build a job, ingest recipients into it in batches, run it once. Use it for a large recipient set
that isn't already a list or audience.

**Contents:** [Quick Reference](#quick-reference) · [The Flow](#the-flow) · [Gotchas](#gotchas) · [Monitoring a Job](#monitoring-a-job) · [Version note](#version-note) · [Related](#related)

## Quick Reference

### Rules
- **`message.event` is required on create.** A notification ID works as the value, but the key must be `event`. `template` and `content` are optional overrides on top of it, never substitutes. `template` alone returns `400 The 'event' parameter is required.`
- **Ingest is `POST /bulk/{jobId}`** with no `/users` suffix. Only the read is `GET /bulk/{jobId}/users`; a `POST` there returns `404`.
- **Batch ingest at 1000 users or fewer per call** (5000 and above return `502`). Call it as many times as you need before running.
- **Contact info goes on `profile`, not `to`.** Email jobs need `profile.email` on every user; `to.email` alone does not route, and the failure is silent. Same for SMS and push. This is the most common bulk failure.
- **A job runs once.** After `runJob` the job is closed; users ingested afterwards are ignored, so create a new job.
- **Poll `retrieveJob` for progress**, not `messages.retrieve`. The job id is not a message id (`404`); per-recipient message ids come from `listUsers`.

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

Python uses snake_case (`create_job`, `add_users`, `run_job`, `retrieve_job`, `list_users`), with the id at `job.job_id`.

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
`list_bulk_users`. See [mcp.md](./mcp.md#available-tools).

## Gotchas

The [Rules](#rules) cover the failures that are silent or return a generic error. Two more:

- **Ingest reports partial failures rather than failing the call.** The response is
  `{"errors":[...],"total":N}` with a 200. Duplicates land in `errors` while the rest succeed, so
  check it instead of relying on the status code. Python's `add_users` returns `None` and Node types
  `addUsers` as `void`, so read the raw response:
  `const res = await client.bulk.addUsers(jobId, body).asResponse(); const { errors } = await res.json();`
  or `client.bulk.with_raw_response.add_users(job_id, users=[...]).json()`.
- **Global `message.data` merges into every recipient.** Put per-recipient values in `user.data`,
  which merges into it.

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

<a id="version-note"></a>

## Version note

Bulk has been missing from the API spec, and therefore from the generated SDKs and the reference
docs, in some releases. The REST endpoints serve traffic regardless.

If `client.bulk` is `undefined`, that is a version problem, not a missing feature. Upgrade, or call
the REST endpoints directly with the curl above. Verify method shapes against the installed
package's own types rather than this file, per
[Verifying Against Live Sources](../../SKILL.md#verifying-against-live-sources).

## Related

- [patterns.md](./patterns.md#lists-and-audience-sends): list and audience sends, the alternative to bulk
- [audiences.md](./audiences.md): dynamic segments, which fan out without a job
- [cli.md](./cli.md#lists-and-bulk): CLI equivalents and delivery debugging
- [reliability.md](./reliability.md): delivery statuses and retry semantics
- [Create a bulk job](https://www.courier.com/docs/api-reference/bulk/create-a-bulk-job) · [Send Bulk Notifications tutorial](https://www.courier.com/docs/guides/send-in-bulk)
