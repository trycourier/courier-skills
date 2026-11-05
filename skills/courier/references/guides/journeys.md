# Journeys

A journey is a JSON graph of nodes that Courier runs asynchronously when you invoke it by API, or when a Segment event, an inbound webhook, or a user joining an audience triggers it. Use it for every multi-step flow; for existing Automations, see [Coming from Automations](#coming-from-automations).

**Contents:** [Quick Reference](#quick-reference) · [Concepts](#concepts) · [Standard Workflow](#standard-workflow) · [Node Types Reference](#node-types-reference) · [Conditions](#conditions) · [Variable Interpolation](#variable-interpolation) · [Merge Strategies (Fetch Nodes)](#merge-strategies-fetch-nodes) · [Examples](#examples) · [Errors & Status Codes](#errors--status-codes) · [Cancelling Runs](#cancelling-runs) · [Debugging Runs](#debugging-runs) · [Coming from Automations](#coming-from-automations) · [Related](#related)

## Quick Reference

### Rules
- **Create, then wire, then publish.** `POST /journeys` takes a `trigger` node first and an `exit` node last, with no `send` nodes (`422`) and no node `id`s (`400 client-supplied node ids are not allowed`). Create the journey-scoped templates under `POST /journeys/{id}/templates`, then add the send nodes with `PUT /journeys/{id}`. See [Standard Workflow](#standard-workflow)
- `PUT /journeys/{id}` is a **full replacement** of the draft and takes the same body: send every node, the trigger first and the `exit` last. It accepts and preserves node `id`s, which you need only to reference an earlier send in a `send_status.<nodeId>` condition, since branch paths nest their child nodes inline
- Send nodes take **journey-scoped** template ids, never workspace `nt_...` ids. Journey-scoped templates can't be used from the Send API or shared across journeys
- **Publishing a journey never publishes its templates.** Publish each template first (create it with `"state": "PUBLISHED"`, or `POST /journeys/{id}/templates/{templateId}/publish` after any content change), then the journey. Invoke runs the last published version, and an unpublished journey returns `404`
- `POST /journeys/{id}/invoke` returns `202` with a `runId`; the run is asynchronous
- Journey-scoped templates use Elemental `version` `"2022-01-01"`. Delay durations are ISO 8601 (`"PT30M"`, `"P1D"`)
- Conditions are **string** tuples, `[path, operator, value]` or `[path, operator]`: a bare tuple for one condition (never `[[...]]`, which returns `400 nodes.N.paths.M.conditions: Invalid input`), an `{ "AND": [...] }` / `{ "OR": [...] }` object for several. Values are strings (`"true"`, `"50"`). Every path starts with `data.`, `profile.`, `tenant.` or `send_status.<nodeId>`, trigger conditions included, or create and replace return `400`. See [Conditions](#conditions)
- Interpolation differs by context: journey-scoped templates read run data bare, `{{field}}` (`{{data.field}}` renders blank there), while workspace templates sent with `/send` use `{{data.field}}`; fetch URLs, headers, query params and bodies need a root on every variable (`{{data.field}}`, `{{profile.field}}`, `{{tenant.field}}`, or `{{recipient}}` for the user ID), and a bare `{{field}}` there is a `400`; conditions use `data.field`. See [Variable Interpolation](#variable-interpolation)
- A send node's `to` override takes **exactly one** of `email_override`, `phone_number_override`, `user_id_override`, `slack`, or `ms_teams`. A Slack `access_token` must be a runtime reference (`{{data.slack_token}}`), never a literal token. See [Slack and Teams sends](#slack-and-teams-sends)
- `message.context.tenant_id` on a send node delivers as one of your customers: a literal id or a whole-string mustache reference only. See [Send Node Options](#send-node-options)

### Common Mistakes
- Publishing the journey and expecting its templates to go live. A send whose template has no published version fails at delivery (`UNDELIVERABLE`, "Notification template not found") while the run and the send step still show `PROCESSED`. Check the message, not the run
- Assuming the trigger `schema` rejects bad payloads. It isn't enforced at invoke: a payload that breaks it gets `202` and the run completes. Validate in your app, or gate with trigger `conditions` (a failed one returns `422`)
- Treating a fetch as best-effort. A failed fetch stops the run with `ERROR`, and no later node runs. See [When a fetch fails](#when-a-fetch-fails)
- Addressing Teams by `channel_name`, `user_id`, or `email` without `service_url` or `tenant_id`. See [Slack and Teams sends](#slack-and-teams-sends)

### SDK shape, Journey management

> **Note:** The API reference and CLI name the journey's own ID `{templateId}` / `--template-id`. It is not a notification template ID. This guide uses `{id}`.

| Operation | Node |
|-----------|------|
| Create | `client.journeys.create({ name, nodes, enabled })` |
| List / retrieve / archive | `client.journeys.list()` · `client.journeys.retrieve(id)` · `client.journeys.archive(id)` |
| Replace (draft) | `client.journeys.replace(id, { name, nodes, enabled })` |
| List versions / publish | `client.journeys.listVersions(id)` · `client.journeys.publish(id)` |
| Invoke | `client.journeys.invoke(id, { user_id, data, profile })` → `{ runId }` |

Python is snake_case with the same positional `id`, except invoke: `client.journeys.invoke(template_id=id, user_id=..., data=..., profile=...)` → `.run_id`. CLI: `courier journeys <operation> --template-id ID`, e.g. `courier journeys invoke --template-id ID --user-id user-123 --data '{...}'`.

### SDK shape, Journey-scoped templates

Under `client.journeys.templates.*` and over REST (the MCP tools are `create_journey_template`, `get_journey_template`, and so on). Argument order differs by method: `create` and `list` take the **journey** id first. Every other method takes the **template** id first, with the journey id as `templateId` in the params object.

| Operation | Node SDK | REST |
|-----------|----------|------|
| Create | `client.journeys.templates.create(journeyId, body)` | `POST /journeys/{id}/templates` |
| List | `client.journeys.templates.list(journeyId)` | `GET /journeys/{id}/templates` |
| Retrieve | `client.journeys.templates.retrieve(templateId, { ... })` | `GET /journeys/{id}/templates/{templateId}` |
| Replace | `client.journeys.templates.replace(templateId, { ... })` | `PUT /journeys/{id}/templates/{templateId}` |
| Archive | `client.journeys.templates.archive(templateId, { ... })` | `DELETE /journeys/{id}/templates/{templateId}` |
| Publish | `client.journeys.templates.publish(templateId, { ... })` | `POST /journeys/{id}/templates/{templateId}/publish` |
| Get content | `client.journeys.templates.retrieveContent(templateId, { ... })` | `GET /journeys/{id}/templates/{templateId}/content` |
| Put content | `client.journeys.templates.putContent(templateId, { ... })` | `PUT /journeys/{id}/templates/{templateId}/content` |
| Put locale | `client.journeys.templates.putLocale(localeId, { ... })` | `PUT .../locales/{localeId}` |
| List versions | `client.journeys.templates.listVersions(templateId, { ... })` | `GET /journeys/{id}/templates/{templateId}/versions` |

**Reading a draft.** There is no `/draft/content` route on journey-scoped templates (it returns **404**). Use the `version` query parameter:

| Want | Route |
|---|---|
| Published content | `GET /journeys/{jid}/templates/{tid}/content` |
| Draft content | `GET /journeys/{jid}/templates/{tid}/content?version=draft` |
| A specific version | `GET /journeys/{jid}/templates/{tid}/content?version=v001` |

`putLocale` on a journey template takes the same `elements` body as on a workspace template, with `templateId` (the journey) and `notificationId` as parameters; see [localization.md](./localization.md#journey-templates).

---

## Concepts

### Triggers

Every journey starts with a trigger node. The API accepts four `trigger_type` values:

| Trigger type | How runs begin | Required fields |
|-------------|----------------|-----------------|
| `api-invoke` | You call `POST /journeys/{id}/invoke` | None beyond discriminators. Optional: `schema` (JSON Schema for editor autofill and variable hints, **not enforced at invoke**), `conditions` (gate invocation; failed condition → `422`). |
| `segment` | A matching Segment event arrives | `request_type` (`identify`, `group`, `track`, or `page`). Optional: `event_id`, `conditions`. With no `event_id` it fires on every event of that type. For `track` events, the event `userId` must be a valid Courier Profile ID or the journey won't start. |
| `webhook` | An event arrives on one of your [inbound webhooks](./webhooks.md#inbound-webhooks) | `event_source`. Optional: `event_id`, matched against the payload's `event`, and `conditions`. Every payload needs a `userId` matching a Courier user. |
| `audience` | A user newly matches an [audience](./audiences.md) | `audience_id` (one audience). Optional: `conditions`. Users already in the audience when you publish don't enter. |

Webhook and audience triggers take no `schema`.

### Run data is a snapshot

On invoke, Courier loads the recipient's profile once and stores the run's `{ data, profile }`. Every node reads that snapshot. A delay doesn't refresh it: if you update the user's profile or your own database while the run waits, a later branch still sees the values from invoke time. Only a `fetch` node (or an update-profile step) changes the run's context mid-flight. So branch on data you pass at invoke or fetch during the run:

```json
{ "type": "fetch", "method": "get", "url": "https://api.example.com/users/{{recipient}}/plan", "merge_strategy": "soft-merge" }
```

### Journey-Scoped vs Workspace Templates

Journey-scoped templates are created under `POST /journeys/{id}/templates`, hold [Elemental](./elemental.md) content, and serve only that journey's send nodes. Use a workspace template when the content must be shared across journeys or sent from the Send API.

**Editing content does not change what the journey sends.** A journey-scoped template versions independently, so `PUT .../content` alone leaves the journey delivering the last published version with nothing in the journey to indicate an edit is pending. Publish the template to make the edit live. `GET .../versions` shows the mismatch while it lasts:

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

---

## Standard Workflow

Every journey follows the same five-step process: create the shell, add templates, wire them into the DAG, publish, and invoke.

### Step 1: Create the journey shell

Create a journey with a name, a trigger node, and an exit node last (other non-send nodes can go between them). Pass `"state": "PUBLISHED"` to publish on create (the default is `"DRAFT"`).

```bash
curl -sS -X POST "https://api.courier.com/journeys" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome Journey",
    "nodes": [
      { "type": "trigger", "trigger_type": "api-invoke" },
      { "type": "exit" }
    ],
    "enabled": true
  }'
```

Create returns `201` with the journey, including server-generated node `id`s. Save the top-level journey `id`; every later request uses it.

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

First publish every journey-scoped template the send nodes use (Step 2 creates them published; republish any you've edited since). Then publish the journey.

Lock in the current draft as a versioned snapshot. All new runs execute against the published version.

```bash
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/publish" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json"
```

### Step 5: Invoke

Start a run. The journey must be **published** first, and you can invoke it by ID or alias. Provide `user_id`, a `profile` with contact info, or both (Courier can also resolve the recipient from `user_id`/`userId`/`anonymousId` inside `profile` or `data`). It returns `202` with `{ "runId": "1-65f240a0-47a6a120c8374de9bcf9f22c" }`, the id you look up in the journey's Logs tab or `journeys.runs.retrieve`.

- **Profile-only** (no stored Courier user): pass `profile` with contact info and omit `user_id`.
- **Profile merge:** when you pass both `user_id` and `profile`, request fields override stored profile fields with the same key; other stored fields are preserved.
- **Tenant-scoped profile** (multi-tenant): pass `"profile": { "context": { "tenant_id": "hospital-a" } }` to load the user's tenant-scoped profile.

```bash
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/invoke" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_abc123",
    "profile": { "email": "alice@example.com" },
    "data": {
      "first_name": "Alice",
      "company_name": "Acme Corp",
      "dashboard_url": "https://app.acme.com/dashboard"
    }
  }'
```

The SDK forms are in the [Journey management table](#sdk-shape-journey-management). In a fetch, read the user ID as `{{recipient}}`, see [Variable Interpolation](#variable-interpolation).

---

## Node Types Reference

| Type | Discriminator | Required fields |
|------|--------------|-----------------|
| Trigger | `type: "trigger"`, `trigger_type` | Per trigger type, see [Triggers](#triggers). |
| Send | `type: "send"` | `message.template` (journey-scoped template ID), or an [`experiment`](#ab-experiments-on-a-send-node) beside `message` instead. Optional: `message.to` (recipient override: `email_override`, `phone_number_override`, `user_id_override`, `slack`, or `ms_teams`, exactly one), `message.context` (tenant context), `message.delay`, `message.data`, `channel` (optional label enum, no routing effect, see [Send Node Options](#send-node-options)), `conditions`. |
| Delay (duration) | `type: "delay"`, `mode: "duration"` | `duration` (ISO 8601 duration string, e.g. `"PT30M"`). Optional: `conditions`. |
| Delay (until) | `type: "delay"`, `mode: "until"` | `until` (ISO 8601 timestamp or context reference). Optional: `conditions`. |
| Fetch (GET/DELETE) | `type: "fetch"`, `method: "get"` or `"delete"` | `url`, `merge_strategy`. Optional: `headers`, `query_params`, `response_schema`, `conditions`. |
| Fetch (POST/PUT) | `type: "fetch"`, `method: "post"` or `"put"` | `url`, `merge_strategy`. Optional: `body`, `headers`, `query_params`, `response_schema`, `conditions`. |
| Branch | `type: "branch"` | `paths[]` (each with `conditions` and `nodes[]`; evaluated in order, the first match runs), `default` (with `nodes[]`). Optional: `paths[].label`, `default.label`. |
| Throttle (static) | `type: "throttle"`, `scope: "user"` or `"global"` | `max_allowed`, `period`. Optional: `conditions`. |
| Throttle (dynamic) | `type: "throttle"`, `scope: "dynamic"` | `max_allowed`, `period`, `throttle_key`. Optional: `conditions`. |
| Batch | `type: "batch"`, `scope: "user"` | `wait_period` (ISO 8601 quiet window, `PT1M` to `P1D`), `max_wait_period` (ISO 8601 hard ceiling, from `wait_period` up to `P7D`), `retain` (`{ type: "first"\|"last"\|"highest"\|"lowest", count: 0–25, sort_key }`; `sort_key` required for `highest`/`lowest`). Optional: `max_items` (1–1000, default 100), `category_key` (≤256 chars, one whole reference such as `"{{data.event_type}}"`, see [batching.md](./batching.md#batch-data-in-templates)), `conditions`. |
| Send to Digest | `type: "add-to-digest"` | `subscription_topic_id`. Optional: `conditions`. |
| AI | `type: "ai"` | `model`, `user_prompt`, `output_schema` (JSON Schema for the structured result). Optional: `web_search`, `conditions`. |
| Exit | `type: "exit"` | None. Optional: `id`. |

The builder's **Cancel** node has no API `type`; from code, call `POST /journeys/cancel`. See [Cancelling Runs](#cancelling-runs).

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

Every condition path starts with one of these roots, on branch paths, node `conditions` and trigger `conditions` alike:

- `data.`: the invocation `data`, plus anything a fetch or AI node merged in
- `profile.`: the recipient's profile. There is no `user.` root, so write `profile.tier`, not `user.tier`
- `tenant.`: the run's tenant. Only when the trigger sets one, otherwise the save fails
- `send_status.<nodeId>`: an earlier send's delivery status, with `was` or `was not` only

Create and replace check every condition and return a `400` that names the bad path, for example `Condition path "user.tier" must start with data., profile., tenant., or send_status.` Array wildcards (`data.items.#.sku`) are rejected the same way.

---

## Variable Interpolation

How you reference a context value depends on **where** you use it. Getting this wrong is the most common journey bug:

| Context | Syntax | Example |
|---------|--------|---------|
| Journey-scoped template content (Elemental) | Run data sits at the top level: `{{field}}`. `{{data.field}}` renders blank in a journey-scoped template. `{{profile.field}}` works. Check a test run's rendered output before shipping copy | `"Welcome, {{first_name}}!"` |
| Workspace template content (Elemental, sent with `/send`) | `{{data.field}}` works in both scopes. A bare `{{field}}` resolves only in default-scope templates (API-created with no `scope`). Design Studio templates are `scope: "strict"`, so read `content.scope` before editing one. Digest totals are the exception, see [digests.md](./digests.md) | `"Welcome, {{data.first_name}}!"` |
| Fetch node `url`, query params, body | `{{data.field}}`, `{{profile.field}}`, `{{tenant.field}}`, or `{{recipient}}` (the user ID). A bare `{{field}}` is a `400` on create or replace | `"https://api.app.com/users/{{recipient}}/status"` |
| Branch / trigger `conditions` | `data.field`, `profile.field`, `tenant.field` (string tuples) | `["data.completed", "is equal", "true"]` |
| Fetch **header values** | A rooted variable inside a plain string | `{ "Authorization": "Bearer {{data.api_token}}" }` |
| Send node `to.slack` / `to.ms_teams` / `context.tenant_id` values | `{{field}}` as the **whole string** | `"access_token": "{{data.slack_token}}"` |

Notes:
- `user_id` passed at the top level of an invoke is used for **recipient resolution** and is not guaranteed to be projected into `data`. In a fetch, use `{{recipient}}`. If a template needs it, declare `user_id` in the trigger schema and pass it inside `data` too.
- A fetch variable with no value (missing, `null`, or `""`) in the URL, headers or query params fails the run with `Variable {{data.user_id}} has no value in this run`.
- Fetch responses are merged into the context (per `merge_strategy`) and are then referenced like any other field: `data.field` in conditions, `{{data.field}}` in a later fetch, `{{field}}` in templates.
- There is **no `{{secrets.*}}` namespace.** Pass credentials via `data`/`profile` and interpolate them into the header string with `{{data.field}}` or `{{profile.field}}`, or store them in the provider/workspace settings.

---

## Merge Strategies (Fetch Nodes)

When a fetch node receives a response, `merge_strategy` determines how the response is incorporated into run state. **`soft-merge` is the safest default**. It never overwrites trigger schema or profile fields.

| Strategy | Behavior |
|----------|----------|
| `soft-merge` (recommended default) | Adds new fields from the response without overwriting existing values. |
| `overwrite` | Deep-merges response into state. Response values overwrite existing fields with the same key. |
| `replace` | Replaces the entire run state with the response. |
| `none` | Doesn't merge into existing context. If the run's context is empty, the response is used. |

Fetch nodes require **HTTPS** URLs on a public host.

### When a fetch fails

**A failed fetch stops the run.** The step and the run both end in `ERROR`, and the nodes after it show `NOT PROCESSED`. Causes are a non-2xx status (redirects aren't followed), a 10-second timeout, a body over 1 MB, no response, or a URL variable with no value. The step's `error.message` names the cause, for example `Fetch failed: GET api.yourapp.com returned 404`. Read it from the run's steps, see [Debugging Runs](#debugging-runs).

If the run should go on without the data, make the endpoint return `200` with an empty or default body, then branch on the field with `["data.expected_field", "exists"]`.

---

## Examples

### Delay, Fetch, Branch, and Exit Nodes

The [Standard Workflow](#standard-workflow) covers the trigger, journey-scoped templates, and send nodes. These `nodes` for a `PUT /journeys/{id}` add the rest: a `delay`, a `fetch` that merges an HTTP response into run state, a `branch` on that data, and `exit` nodes that end the run early.

```json
[
  { "type": "trigger", "trigger_type": "api-invoke" },
  { "type": "send", "message": { "template": "<welcome-template-id>" } },
  { "type": "delay", "mode": "duration", "duration": "P1D" },
  {
    "type": "fetch",
    "method": "get",
    "url": "https://api.yourapp.com/users/{{recipient}}/setup-status",
    "merge_strategy": "soft-merge",
    "headers": { "Authorization": "Bearer {{data.app_api_token}}" }
  },
  {
    "type": "branch",
    "paths": [
      {
        "label": "Setup complete",
        "conditions": ["data.setup_complete", "is equal", "true"],
        "nodes": [
          { "type": "send", "message": { "template": "<success-template-id>" } },
          { "type": "exit" }
        ]
      }
    ],
    "default": {
      "label": "Setup incomplete",
      "nodes": [
        { "type": "send", "message": { "template": "<reminder-template-id>" } },
        { "type": "delay", "mode": "duration", "duration": "P2D" },
        { "type": "send", "message": { "template": "<nudge-template-id>" } },
        { "type": "exit" }
      ]
    }
  },
  { "type": "exit" }
]
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

A send node can also carry `channel` **outside** `message`, such as `"channel": "inbox"` (one of `email`, `sms`, `push`, `inbox`, `slack`, `msteams`). The journey designer writes it. **It is a label for analytics and reporting, not routing**: setting it doesn't make a send go to that channel, and omitting it doesn't stop delivery. To control the delivery channel, set `channel` on the journey-scoped template or attach a routing strategy. See [the channel element vs the three other places a channel is named](./elemental.md#the-channel-element-vs-the-three-other-places-a-channel-is-named).

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

- `access_token` must be a whole-string **runtime reference** like `{{data.slack_token}}`. Literal `xoxb-...` values are rejected.
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

**Template channel.** `POST /journeys/{id}/templates` takes `channel` as an open string that routes: a channel key or provider-key form (`slack`, `msteams`, or `provider:alias`), plus an optional `providerKey`. The send node's own `channel` only labels, see [Send Node Options](#send-node-options). Block Kit, Adaptive Cards, threading, and provider setup live in [slack.md](../channels/slack.md) and [ms-teams.md](../channels/ms-teams.md).

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

The fields are in the [Node Types Reference](#node-types-reference). How it releases, what `retain` and `category_key` actually do, and what the template receives are in [batching.md](./batching.md).

### Send to Digest Node

`add-to-digest` adds the event to a subscription topic's digest; the topic owns the schedule, categories, and digest template. A topic with no digest template fails the run with `ERROR`. Setup is in [digests.md](./digests.md#from-a-journey).

### AI Node

Run an LLM prompt and store a structured result (conforming to `output_schema`) under `data.ai_result` for downstream nodes. `model` and `user_prompt` are required; a missing one is a `400` (`AI step needs a model`, `AI step needs a prompt`):

```json
{
  "type": "ai",
  "model": "gpt-5.4-mini",
  "user_prompt": "Classify this support message intent: {{data.message_body}}",
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

- Read the result as `data.ai_result.intent` in conditions and `{{ai_result.intent}}` in templates. A second AI node overwrites `data.ai_result`, so use the first result before the run reaches the next one
- A failed AI node stops the run with `ERROR`, like a failed fetch. The step's `error.message` names the cause
- AI nodes run in the US datacenter only. In the EU, create, replace and publish fail
- `web_search` works only with the `claude-*` models and costs 2 extra credits per run
- Use a model id from the [AI node's model list](https://www.courier.com/docs/journeys/nodes/ai#ai-model). An unknown id is a `400` that lists the valid ones

### Segment-Triggered Journey

Instead of `api-invoke`, start runs from your Segment event stream, and filter which events qualify with trigger `conditions`. The trigger node:

```json
{
  "type": "trigger",
  "trigger_type": "segment",
  "request_type": "track",
  "event_id": "Order Completed",
  "conditions": ["data.total", "greater than", "100"]
}
```

A Segment event's properties are the run's `data`, so trigger `conditions` and later nodes both use `data.total`. A `properties.total` path is a `400` on create or replace, like any condition without a `data.`, `profile.`, `tenant.` or `send_status.` root. Segment triggers take no `schema`.

---

## Errors & Status Codes

Error bodies have the shape `{ "type": "...", "message": "..." }`. Create errors are in the [Rules](#rules). Common **invoke** (`POST /journeys/{id}/invoke`) errors:

| Status | Cause | Example message |
|--------|-------|-----------------|
| `400` | Missing recipient | `User identifier or profile required. Provide user_id, ... or profile with contact info.` |
| `400` | `user_id` has no stored profile, and the body has no `profile` | `Profile could not be loaded` |
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

```typescript
// Your app learns the order shipped: stop the whole reminder ladder
await client.journeys.cancel({ cancelation_token: "order-4821" });
```

Use the **token** when one real-world event should stop a whole family of runs (order shipped, trial converted, user unsubscribed). Use **`run_id`** when you're cancelling one specific run you hold the id for.

### From inside a flow: the Cancel node

A **Cancel** node stops in-flight runs from within a journey. Its one setting is a Cancelation Token.

> ⚠️ **A Cancel node does not cancel its own run.** When a run reaches the node, Courier cancels **every *other* active run sharing that token**, the run containing the node continues to the next node. Use an `exit` node to end the current run.

This is the pattern for "the newest run wins": a re-engagement journey whose first node cancels any earlier run for the same user, so a returning user doesn't receive two overlapping sequences.

The Cancel node is configured in the journey builder. It is **not part of the API journey definition**, there is no `cancel` node `type` in the published OpenAPI schema, so you cannot add one via `POST /journeys` or `PUT /journeys/{id}`. Building journeys as code? Call `POST /journeys/cancel` from your application at the equivalent point instead. It has the same token semantics.

## Debugging Runs

Every invoke returns a `runId`. Open the journey's **Logs** tab to see a run on the journey canvas: which nodes ran and in what order, which path each branch took, where a waiting run is paused, and which node failed. Start here when a journey "ran but nothing sent." See [Journey logs](https://www.courier.com/docs/monitor/logs#journey-logs).

The same data is in the runs API:

| Operation | Node | CLI |
|-----------|------|-----|
| List runs | `client.journeys.runs.list({ template_id, status })` | `courier journeys:runs list --template-id ID --status ERROR` |
| One run | `client.journeys.runs.retrieve(runId)` | `courier journeys:runs retrieve --run-id RUN_ID` |
| Each step of a run | `client.journeys.runs.listSteps(runId)` | `courier journeys:runs list-steps --run-id RUN_ID` |

Python uses snake_case (`list_steps`).

Each step's `node_id` is the node's id in the published journey. A send step that produced a message carries its `message_id`, so follow it to `GET /messages/{message_id}` for delivery status.

- A step with `status: "ERROR"` carries `error.message`, such as `Fetch failed: GET api.yourapp.com returned 404`. A `SKIPPED` step carries `skip_reason`, such as `Node conditions not met`. Both are `null` otherwise
- Nodes the run never reached show `NOT PROCESSED`
- Steps aren't returned in the order they ran, and they share one `created_at`. Use each step's `updated_at` and `node_id` to place it

---

## Coming from Automations

Build new multi-step flows as Journeys; existing Automations keep running, so there's no forced cutover. Most Automations steps have a direct node equivalent: delay, if/switch, send, batch, digest, throttle, fetch, and cancellation by token. Two don't:

- **Send to a list.** A journey `send` node addresses the run's one recipient. To reach a list, invoke the journey once per member, or keep that step on a list send.
- **Get Profile.** A journey loads the profile once at invoke (see [Run data is a snapshot](#run-data-is-a-snapshot)). To read fresher data mid-run, use a `fetch` node against your API or Courier's `GET /profiles/{user_id}`.

Journeys interpolate with `{{data.field}}`, not the `${...}` form some Automations use.

## Related

- [Templates](./templates.md) (workspace templates), [Multi-Channel](./multi-channel.md) (escalation patterns), [Tenants](./tenants.md) (per-customer context)
- [Building Journeys via API](https://www.courier.com/docs/journeys/build) · [Journeys API Reference](https://www.courier.com/docs/api-reference/journeys/create-a-journey) · [Journey logs](https://www.courier.com/docs/monitor/logs#journey-logs)
