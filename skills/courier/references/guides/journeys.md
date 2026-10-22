# Journeys

Build multi-step notification workflows as code using directed acyclic graphs (DAGs). A journey is a sequence of nodes. Send, delay, branch, fetch, throttle, batch, add-to-digest, AI, and exit. That Courier executes asynchronously when you start the journey from an API invoke, a Segment event, an inbound webhook, or a user joining an audience.

> **Journeys is Courier's orchestration product. Use it for every multi-step flow.** If you have existing Automations, see [Coming from Automations](#coming-from-automations).

## Quick Reference

### Rules
- A journey must have at least one `trigger` node. It is the entry point for all runs
- `POST /journeys` takes a trigger node first and an exit node last, with no send nodes and no node `id`s
- Journey-scoped templates are **not** workspace templates. They live under `POST /journeys/{id}/templates` and cannot be referenced from the Send API or shared across journeys
- Journeys must be **published** before they can be invoked, draft changes are not executed
- `PUT /journeys/{id}` is a **full replacement** of the draft, include all nodes, not just the ones you changed
- End the top-level `nodes` with an `exit` node on create, and keep it last on every `PUT`, which takes the same body shape
- `POST /journeys/{id}/invoke` returns `202` with a `runId`, processing is asynchronous
- **Node `id`s are server-generated.** Do **not** send client-supplied node `id`s on `POST /journeys`. They're rejected with `400` (`client-supplied node ids are not allowed`). On `PUT /journeys/{id}` (replace) `id`s are accepted and preserved, but they're optional. Branch paths nest their child nodes inline, so you don't need `id`s to wire the graph, except to reference an earlier send in a `send_status.<nodeId>` condition.
- Elemental version string for journey-scoped templates is always `"2022-01-01"`. See [Elemental](./elemental.md)
- Delay durations use ISO 8601 format (e.g., `"PT1H"` for one hour, `"PT30M"` for 30 minutes, `"P1D"` for one day)
- Conditions use **string** tuples: `[path, operator, value]` for binary, `[path, operator]` for unary. A single condition is the bare tuple; multiple conditions use an `{ "AND": [...] }` / `{ "OR": [...] }` object. Comparison values are always strings (`"true"`, `"50"`), not native booleans/numbers. See [Conditions](#conditions)
- Interpolation differs by context: templates use `{{data.field}}` (a bare `{{field}}` resolves only in default scope); fetch URLs and header values use `{{field}}`; conditions use `data.field`. Fetch `headers` values are plain strings, e.g. `"Authorization": "Bearer {{api_token}}"`. See [Variable Interpolation](#variable-interpolation)
- A send node's `to` override takes **exactly one** of `email_override`, `phone_number_override`, `user_id_override`, `slack`, or `ms_teams` — never a combination. See [Slack and Teams sends](#slack-and-teams-sends)
- A Slack `access_token` on a send node must be a **runtime reference** (`{{data.slack_token}}`), never a literal token. See [Slack and Teams sends](#slack-and-teams-sends)
- A send node can carry `message.context.tenant_id` to deliver as one of your customers — literal id or whole-string mustache reference only. See [Send Node Options](#send-node-options)

### Common Mistakes
- Forgetting to publish after creating or updating the journey (invoke uses the last published version, not the draft)
- Referencing workspace template IDs (`nt_...`) in send nodes. Send nodes require journey-scoped template IDs created under `POST /journeys/{id}/templates`
- Creating send nodes before creating the journey-scoped templates they reference (the template must exist to wire its ID)
- Omitting the trigger node when replacing a journey via `PUT` (every journey needs at least one trigger)
- Using `POST /journeys/{id}/invoke` on an unpublished journey, returns an error; publish first
- Assuming the trigger `schema` rejects bad payloads at invoke. It does **not**. The `schema` powers editor autofill and variable hints only; missing fields are not rejected at invocation. A run proceeds until it reaches a node that references a missing field, then fails there. Use **trigger `conditions`** to gate invocation (a failed trigger condition returns `422`)
- Including `send` nodes in the `POST /journeys` body. Send nodes are **not allowed on create**. Create the shell (a trigger, then an exit), add templates, then add send nodes via `PUT /journeys/{id}`
- Wrapping a single condition in an extra array (`[[...]]`) or using non-string values, a single condition is a bare tuple of strings (`["data.plan", "is equal", "pro"]`); use an `{ "AND": [...] }` / `{ "OR": [...] }` object for multiple conditions
- Hardcoding a literal Slack bot token in `to.slack.access_token` — see [Slack and Teams sends](#slack-and-teams-sends)
- Addressing Teams by `channel_name`, `user_id`, or `email` without `service_url` or `tenant_id` — see [Slack and Teams sends](#slack-and-teams-sends)

### SDK shape, Journey management

> **Note:** The API reference uses `{templateId}` as the path parameter name for the journey ID. This is the journey's own ID (returned from `client.journeys.create`), not a notification template ID. This guide uses `{id}` for clarity.

Journey management is supported by the Node and Python SDKs and the CLI. Use the SDK in application code; use curl/CLI for ad-hoc work.

| Operation | Node | Python | CLI |
|-----------|------|--------|-----|
| Create | `client.journeys.create({ name, nodes, enabled })` | `client.journeys.create(name=..., nodes=..., enabled=...)` | `courier journeys create --name ... --node '{...}'` |
| List | `client.journeys.list()` | `client.journeys.list()` | `courier journeys list` |
| Retrieve | `client.journeys.retrieve(id)` | `client.journeys.retrieve(id)` | `courier journeys retrieve --template-id ID` |
| Replace (draft) | `client.journeys.replace(id, { name, nodes, enabled })` | `client.journeys.replace(id, name=..., nodes=...)` | `courier journeys replace --template-id ID ...` |
| Archive | `client.journeys.archive(id)` | `client.journeys.archive(id)` | `courier journeys archive --template-id ID` |
| List versions | `client.journeys.listVersions(id)` | `client.journeys.list_versions(id)` | `courier journeys list-versions --template-id ID` |
| Publish | `client.journeys.publish(id)` | `client.journeys.publish(id)` | `courier journeys publish --template-id ID` |
| Invoke | `client.journeys.invoke(id, { user_id, data, profile })` → `{ runId }` | `client.journeys.invoke(template_id=id, user_id=..., data=..., profile=...)` → `.run_id` | `courier journeys invoke --template-id ID --user-id user-123 --data '{...}'` |

### SDK shape, Journey-scoped templates

Journey-scoped template CRUD is available in the SDK under `client.journeys.templates.*`, in MCP, and over REST.

Argument order differs by method: `create` and `list` take the **journey** id first. Every other method takes the **template** id first, with the journey id as `templateId` in the params object.

| Operation | Node SDK | REST | MCP tool |
|-----------|----------|------|----------|
| Create | `client.journeys.templates.create(journeyId, body)` | `POST /journeys/{id}/templates` | `create_journey_template` |
| List | `client.journeys.templates.list(journeyId)` | `GET /journeys/{id}/templates` | `list_journey_templates` |
| Retrieve | `client.journeys.templates.retrieve(templateId, { ... })` | `GET /journeys/{id}/templates/{templateId}` | `get_journey_template` |
| Replace | `client.journeys.templates.replace(templateId, { ... })` | `PUT /journeys/{id}/templates/{templateId}` | `replace_journey_template` |
| Archive | `client.journeys.templates.archive(templateId, { ... })` | `DELETE /journeys/{id}/templates/{templateId}` | `archive_journey_template` |
| Publish | `client.journeys.templates.publish(templateId, { ... })` | `POST /journeys/{id}/templates/{templateId}/publish` | `publish_journey_template` |
| Get content | `client.journeys.templates.retrieveContent(templateId, { ... })` | `GET /journeys/{id}/templates/{templateId}/content` | `get_journey_template_content` |
| Put content | `client.journeys.templates.putContent(templateId, { ... })` | `PUT /journeys/{id}/templates/{templateId}/content` | `put_journey_template_content` |
| Put locale | `client.journeys.templates.putLocale(localeId, { ... })` | `PUT .../locales/{localeId}` | `put_journey_template_locale` |
| List versions | `client.journeys.templates.listVersions(templateId, { ... })` | `GET /journeys/{id}/templates/{templateId}/versions` | `list_journey_template_versions` |

**Reading a draft.** There is no `/draft/content` route on journey-scoped templates (it returns **404**). Use the `version` query parameter:

| Want | Route |
|---|---|
| Published content | `GET /journeys/{jid}/templates/{tid}/content` |
| Draft content | `GET /journeys/{jid}/templates/{tid}/content?version=draft` |
| A specific version | `GET /journeys/{jid}/templates/{tid}/content?version=v001` |

`putLocale` on a journey template takes the same `elements` body as on a workspace template, with `templateId` (the journey) and `notificationId` as parameters; see [localization.md](./localization.md#journey-templates).

`?version=` works the same way on workspace templates (`GET /notifications/{id}/content?version=draft`) and reads any published version on either.

Workspace templates under `/notifications` are a separate namespace with their own full SDK support. See [templates.md](./templates.md).

---

## Concepts

### Journey Structure

A journey is a directed acyclic graph (DAG) of nodes. Each node performs one action (send a notification, wait, branch, fetch data, throttle, run an LLM prompt, or exit), and the array order defines execution sequence.

```
[Trigger] → [Send Welcome] → [Delay 1 day] → [Branch: setup complete?]
                                                   ├─ Yes → [Send Success] → [Exit]
                                                   └─ No  → [Send Reminder] → [Delay 2 days] → [Send Nudge] → [Exit]
```

### Triggers

Every journey starts with a trigger node. The API accepts four `trigger_type` values:

| Trigger type | How runs begin | Required fields |
|-------------|----------------|-----------------|
| `api-invoke` | You call `POST /journeys/{id}/invoke` | None beyond discriminators. Optional: `schema` (JSON Schema for editor autofill/variable hints, **not** invoke-time validation), `conditions` (gate invocation; failed condition → `422`). |
| `segment` | A matching Segment event arrives | `request_type` (`identify`, `group`, `track`, or `page`). Optional: `event_id`, `conditions`. With no `event_id` it fires on every event of that type. For `track` events, the event `userId` must be a valid Courier Profile ID or the journey won't start. |
| `webhook` | An event arrives on one of your [inbound webhooks](./webhooks.md#inbound-webhooks) | `event_source`. Optional: `event_id`, matched against the payload's `event`, and `conditions`. Every payload needs a `userId` matching a Courier user. |
| `audience` | A user newly matches an [audience](./audiences.md) | `audience_id` (one audience). Optional: `conditions`. Users already in the audience when you publish don't enter. |

Webhook and audience triggers take no `schema`.

### Journey-Scoped vs Workspace Templates

| | Journey-scoped | Workspace |
|--|----------------|-----------|
| Created via | `POST /journeys/{id}/templates` | `POST /notifications` or Design Studio |
| Used from | Send nodes within the journey | Send API (`client.send.message`) |
| Shareable | No, exclusive to one journey | Yes, any send can reference them |
| Content format | [Elemental](./elemental.md) (`version` + `elements`) | Elemental or Design Studio |
| Publishable | Independently (`state: "PUBLISHED"` on create, or `.../publish`) | Via `notifications.publish` |

Publish each journey-scoped template yourself. Create it with `"state": "PUBLISHED"`, or call `POST /journeys/{id}/templates/{templateId}/publish` after an edit. A run sends each template's published version, so don't rely on publishing the journey to publish its templates.

**Editing content does not change what the journey sends.** A journey-scoped template versions independently, so `PUT .../content` alone leaves the journey delivering the previously published version with nothing in the journey to indicate an edit is pending. Publish the template to make the edit live. `GET .../versions` shows the mismatch while it lasts:

```json
{
  "paging": { "more": false },
  "versions": [
    { "version": "draft", "has_changes": true, "created": 1755561339147, "creator": "user-123" },
    { "version": "published:v001", "created": 1755559277705, "creator": "user-123" }
  ]
}
```

`has_changes` appears only on the draft entry. `versions` is ordered by `created` (epoch ms), not by version number, so a `v002` can follow a `published:v003`. Sort on `created`.

If you need a template reusable across journeys or callable from the Send API, use a workspace template. If the template is specific to one journey, keep it scoped.

---

## Standard Workflow

Every journey follows the same five-step process: create the shell, add templates, wire them into the DAG, publish, and invoke.

### Step 1: Create the journey shell

Create a journey with a name, a trigger node, and an exit node last.

```bash
curl -sS -X POST "https://api.courier.com/journeys" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome Journey",
    "nodes": [
      {
        "type": "trigger",
        "trigger_type": "api-invoke",
        "schema": {
          "type": "object",
          "properties": {
            "first_name": { "type": "string" },
            "company_name": { "type": "string" },
            "dashboard_url": { "type": "string" }
          },
          "required": ["first_name"]
        }
      },
      { "type": "exit" }
    ],
    "enabled": true
  }'
```

> Do **not** include client-supplied node `id`s on create, the server generates them (and returns `400` if you send your own). `send` nodes are not allowed on `POST /journeys` either. Create the shell with a trigger node, and an exit node last (other non-send nodes can go between them); add send nodes later via `PUT` once their templates exist. To publish immediately on create, pass `"state": "PUBLISHED"` (defaults to `"DRAFT"`).

Create returns `201` with the journey. The response echoes back **server-generated** node `id`s (e.g. `"PK5BA6NV424BAYN58R6CVM2GTH10"`). Save the top-level journey `id`. You'll use it in every subsequent request:

```json
{
  "id": "3ac3b1ba-5910-4954-9871-99e601d77bb8",
  "name": "Welcome Journey",
  "cancelation_token": null,
  "state": "DRAFT",
  "enabled": true,
  "nodes": [
    { "id": "PK5BA6NV424BAYN58R6CVM2GTH10", "type": "trigger", "trigger_type": "api-invoke" },
    { "id": "QX7CB2MW535CBZP69S7DWN3HUJ21", "type": "exit" }
  ],
  "created": 1715000000000,
  "creator": null,
  "updated": 1715000000000,
  "updater": null,
  "published": null
}
```

### Step 2: Create journey-scoped templates

Create the notification templates your send nodes will reference. Content uses [Elemental](./elemental.md) format, wrapped in a `channel` element that matches the template's `channel` so it displays and edits properly in Courier.

```bash
JOURNEY_ID="<id from step 1>"

curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/templates" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "state": "PUBLISHED",
    "notification": {
      "name": "Welcome Email",
      "tags": [],
      "brand": null,
      "subscription": null,
      "content": {
        "version": "2022-01-01",
        "elements": [
          {
            "type": "channel",
            "channel": "email",
            "elements": [
              { "type": "meta", "title": "Welcome to {{company_name}}, {{first_name}}!" },
              { "type": "text", "content": "Hi {{first_name}}, thanks for signing up. We are excited to have you on board." },
              { "type": "text", "content": "Here are a few things to get you started:" },
              { "type": "action", "content": "Go to your dashboard", "href": "{{dashboard_url}}" }
            ]
          }
        ]
      }
    }
  }'
```

Save the template `id` from the response.

### Step 3: Wire templates into the journey

Replace the journey draft with your full node graph, referencing template IDs from step 2.

```bash
TEMPLATE_ID="<id from step 2>"

curl -sS -X PUT "https://api.courier.com/journeys/$JOURNEY_ID" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome Journey",
    "nodes": [
      {
        "id": "trigger-1",
        "type": "trigger",
        "trigger_type": "api-invoke",
        "schema": {
          "type": "object",
          "properties": {
            "first_name": { "type": "string" },
            "company_name": { "type": "string" },
            "dashboard_url": { "type": "string" }
          },
          "required": ["first_name"]
        }
      },
      {
        "id": "send-welcome",
        "type": "send",
        "message": {
          "template": "'"$TEMPLATE_ID"'"
        }
      },
      { "id": "exit-1", "type": "exit" }
    ],
    "enabled": true
  }'
```

### Step 4: Publish

Lock in the current draft as a versioned snapshot. All new runs execute against the published version.

```bash
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/publish" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json"
```

### Step 5: Invoke

Start a run. The journey must be **published** first. You can invoke by journey **ID or alias**. Provide **either** `user_id` **or** a `profile` with contact info (Courier can also resolve the recipient from `user_id`/`userId`/`anonymousId` inside `profile` or `data`). Returns `202` with a `runId`. Courier processes the run asynchronously, walking through the DAG. The `runId` is what you look up in the journey's Logs tab or `journeys.runs.retrieve`.

```json
{ "runId": "1-65f240a0-47a6a120c8374de9bcf9f22c" }
```

> **Tip:** If any downstream `fetch` node references `{{user_id}}` in its URL, also include `user_id` inside `data`, the top-level `user_id` is used for recipient resolution, but Courier does not guarantee it is projected into `data` for variable interpolation. Passing it both places is the safe default.

**Recipient resolution & profiles:**
- **Profile-only** (no stored Courier user): pass `profile` with contact info and omit `user_id`.
- **Profile merge:** when you pass both `user_id` and `profile`, request fields override stored profile fields with the same key; other stored fields are preserved.
- **Tenant-scoped profile** (multi-tenant): pass `profile.context.tenant_id` to load the user's tenant-scoped profile:

```json
{
  "user_id": "doctor-smith",
  "profile": { "context": { "tenant_id": "hospital-a" } },
  "data": { "report_date": "2026-01-15" }
}
```

**Node:**
```typescript
const { runId } = await client.journeys.invoke(JOURNEY_ID, {
  user_id: "user_abc123",
  profile: { email: "alice@example.com" },
  data: {
    user_id: "user_abc123", // mirror for fetch URL templating
    first_name: "Alice",
    company_name: "Acme Corp",
    dashboard_url: "https://app.acme.com/dashboard",
  },
});
```

**Python:**
```python
response = client.journeys.invoke(
    template_id=JOURNEY_ID,
    user_id="user_abc123",
    profile={"email": "alice@example.com"},
    data={
        "user_id": "user_abc123",
        "first_name": "Alice",
        "company_name": "Acme Corp",
        "dashboard_url": "https://app.acme.com/dashboard",
    },
)
run_id = response.run_id
```

**curl:**
```bash
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/invoke" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_abc123",
    "profile": { "email": "alice@example.com" },
    "data": {
      "user_id": "user_abc123",
      "first_name": "Alice",
      "company_name": "Acme Corp",
      "dashboard_url": "https://app.acme.com/dashboard"
    }
  }'
```

---

## Node Types Reference

### Summary

| Node type | Description |
|-----------|-------------|
| `trigger` | Entry point. Discriminated by `trigger_type`: `api-invoke`, `segment`, `webhook`, or `audience`. |
| `send` | Send a notification using a journey-scoped template. References the template via `message.template`. Delivers on any configured channel: email, SMS, push, inbox, Slack, or Microsoft Teams. |
| `delay` | Pause the run. Discriminated by `mode`: `duration` (ISO 8601) or `until` (timestamp). |
| `fetch` | Make an HTTP request and merge the response into run state. Discriminated by `method`: `get`, `delete`, `post`, or `put`. |
| `branch` | Conditional routing. Evaluates `paths[]` in order and routes to the first match, with a `default` fallback. |
| `throttle` | Rate-limit runs. Discriminated by `scope`: `user`, `global`, or `dynamic`. |
| `batch` | Collect multiple events into one aggregated payload, then fire one downstream step. Releases on `max_items`, a quiet `wait_period`, or the `max_wait_period` ceiling. |
| `add-to-digest` | Add the event to a digest keyed by a subscription topic; the digest releases on the topic's configured schedule. |
| `ai` | Run an LLM prompt with optional web search. Returns structured output per `output_schema`. |
| `exit` | End the run immediately. |
| Cancel *(builder only)* | Cancels every **other** active run sharing a cancelation token, not its own run. Not in the API journey schema; from code, call `POST /journeys/cancel`. See [Cancelling Runs](#cancelling-runs). |

### Detailed Reference

| Type | Discriminator | Required fields |
|------|--------------|-----------------|
| Trigger (API) | `type: "trigger"`, `trigger_type: "api-invoke"` | None beyond discriminators. Optional: `id`, `schema`, `conditions`. |
| Trigger (Segment) | `type: "trigger"`, `trigger_type: "segment"` | `request_type` (`identify`, `group`, `track`, or `page`). Optional: `event_id`, `conditions`. |
| Trigger (Webhook) | `type: "trigger"`, `trigger_type: "webhook"` | `event_source`. Optional: `id`, `event_id`, `conditions`. |
| Trigger (Audience) | `type: "trigger"`, `trigger_type: "audience"` | `audience_id`. Optional: `id`, `conditions`. |
| Send | `type: "send"` | `message.template` (journey-scoped template ID), or an [`experiment`](#ab-experiments-on-a-send-node) beside `message` instead. Optional: `message.to` (recipient override: `email_override`, `phone_number_override`, `user_id_override`, `slack`, or `ms_teams`, exactly one), `message.context` (tenant context), `message.delay`, `message.data`, `channel` (optional label enum, no routing effect, see [Slack and Teams sends](#slack-and-teams-sends)), `conditions`. |
| Delay (duration) | `type: "delay"`, `mode: "duration"` | `duration` (ISO 8601 duration string, e.g. `"PT30M"`). Optional: `conditions`. |
| Delay (until) | `type: "delay"`, `mode: "until"` | `until` (ISO 8601 timestamp or context reference). Optional: `conditions`. |
| Fetch (GET/DELETE) | `type: "fetch"`, `method: "get"` or `"delete"` | `url`, `merge_strategy`. Optional: `headers`, `query_params`, `response_schema`, `conditions`. |
| Fetch (POST/PUT) | `type: "fetch"`, `method: "post"` or `"put"` | `url`, `merge_strategy`. Optional: `body`, `headers`, `query_params`, `response_schema`, `conditions`. |
| Branch | `type: "branch"` | `paths[]` (each with `conditions` and `nodes[]`), `default` (with `nodes[]`). Optional: `paths[].label`, `default.label`. |
| Throttle (static) | `type: "throttle"`, `scope: "user"` or `"global"` | `max_allowed`, `period`. Optional: `conditions`. |
| Throttle (dynamic) | `type: "throttle"`, `scope: "dynamic"` | `max_allowed`, `period`, `throttle_key`. Optional: `conditions`. |
| Batch | `type: "batch"`, `scope: "user"` | `wait_period` (ISO 8601 quiet window), `max_wait_period` (ISO 8601 hard ceiling; must be > `wait_period`), `retain` (`{ type: "first"\|"last"\|"highest"\|"lowest", count: 0–25, sort_key }`; `sort_key` required for `highest`/`lowest`). Optional: `max_items` (1–1000, default 100), `category_key` (partition key, ≤256 chars), `conditions`. |
| Send to Digest | `type: "add-to-digest"` | `subscription_topic_id`. Optional: `conditions`. |
| AI | `type: "ai"` | `output_schema` (JSON Schema for the structured result). Optional: `model`, `user_prompt`, `web_search`, `conditions`. |
| Exit | `type: "exit"` | None. Optional: `id`. |

---

## Conditions

Several node types (`branch` paths, `send`, `delay`, `fetch`, `throttle`, triggers, …) support a `conditions` field. A condition's elements are **always strings**, compare against `"true"`/`"false"` and `"50"`, never native booleans or numbers.

The `conditions` field accepts one of three shapes:

**1. A single condition (bare tuple).** Binary is `[path, operator, value]`; unary is `[path, operator]`:

```json
"conditions": ["data.plan", "is equal", "pro"]
```

```json
"conditions": ["data.email", "exists"]
```

> Do **not** wrap a single condition in an extra array (`[[...]]`). That is not a valid shape.

**2. A group (AND/OR).** An object with exactly one of `AND` or `OR`, each a list of 2+ condition tuples:

```json
"conditions": {
  "AND": [
    ["data.is_first_order", "is equal", "true"],
    ["data.order_total", "greater than", "50"]
  ]
}
```

**3. A nested group.** An object with `AND`/`OR` whose entries are themselves groups, e.g. "first-time buyer over $50 **OR** returning buyer over $200":

```json
"conditions": {
  "OR": [
    { "AND": [["data.is_first_order", "is equal", "true"], ["data.order_total", "greater than", "50"]] },
    { "AND": [["data.is_first_order", "is equal", "false"], ["data.order_total", "greater than", "200"]] }
  ]
}
```

### Available Operators

| Type | Operators |
|------|-----------|
| Binary | `is equal`, `is not equal`, `contains`, `does not contain`, `starts with`, `ends with`, `greater than`, `greater than or equal`, `less than`, `less than or equal` |
| Unary | `exists`, `does not exist` |
| Send status | `was`, `was not` |

### Branching on an earlier send

`was` and `was not` compare `send_status.<nodeId>` against `SENT`, `DELIVERED`, `OPENED`, `CLICKED`, or
`UNDELIVERABLE`, where `<nodeId>` is an earlier send node's id. The first four are cumulative, so
`was DELIVERED` is also true once the message was opened or clicked. `UNDELIVERABLE` matches only itself.

Send nodes can't be added on create, so the safe order is two `PUT`s: add
the email send node, read its `id` from that response, then `PUT` again with the delay and branch.
`PUT` is a full replacement, so the second one repeats every node, trigger included. Escalate to SMS when an email is not clicked within a day. Key on `CLICKED`, not `OPENED`, because image-proxy prefetch fires opens nobody saw. `CLICKED` needs click tracking on and a tracked link in the message; without them the condition is always true and everyone gets the SMS:

The `nodes` of the second `PUT`:

```json
[
  { "id": "trigger-1", "type": "trigger", "trigger_type": "api-invoke" },
  { "id": "P9Z3VCRJG647M7QNJZR3548HW741", "type": "send", "message": { "template": "<email-template-id>" } },
  { "type": "delay", "mode": "duration", "duration": "P1D" },
  {
    "type": "branch",
    "paths": [
      {
        "label": "Email not clicked",
        "conditions": ["send_status.P9Z3VCRJG647M7QNJZR3548HW741", "was not", "CLICKED"],
        "nodes": [{ "type": "send", "message": { "template": "<sms-template-id>" } }]
      }
    ],
    "default": { "nodes": [] }
  },
  { "type": "exit" }
]
```

Condition paths reference the journey context: `data.*` (invocation `data` + merged fetch responses), `profile.*`, and `user.*`.

---

## Variable Interpolation

How you reference a context value depends on **where** you use it. Getting this wrong is the most common journey bug:

| Context | Syntax | Example |
|---------|--------|---------|
| Template content (Elemental) | `{{data.field}}` works in both scopes. A bare `{{field}}` resolves only in default-scope templates (API-created with no `scope`). Design Studio templates are `scope: "strict"`, so read `content.scope` before editing one. Digest totals are the exception, see [digests.md](./digests.md) | `"Welcome, {{data.first_name}}!"` |
| Fetch node `url` | `{{field}}` | `"https://api.app.com/users/{{user_id}}/status"` |
| Branch / trigger `conditions` | `data.field` (string tuples) | `["data.completed", "is equal", "true"]` |
| Fetch **header values** | `{{field}}` inside a plain string | `{ "Authorization": "Bearer {{api_token}}" }` |
| Send node `to.slack` / `to.ms_teams` / `context.tenant_id` values | `{{field}}` as the **whole string** | `"access_token": "{{data.slack_token}}"` |

Notes:
- `user_id` passed at the top level of an invoke is used for **recipient resolution** and is not guaranteed to be projected into `data`. If a fetch URL or template needs it, declare `user_id` in the trigger schema and pass it inside `data` too.
- Fetch responses are merged into the context (per `merge_strategy`) and are then referenced like any other field: `data.field` in conditions, `{{field}}` in templates.
- There is **no `{{secrets.*}}` namespace.** Pass credentials via `data`/`profile` and interpolate them into the header string with `{{field}}`, or store them in the provider/workspace settings.

---

## Merge Strategies (Fetch Nodes)

When a fetch node receives a response, `merge_strategy` determines how the response is incorporated into run state. **`soft-merge` is the safest default**. It never overwrites trigger schema or profile fields.

| Strategy | Behavior |
|----------|----------|
| `soft-merge` (recommended default) | Adds new fields from the response without overwriting existing values. |
| `overwrite` | Deep-merges response into state. Response values overwrite existing fields with the same key. |
| `replace` | Replaces the entire run state with the response. |
| `none` | Doesn't merge into existing context. If the run's context is empty, the response is used. |

Fetch nodes require **HTTPS** URLs. If a fetch fails (network error or non-2xx), the journey **continues** and no data is merged, guard downstream nodes with conditions like `["data.expected_field", "exists"]`.

---

## Examples

### Delay, Fetch, Branch, and Exit Nodes

The [Standard Workflow](#standard-workflow) covers the trigger, journey-scoped templates, and send nodes. This journey adds the rest: a `delay`, a `fetch` that merges an HTTP response into run state, a `branch` on that data, and `exit` nodes that end the run early.

```bash
curl -sS -X PUT "https://api.courier.com/journeys/$JOURNEY_ID" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Onboarding Sequence",
    "nodes": [
      {
        "id": "trigger-1",
        "type": "trigger",
        "trigger_type": "api-invoke",
        "schema": {
          "type": "object",
          "properties": {
            "user_name": { "type": "string" },
            "signup_date": { "type": "string" }
          },
          "required": ["user_name"]
        }
      },
      {
        "id": "send-welcome",
        "type": "send",
        "message": { "template": "<welcome-template-id>" }
      },
      {
        "id": "wait-1-day",
        "type": "delay",
        "mode": "duration",
        "duration": "P1D"
      },
      {
        "id": "check-setup",
        "type": "fetch",
        "method": "get",
        "url": "https://api.yourapp.com/users/{{user_id}}/setup-status",
        "merge_strategy": "soft-merge",
        "headers": { "Authorization": "Bearer {{app_api_token}}" }
      },
      {
        "id": "branch-setup",
        "type": "branch",
        "paths": [
          {
            "label": "Setup complete",
            "conditions": ["data.setup_complete", "is equal", "true"],
            "nodes": [
              {
                "id": "send-success",
                "type": "send",
                "message": { "template": "<success-template-id>" }
              },
              { "id": "exit-success", "type": "exit" }
            ]
          }
        ],
        "default": {
          "label": "Setup incomplete",
          "nodes": [
            {
              "id": "send-reminder",
              "type": "send",
              "message": { "template": "<reminder-template-id>" }
            },
            {
              "id": "wait-2-days",
              "type": "delay",
              "mode": "duration",
              "duration": "P2D"
            },
            {
              "id": "send-nudge",
              "type": "send",
              "message": { "template": "<nudge-template-id>" }
            },
            { "id": "exit-default", "type": "exit" }
          ]
        }
      },
      { "id": "exit-end", "type": "exit" }
    ],
    "enabled": true
  }'
```

Every field is in the [Node Types Reference](#node-types-reference).

### Throttle Node and Send Conditions

Rate-limit re-engagement per user, and gate a send on run data:

```json
{ "id": "throttle-user", "type": "throttle", "scope": "user", "max_allowed": 1, "period": "P30D" }
```

```json
{
  "id": "send-last-chance",
  "type": "send",
  "message": { "template": "<last-chance-template-id>" },
  "conditions": ["data.user_tier", "is equal", "high-value"]
}
```

### Send Node Options

A send node's `message` can do more than reference a template:

```json
{
  "type": "send",
  "message": {
    "template": "<template-id>",
    "to": { "email_override": "billing@acme.com" },
    "context": { "tenant_id": "{{data.tenant_id}}" },
    "delay": { "until": "{{send_at}}", "timezone": "America/New_York" },
    "data": { "invoice_url": "{{invoice_url}}" }
  }
}
```

- `to`, override the resolved recipient. **Exactly one** of `email_override`, `phone_number_override`, `user_id_override`, `slack`, or `ms_teams` — never a combination. See [Slack and Teams sends](#slack-and-teams-sends) for the `slack`/`ms_teams` shapes.
- `context.tenant_id`, deliver this send as one of your customers so the message uses that tenant's brand and settings. A literal id, or a whole-string mustache reference resolved per run (`{{data.tenant_id}}`, or `{{f1.body.tenant_id}}` from the fetch node with id `f1`), so one journey serves every tenant. Mid-string interpolation and `refs.`-prefixed values are `400`s; an unresolved reference sends **without** tenant context rather than failing the run. See [tenants.md](./tenants.md).
- `delay`, schedule this individual send: `until` (required, ISO 8601 timestamp or context reference) plus optional `timezone`. (For pausing the whole run, use a `delay` node instead.)
- `data`, extra merge data scoped to this send.

A send node can also carry `channel` **outside** `message`:

```json
{ "id": "n1", "type": "send", "message": { "template": "<template-id>" }, "channel": "inbox" }
```

The journey designer writes this field, so designer-built journeys have it and hand-written ones usually don't. **It is a label for analytics and reporting, not routing.** Setting it does not make a send go to that channel, and omitting it does not stop delivery. To control the delivery channel, set `channel` on the journey-scoped template (`POST /journeys/{id}/templates`) or attach a routing strategy. See [the channel element vs the three other places a channel is named](./elemental.md#the-channel-element-vs-the-three-other-places-a-channel-is-named).

### Slack and Teams Sends

Journeys can deliver to Slack and Microsoft Teams. The send node's `to` override addresses them directly, bypassing the recipient's stored profile:

**Slack** (`to.slack`) — exactly one destination: `channel`, `user_id` (Slack user ID), or `email` (resolved via the workspace directory). For `channel`, use the channel ID (`C...`): the API accepts a name and passes it through to Slack, but names only resolve for channels the bot can see — a name that doesn't resolve fails at delivery with `channel_not_found`.

```json
{
  "type": "send",
  "message": {
    "template": "<slack-template-id>",
    "to": {
      "slack": {
        "channel": "C012AB3CD",
        "access_token": "{{data.slack_token}}"
      }
    }
  }
}
```

- `access_token` must be a **runtime reference** like `{{data.slack_token}}` (a whole-string reference to a value the run holds). Literal `xoxb-...` values are rejected — they'd be stored permanently in the journey definition with no way to rotate them. `{{data...}}` references are the only attested form; for per-customer tokens, prefer the omission route below.
- Omit `access_token` to use the token on the recipient's stored Slack profile. In a multi-tenant app, store one bot token per customer on the tenant's `user_profile`, send with `context.tenant_id`, and each run picks up the right workspace through the profile merge ([tenants.md](./tenants.md#hierarchy-and-merging)).
- Unlike email/SMS/push, Slack has no journey user to fall back on for the destination — always set `channel`, `user_id`, or `email` on the node.

**Microsoft Teams** (`to.ms_teams`) — exactly one target: `channel_id` (Bot Framework channel ID), `channel_name` **with** `team_id`, `user_id`, or `email`.

```json
{
  "type": "send",
  "message": {
    "template": "<teams-template-id>",
    "to": {
      "ms_teams": {
        "user_id": "{{data.teams_user_id}}",
        "service_url": "https://smba.trafficmanager.net/amer",
        "tenant_id": "{{data.microsoft_tenant_id}}"
      }
    }
  }
}
```

- `channel_name`, `user_id`, and `email` targets need at least one of `service_url` (the regional Bot Framework host) or `tenant_id` (the Microsoft/Azure AD tenant); supply both and they must agree.
- `channel_id` publishes without either, but sends with neither have failed at delivery — provide `service_url` or `tenant_id` anyway.
- `ms_teams.tenant_id` is the **Microsoft** tenant, unrelated to `message.context.tenant_id`, which is your own Courier multi-tenant context.
- `conversation_id` and `reply_to_activity_id` from the send API's Teams profile are **not** supported on journey send nodes.

**Templates and the two `channel` fields.** Message content comes from a journey-scoped template like any other channel. `POST /journeys/{id}/templates` takes `channel` as an open string that participates in routing — it accepts channel keys and provider-key forms (`slack`, `msteams`, or `provider:alias`), plus an optional `providerKey` field. Separately, the send **node** itself takes an optional flat `channel` field with a closed enum — `email` | `sms` | `push` | `inbox` | `slack` | `msteams` — a label that makes the node's channel explicit to clients reading the journey; it does not affect routing, is never checked for consistency against the template's channel, and is absent from `GET` responses when unset. Don't confuse the two: the template's channel routes, the node's channel labels. Block Kit, Adaptive Cards, threading, and provider setup live in the channel guides: [slack.md](../channels/slack.md), [ms-teams.md](../channels/ms-teams.md).

### A/B Experiments on a Send Node

A/B testing is a field on the send node, **not** a separate node type. Put `experiment` on the node, beside `message`, **instead of** `message.template`. Each recipient is bucketed by `bucketingKey` and routed to one variant in proportion to its `weight`.

```json
{
  "type": "send",
  "message": {},
  "experiment": {
    "name": "Welcome subject line test",
    "bucketingKey": "user.id",
    "variants": [
      { "id": "control", "name": "Direct",    "templateId": "<template-id-a>", "weight": 50 },
      { "id": "variant", "name": "Curiosity", "templateId": "<template-id-b>", "weight": 50 }
    ]
  }
}
```

- **`message`** (required), may be `{}` when `experiment` is present. `message.to`, `message.delay`, and `message.data` still apply to whichever variant is chosen.
- **`bucketingKey`** (required), a path to a value in the run, such as `user.id`, `user.email`, or `data.account_id`, not a literal. Courier hashes the value at that path, so the same recipient always lands in the same variant. If the path doesn't resolve, it falls back to the user ID, then the email. Assignments are sticky across sends, even if you change the weights later. Adding or removing a variant, or changing the bucketing key, re-buckets everyone.
- **`variants`** (required), between 2 and 10. Each needs `id`, `templateId` (a journey-scoped template), and `weight`. Variant `id`s must be unique within the experiment; weights are **relative** (no sum-to-100 requirement) and their total must be greater than 0, routing normalizes proportionally.
- **`id`** (optional), an `exp_`-prefixed experiment id. Omit to have one generated; if you supply it, it must be a valid `exp_` id.
- ⚠️ **`bucketingKey` and `templateId` are camelCase**, unlike the snake_case used elsewhere in the Journeys API. Copy them exactly.

### Dynamic Delay

A `delay` node's interval can come from the journey context instead of a hardcoded value. Pass a context reference in `duration` (an ISO 8601 duration like `PT2H`) or `until` (a timestamp):

```json
{ "type": "delay", "mode": "duration", "duration": "{{follow_up_delay}}" }
```

### Batch Node

Collect multiple invocations for the same user into one aggregated payload, then fire one downstream send. Releases when any of: `max_items` reached, the quiet `wait_period` elapses with no new events, or the `max_wait_period` ceiling hits.

```json
{
  "type": "batch",
  "scope": "user",
  "wait_period": "PT10M",
  "max_wait_period": "PT1H",
  "max_items": 50,
  "category_key": "data.project_id",
  "retain": { "type": "highest", "count": 5, "sort_key": "data.priority" }
}
```

- `retain.type`, which collected events to keep: `first`, `last`, `highest`, or `lowest` (the latter two require `sort_key`). `count` is 0–25.
- `category_key`, events sharing this value batch together; different values batch separately.

### Send to Digest Node

Add the event to a subscription topic's digest. The topic controls the schedule, categories, and digest template, not the journey. If the topic has no digest template when the first event arrives, the run is marked `ERROR` and stops. Runs scoped to different tenants collect separate digests. Setup is in [digests.md](./digests.md):

```json
{ "type": "add-to-digest", "subscription_topic_id": "<topic-id>" }
```

### AI Node

Run an LLM prompt and merge a structured result (conforming to `output_schema`) into the journey context for downstream branching:

```json
{
  "type": "ai",
  "model": "gpt-5.4-mini",
  "user_prompt": "Classify this support message intent: {{message_body}}",
  "web_search": false,
  "output_schema": {
    "type": "object",
    "properties": {
      "intent": { "type": "string" },
      "urgency": { "type": "string" }
    },
    "required": ["intent"]
  }
}
```

`web_search` works only with the `claude-*` models and costs 2 extra credits per run. Use a model id from the [AI node's model list](https://www.courier.com/docs/journeys/nodes/ai#ai-model). Unknown ids may return `400`.

### Segment-Triggered Journey

Instead of `api-invoke`, start runs from your Segment event stream. Filter which events qualify with trigger `conditions`. The `PUT /journeys/{id}` body, after you create the shell and its template:

```json
{
  "name": "High-Value Order Follow-Up",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger",
      "trigger_type": "segment",
      "request_type": "track",
      "event_id": "Order Completed",
      "conditions": ["properties.total", "greater than", "100"]
    },
    { "id": "send-thanks", "type": "send", "message": { "template": "<thanks-template-id>" } },
    { "type": "exit" }
  ],
  "enabled": true
}
```

For `track` events, the event's `userId` must be a valid Courier Profile ID or the journey won't start. Segment journeys have no `schema`. Courier receives whatever Segment sends.

A Segment trigger's own `conditions` read the Segment event, so their paths start at `properties.` (`properties.total`). After the trigger, those properties are the run's `data`, so later nodes use `data.total`.

---

## Errors & Status Codes

| Endpoint | Success | Error statuses |
|----------|---------|----------------|
| `POST /journeys` | `201` (journey) | `400`, `404`, `422` |
| `POST /journeys/{id}/invoke` | `202` (`{ runId }`) | `400`, `404`, `422` |

Error bodies have the shape `{ "type": "...", "message": "..." }`. Common **create** (`POST /journeys`) errors:

| Status | `type` | Cause / message |
|--------|--------|-----------------|
| `400` | `invalid_request_error` | Client-supplied node `id`s (`client-supplied node ids are not allowed; ids are server-generated`) |
| `400` | `invalid_request_error` | Malformed condition (`nodes.N.paths.M.conditions: Invalid input`), e.g. `[[...]]` wrapping or non-string values |
| `422` | `validation_error` | `send` node in the create body (`send nodes are not allowed at journey creation; create the journey, then create notification templates scoped to it, then PUT to wire the send nodes`) |

Common **invoke** (`POST /journeys/{id}/invoke`) errors:

| Status | Cause | Example message |
|--------|-------|-----------------|
| `400` | Missing recipient | `User identifier or profile required. Provide user_id, ... or profile with contact info.` |
| `404` | Journey not found / not published | `Automation template abc-123 not found` |
| `422` | Trigger conditions not met | `Trigger conditions not met` |
| `422` | Journey archived | `Cannot invoke archived automation template abc-123` |
| `422` | Journey disabled (`enabled: false`) | `Cannot invoke disabled automation template abc-123` |

## Cancelling Runs

Journeys support cancellation two ways: **externally** via the API, and **from inside a flow** via the Cancel node. Both work off the same concept, a **cancelation token** shared by a family of runs.

### The cancelation token

The token is a journey-level field, `cancelation_token`, set on `POST /journeys` or `PUT /journeys/{id}`, or in the journey's settings in the designer. It is templated from run data, `{{data.…}}`, `{{profile.…}}`, or `{{recipient}}`, such as `order-{{data.order_id}}`, which gives every run for one order a shared handle. A `PUT` that leaves it out keeps the existing token.

```json
{
  "name": "Order reminders",
  "cancelation_token": "order-{{data.order_id}}",
  "nodes": [
    { "type": "trigger", "trigger_type": "api-invoke" },
    { "type": "exit" }
  ]
}
```

> ⚠️ **If the referenced variable doesn't resolve when the run starts, the run is created with no token, and can never be cancelled by token.** Only `run_id` cancellation will reach it. Make sure the fields your token references are always present in the invoke payload.

### Externally: `POST /journeys/cancel`

Provide **exactly one** of `cancelation_token` or `run_id`, both, or neither, is rejected.

| Body | Cancels | Returns (`202`) |
|------|---------|-----------------|
| `{ "cancelation_token": "order-4821" }` | **Every** active run sharing that token | `{ cancelation_token }` |
| `{ "run_id": "<runId>" }` | A single tenant-scoped run | `{ run_id, status }` |

```bash
# Your app learns the order shipped — kill the whole reminder ladder
curl -sS -X POST "https://api.courier.com/journeys/cancel" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "cancelation_token": "order-4821" }'
```

```typescript
await client.journeys.cancel({ cancelation_token: "order-4821" });
```

Use the **token** when one real-world event should stop a whole family of runs (order shipped, trial converted, user unsubscribed). Use **`run_id`** when you're cancelling one specific run you hold the id for.

### From inside a flow: the Cancel node

A **Cancel** node stops in-flight runs from within a journey. Its one setting is a Cancelation Token.

> ⚠️ **A Cancel node does not cancel its own run.** When a run reaches the node, Courier cancels **every *other* active run sharing that token**, the run containing the node continues to the next node. Use an `exit` node to end the current run.

This is the pattern for "the newest run wins": a re-engagement journey whose first node cancels any earlier run for the same user, so a returning user doesn't receive two overlapping sequences.

The Cancel node is configured in the journey builder. It is **not currently part of the API journey definition**, there is no `cancel` node `type` in the published OpenAPI schema, so you cannot add one via `POST /journeys` or `PUT /journeys/{id}`. Building journeys as code? Call `POST /journeys/cancel` from your application at the equivalent point instead. It has the same token semantics.

## Debugging Runs

Every invoke returns a `runId`. Open the journey's **Logs** tab to see a run on the journey canvas: which nodes ran and in what order, which path each branch took, where a waiting run is paused, and which node failed. Start here when a journey "ran but nothing sent." See [Journey logs](https://www.courier.com/docs/monitor/logs#journey-logs).

The same data is in the runs API:

| Operation | Node | Python | CLI |
|-----------|------|--------|-----|
| List runs | `client.journeys.runs.list({ template_id, status })` | `client.journeys.runs.list(template_id=..., status=...)` | `courier journeys:runs list --template-id ID --status ERROR` |
| One run | `client.journeys.runs.retrieve(runId)` | `client.journeys.runs.retrieve(run_id)` | `courier journeys:runs retrieve --run-id RUN_ID` |
| Each step of a run | `client.journeys.runs.listSteps(runId)` | `client.journeys.runs.list_steps(run_id)` | `courier journeys:runs list-steps --run-id RUN_ID` |

Each step's `node_id` is the node's id in the published journey. A send step that produced a message carries its `message_id`, so follow it to `GET /messages/{message_id}` for delivery status.

---

## Coming from Automations

**Journeys is Courier's orchestration product and where the investment goes.** If you're building multi-step flows on Automations today, build new ones as Journeys, existing Automations keep running, so there's no forced cutover.

The models are near-identical: a flow a user enters, moves through step by step, and exits. Every Automations step has a direct node equivalent, delay, if/switch, send, batch, digest, throttle, fetch, and cancellation by token. What Journeys adds is that the definition is code: a JSON DAG you create, version, publish, and invoke over REST, with immutable published versions, journey-scoped templates, A/B experiments on send nodes, a typed trigger contract, and run logs that show you exactly which branch a run took and why.

## Related

- [Elemental](./elemental.md), content format for journey-scoped templates
- [Templates](./templates.md), workspace-level template CRUD (for templates outside of journeys)
- [Slack](../channels/slack.md) and [MS Teams](../channels/ms-teams.md), channel setup, Block Kit, Adaptive Cards
- [Tenants](./tenants.md), per-customer context for `message.context.tenant_id` and per-tenant Slack/Teams credentials
- [Multi-Channel](./multi-channel.md), channel routing and escalation patterns
- [Patterns](./patterns.md), reusable code patterns (idempotency, cancellation, masking)
- [Reliability](./reliability.md), retries, idempotency, webhook handling
- [Building Journeys via API](https://www.courier.com/docs/journeys/build), official Courier documentation
- [Journeys API Reference](https://www.courier.com/docs/api-reference/journeys/create-a-journey), endpoint reference
- [Journey logs](https://www.courier.com/docs/monitor/logs#journey-logs), step through runs to debug
