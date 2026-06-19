# Journeys

Build multi-step notification workflows as code using directed acyclic graphs (DAGs). A journey is a sequence of nodes — send, delay, branch, fetch, throttle, batch, add-to-digest, AI, and exit — that Courier executes asynchronously when you invoke the journey via API or a Segment event.

> **Journeys are the recommended way to build multi-step flows.** If you have existing Courier Automations, they continue to work — see [Migrating from Automations](#migrating-from-automations) at the bottom of this file.

## Quick Reference

### Rules
- A journey must have at least one `trigger` node — it is the entry point for all runs
- Journey-scoped templates are **not** workspace templates — they live under `POST /journeys/{id}/templates` and cannot be referenced from the Send API or shared across journeys
- Journeys must be **published** before they can be invoked — draft changes are not executed
- `PUT /journeys/{id}` is a **full replacement** of the draft — include all nodes, not just the ones you changed
- `POST /journeys/{id}/invoke` returns `202` with a `runId` — processing is asynchronous
- **Node `id`s are server-generated.** Do **not** send client-supplied node `id`s on `POST /journeys` — they're rejected with `400` (`client-supplied node ids are not allowed`). On `PUT /journeys/{id}` (replace) `id`s are accepted and preserved, but they're optional. Branch paths nest their child nodes inline, so you don't need `id`s to wire the graph at all.
- Elemental version string for journey-scoped templates is always `"2022-01-01"` — see [Elemental](./elemental.md)
- Delay durations use ISO 8601 format (e.g., `"PT1H"` for one hour, `"PT30M"` for 30 minutes, `"P1D"` for one day)
- Conditions use **string** tuples: `[path, operator, value]` for binary, `[path, operator]` for unary. A single condition is the bare tuple; multiple conditions use an `{ "AND": [...] }` / `{ "OR": [...] }` object. Comparison values are always strings (`"true"`, `"50"`), not native booleans/numbers — see [Conditions](#conditions)
- Header/value interpolation differs by context: templates and fetch URLs use `{{field}}` (no prefix); branch/trigger conditions use `data.field`; fetch **header values** use the `$ref` object form `{ "$ref": "data.token" }` — see [Variable Interpolation](#variable-interpolation)

### Common Mistakes
- Forgetting to publish after creating or updating the journey (invoke uses the last published version, not the draft)
- Referencing workspace template IDs (`nt_...`) in send nodes — send nodes require journey-scoped template IDs created under `POST /journeys/{id}/templates`
- Creating send nodes before creating the journey-scoped templates they reference (the template must exist to wire its ID)
- Omitting the trigger node when replacing a journey via `PUT` (every journey needs at least one trigger)
- Using `POST /journeys/{id}/invoke` on an unpublished journey — returns an error; publish first
- Assuming the trigger `schema` rejects bad payloads at invoke — it does **not**. The `schema` powers editor autofill and variable hints only; missing fields are not rejected at invocation. A run proceeds until it reaches a node that references a missing field, then fails there. Use **trigger `conditions`** to gate invocation (a failed trigger condition returns `422`)
- Including `send` nodes in the `POST /journeys` body — send nodes are **not allowed on create**. Create the shell (trigger only), add templates, then add send nodes via `PUT /journeys/{id}`
- Wrapping a single condition in an extra array (`[[...]]`) or using non-string values — a single condition is a bare tuple of strings (`["data.plan", "is equal", "pro"]`); use an `{ "AND": [...] }` / `{ "OR": [...] }` object for multiple conditions

### SDK shape — Journey management

> **Note:** The API reference uses `{templateId}` as the path parameter name for the journey ID. This is the journey's own ID (returned from `client.journeys.create`), not a notification template ID. This guide uses `{id}` for clarity.

Journey management is supported by the Node and Python SDKs and the CLI. Use the SDK in application code; use curl/CLI for ad-hoc work.

| Operation | Node | Python | CLI |
|-----------|------|--------|-----|
| Create | `client.journeys.create({ name, nodes, enabled })` | `client.journeys.create(name=..., nodes=..., enabled=...)` | `courier journeys create --name ... --node '{...}'` |
| List | `client.journeys.list()` | `client.journeys.list()` | `courier journeys list` |
| Retrieve | `client.journeys.retrieve(id)` | `client.journeys.retrieve(id)` | `courier journeys retrieve --template-id ID` |
| Replace (draft) | `client.journeys.replace(id, { name, nodes, enabled })` | `client.journeys.replace(id, name=..., nodes=...)` | `courier journeys replace --template-id ID ...` |
| Archive | `client.journeys.archive(id)` | `client.journeys.archive(id)` | `courier journeys archive --template-id ID` |
| List versions | `GET /journeys/{id}/versions` (REST) | `GET /journeys/{id}/versions` (REST) | `courier journeys versions --template-id ID` |
| Publish | `client.journeys.publish(id)` | `client.journeys.publish(id)` | `courier journeys publish --template-id ID` |
| Invoke | `client.journeys.invoke(id, { user_id, data, profile })` → `{ runId }` | `client.journeys.invoke(template_id=id, user_id=..., data=..., profile=...)` → `.run_id` | `courier journeys invoke --template-id ID --user-id user-123 --data '{...}'` |

### SDK shape — Journey-scoped templates

Journey-scoped template CRUD is **not** in the SDK or MCP yet — use REST/curl. (Workspace templates under `/notifications` do have full SDK support — see [templates.md](./templates.md).)

| Operation | REST |
|-----------|------|
| Create | `POST /journeys/{id}/templates` |
| List | `GET /journeys/{id}/templates` |
| Retrieve | `GET /journeys/{id}/templates/{templateId}` |
| Replace | `PUT /journeys/{id}/templates/{templateId}` |
| Archive | `DELETE /journeys/{id}/templates/{templateId}` |
| Publish | `POST /journeys/{id}/templates/{templateId}/publish` |
| List versions | `GET /journeys/{id}/templates/{templateId}/versions` |

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

Every journey starts with a trigger node. Two types:

| Trigger type | How runs begin | Required fields |
|-------------|----------------|-----------------|
| `api-invoke` | You call `POST /journeys/{id}/invoke` | None beyond discriminators. Optional: `schema` (JSON Schema for editor autofill/variable hints — **not** invoke-time validation), `conditions` (gate invocation; failed condition → `422`). |
| `segment` | A matching Segment event arrives | `request_type` (`identify`, `group`, or `track`). Optional: `event_id`, `conditions`. For `track` events, the event `userId` must be a valid Courier Profile ID or the journey won't start. |

### Journey-Scoped vs Workspace Templates

| | Journey-scoped | Workspace |
|--|----------------|-----------|
| Created via | `POST /journeys/{id}/templates` | `POST /notifications` or Design Studio |
| Used from | Send nodes within the journey | Send API (`client.send.message`) |
| Shareable | No — exclusive to one journey | Yes — any send can reference them |
| Content format | [Elemental](./elemental.md) (`version` + `elements`) | Elemental or Design Studio |
| Publishable | Independently or with journey publish | Via `notifications.publish` |

Journey-scoped templates are published **automatically** when you publish the journey itself. You can also publish them independently via `POST /journeys/{id}/templates/{templateId}/publish` if you need to update a template without republishing the entire journey.

If you need a template reusable across journeys or callable from the Send API, use a workspace template. If the template is specific to one journey, keep it scoped.

---

## Standard Workflow

Every journey follows the same five-step process: create the shell, add templates, wire them into the DAG, publish, and invoke.

### Step 1: Create the journey shell

Create a journey with a name and at least a trigger node.

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
      }
    ],
    "enabled": true
  }'
```

> Do **not** include client-supplied node `id`s on create — the server generates them (and returns `400` if you send your own). `send` nodes are not allowed on `POST /journeys` either. Create the shell with the trigger (and other non-send nodes) only; add send nodes later via `PUT` once their templates exist. To publish immediately on create, pass `"state": "PUBLISHED"` (defaults to `"DRAFT"`).

Create returns `201` with the journey. The response echoes back **server-generated** node `id`s (e.g. `"PK5BA6NV424BAYN58R6CVM2GTH10"`). Save the top-level journey `id` — you'll use it in every subsequent request:

```json
{
  "id": "3ac3b1ba-5910-4954-9871-99e601d77bb8",
  "name": "Welcome Journey",
  "state": "DRAFT",
  "enabled": true,
  "nodes": [ { "id": "PK5BA6NV424BAYN58R6CVM2GTH10", "type": "trigger", "trigger_type": "api-invoke" } ],
  "created": 1715000000000,
  "creator": null,
  "updated": 1715000000000,
  "updater": null,
  "published": null
}
```

### Step 2: Create journey-scoped templates

Create the notification templates your send nodes will reference. Content uses [Elemental](./elemental.md) format.

```bash
JOURNEY_ID="<id from step 1>"

curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/templates" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "notification": {
      "name": "Welcome Email",
      "tags": [],
      "brand": null,
      "subscription": null,
      "content": {
        "version": "2022-01-01",
        "elements": [
          { "type": "meta", "title": "Welcome to {{company_name}}, {{first_name}}!" },
          { "type": "text", "content": "Hi {{first_name}}, thanks for signing up. We are excited to have you on board." },
          { "type": "text", "content": "Here are a few things to get you started:" },
          { "type": "action", "content": "Go to your dashboard", "href": "{{dashboard_url}}" }
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
      }
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

Start a run. The journey must be **published** first. You can invoke by journey **ID or alias**. Provide **either** `user_id` **or** a `profile` with contact info (Courier can also resolve the recipient from `user_id`/`userId`/`anonymousId` inside `profile` or `data`). Returns `202` with a `runId`. Courier processes the run asynchronously, walking through the DAG. The `runId` is what you look up in Run Inspection.

```json
{ "runId": "1-65f240a0-47a6a120c8374de9bcf9f22c" }
```

> **Tip:** If any downstream `fetch` node references `{{user_id}}` in its URL, also include `user_id` inside `data` — the top-level `user_id` is used for recipient resolution, but Courier does not guarantee it is projected into `data` for variable interpolation. Passing it both places is the safe default.

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
| `trigger` | Entry point. Discriminated by `trigger_type`: `api-invoke` or `segment`. |
| `send` | Send a notification using a journey-scoped template. References the template via `message.template`. |
| `delay` | Pause the run. Discriminated by `mode`: `duration` (ISO 8601) or `until` (timestamp). |
| `fetch` | Make an HTTP request and merge the response into run state. Discriminated by `method`: `get`, `delete`, `post`, or `put`. |
| `branch` | Conditional routing. Evaluates `paths[]` in order and routes to the first match, with a `default` fallback. |
| `throttle` | Rate-limit runs. Discriminated by `scope`: `user`, `global`, or `dynamic`. |
| `batch` | Collect multiple events into one aggregated payload, then fire one downstream step. Releases on `max_items`, a quiet `wait_period`, or the `max_wait_period` ceiling. |
| `add-to-digest` | Add the event to a digest keyed by a subscription topic; the digest releases on the topic's configured schedule. |
| `ai` | Run an LLM prompt with optional web search. Returns structured output per `output_schema`. |
| `exit` | End the run immediately. |

### Detailed Reference

| Type | Discriminator | Required fields |
|------|--------------|-----------------|
| Trigger (API) | `type: "trigger"`, `trigger_type: "api-invoke"` | None beyond discriminators. Optional: `id`, `schema`, `conditions`. |
| Trigger (Segment) | `type: "trigger"`, `trigger_type: "segment"` | `request_type` (`identify`, `group`, or `track`). Optional: `event_id`, `conditions`. |
| Send | `type: "send"` | `message.template` (journey-scoped template ID). Optional: `message.to` (overrides), `message.delay`, `message.data`, `conditions`. |
| Delay (duration) | `type: "delay"`, `mode: "duration"` | `duration` (ISO 8601 duration string, e.g. `"PT30M"`). Optional: `conditions`. |
| Delay (until) | `type: "delay"`, `mode: "until"` | `until` (ISO 8601 timestamp or context reference). Optional: `conditions`. |
| Fetch (GET/DELETE) | `type: "fetch"`, `method: "get"` or `"delete"` | `url`, `merge_strategy`. Optional: `headers`, `query_params`, `response_schema`, `conditions`. |
| Fetch (POST/PUT) | `type: "fetch"`, `method: "post"` or `"put"` | `url`, `merge_strategy`. Optional: `body`, `headers`, `query_params`, `response_schema`, `conditions`. |
| Branch | `type: "branch"` | `paths[]` (each with `conditions` and `nodes[]`), `default` (with `nodes[]`). Optional: `paths[].label`, `default.label`. |
| Throttle (static) | `type: "throttle"`, `scope: "user"` or `"global"` | `max_allowed`, `period`. Optional: `conditions`. |
| Throttle (dynamic) | `type: "throttle"`, `scope: "dynamic"` | `max_allowed`, `period`, `throttle_key`. Optional: `conditions`. |
| Batch | `type: "batch"`, `scope: "user"` | `wait_period` (ISO 8601 quiet window), `max_wait_period` (ISO 8601 hard ceiling; must be > `wait_period`), `retain` (`{ type: "first"\|"last"\|"highest"\|"lowest", count: 0–25, sort_key }`; `sort_key` required for `highest`/`lowest`). Optional: `max_items` (1–1000, default 100), `category_key` (partition key, ≤256 chars), `conditions`. |
| Add to digest | `type: "add-to-digest"` | `subscription_topic_id`. Optional: `conditions`. |
| AI | `type: "ai"` | `output_schema` (JSON Schema for the structured result). Optional: `model`, `user_prompt`, `web_search`, `conditions`. |
| Exit | `type: "exit"` | None. Optional: `id`. |

---

## Conditions

Several node types (`branch` paths, `send`, `delay`, `fetch`, `throttle`, triggers, …) support a `conditions` field. A condition's elements are **always strings** — compare against `"true"`/`"false"` and `"50"`, never native booleans or numbers.

The `conditions` field accepts one of three shapes:

**1. A single condition (bare tuple).** Binary is `[path, operator, value]`; unary is `[path, operator]`:

```json
"conditions": ["data.plan", "is equal", "pro"]
```

```json
"conditions": ["data.email", "exists"]
```

> Do **not** wrap a single condition in an extra array (`[[...]]`) — that is not a valid shape.

**2. A group (AND/OR).** An object with exactly one of `AND` or `OR`, each a list of 2+ condition tuples:

```json
"conditions": {
  "AND": [
    ["data.is_first_order", "is equal", "true"],
    ["data.order_total", "greater than", "50"]
  ]
}
```

**3. A nested group.** An object with `AND`/`OR` whose entries are themselves groups — e.g. "first-time buyer over $50 **OR** returning buyer over $200":

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

Condition paths reference the journey context: `data.*` (invocation `data` + merged fetch responses), `profile.*`, and `user.*`.

---

## Variable Interpolation

How you reference a context value depends on **where** you use it. Getting this wrong is the most common journey bug:

| Context | Syntax | Example |
|---------|--------|---------|
| Template content (Elemental) | `{{field}}` — **no** `data.` prefix | `"Welcome, {{first_name}}!"` |
| Fetch node `url` | `{{field}}` | `"https://api.app.com/users/{{user_id}}/status"` |
| Branch / trigger `conditions` | `data.field` (string tuples) | `["data.completed", "is equal", "true"]` |
| Fetch / send **header & override values** | `$ref` object | `{ "Authorization": { "$ref": "data.api_token" } }` |

Notes:
- `user_id` passed at the top level of an invoke is used for **recipient resolution** and is not guaranteed to be projected into `data`. If a fetch URL or template needs it, declare `user_id` in the trigger schema and pass it inside `data` too.
- Fetch responses are merged into the context (per `merge_strategy`) and are then referenced like any other field: `data.field` in conditions, `{{field}}` in templates.
- There is **no `{{secrets.*}}` namespace.** Pass credentials via `data`/`profile` and reference them with `$ref`, or store them in the provider/workspace settings.

---

## Merge Strategies (Fetch Nodes)

When a fetch node receives a response, `merge_strategy` determines how the response is incorporated into run state. **`soft-merge` is the safest default** — it never overwrites trigger schema or profile fields.

| Strategy | Behavior |
|----------|----------|
| `soft-merge` (recommended default) | Adds new fields from the response without overwriting existing values. |
| `overwrite` | Deep-merges response into state. Response values overwrite existing fields with the same key. |
| `replace` | Replaces the entire run state with the response. |
| `none` | Discards the response body. Useful for fire-and-forget requests. |

Fetch nodes require **HTTPS** URLs. If a fetch fails (network error or non-2xx), the journey **continues** and no data is merged — guard downstream nodes with conditions like `["data.expected_field", "exists"]`.

---

## Examples

### Onboarding Journey with Delays and Branching

A multi-day onboarding sequence that checks whether the user completed setup and branches accordingly.

**Step 1 — Create the journey shell:**

```bash
curl -sS -X POST "https://api.courier.com/journeys" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Onboarding Sequence",
    "nodes": [
      {
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
      }
    ],
    "enabled": true
  }'
```

**Step 2 — Create journey-scoped templates** (one per send node — welcome, setup reminder, core nudge, success):

```bash
# Create welcome email template
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/templates" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "notification": {
      "name": "Onboarding - Welcome",
      "tags": [],
      "brand": null,
      "subscription": null,
      "content": {
        "version": "2022-01-01",
        "elements": [
          { "type": "meta", "title": "Welcome, {{user_name}}!" },
          { "type": "text", "content": "Thanks for signing up. Let us help you get started." },
          { "type": "action", "content": "Complete setup", "href": "{{setup_url}}" }
        ]
      }
    }
  }'

# Repeat for: setup-reminder, core-nudge, success templates
```

**Step 3 — Wire the full DAG:**

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
        "headers": { "Authorization": { "$ref": "data.app_api_token" } }
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
      }
    ],
    "enabled": true
  }'
```

**Steps 4 & 5 — Publish and invoke** (same as the standard workflow above).

### Escalation Journey (Time-Based)

Escalate from in-app to push to email if the user hasn't read the notification:

```json
{
  "name": "Escalating Alert",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger",
      "trigger_type": "api-invoke"
    },
    {
      "id": "send-inbox",
      "type": "send",
      "message": { "template": "<inbox-template-id>" }
    },
    {
      "id": "wait-15m",
      "type": "delay",
      "mode": "duration",
      "duration": "PT15M"
    },
    {
      "id": "send-push",
      "type": "send",
      "message": { "template": "<push-template-id>" }
    },
    {
      "id": "wait-1h",
      "type": "delay",
      "mode": "duration",
      "duration": "PT1H"
    },
    {
      "id": "send-email",
      "type": "send",
      "message": { "template": "<email-template-id>" }
    }
  ],
  "enabled": true
}
```

### Win-Back Journey with Throttle

Rate-limit re-engagement attempts per user:

```json
{
  "name": "Win-Back Sequence",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger",
      "trigger_type": "api-invoke"
    },
    {
      "id": "throttle-user",
      "type": "throttle",
      "scope": "user",
      "max_allowed": 1,
      "period": "P30D"
    },
    {
      "id": "send-miss-you",
      "type": "send",
      "message": { "template": "<miss-you-template-id>" }
    },
    {
      "id": "wait-3-days",
      "type": "delay",
      "mode": "duration",
      "duration": "P3D"
    },
    {
      "id": "send-whats-new",
      "type": "send",
      "message": { "template": "<whats-new-template-id>" }
    },
    {
      "id": "wait-7-days",
      "type": "delay",
      "mode": "duration",
      "duration": "P7D"
    },
    {
      "id": "send-last-chance",
      "type": "send",
      "message": { "template": "<last-chance-template-id>" },
      "conditions": ["data.user_tier", "is equal", "high-value"]
    }
  ],
  "enabled": true
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
    "delay": { "until": "{{send_at}}", "timezone": "America/New_York" },
    "data": { "invoice_url": "{{invoice_url}}" }
  }
}
```

- `to` — override the resolved recipient: `email_override`, `phone_number_override`, `user_id_override`.
- `delay` — schedule this individual send: `until` (required, ISO 8601 timestamp or context reference) plus optional `timezone`. (For pausing the whole run, use a `delay` node instead.)
- `data` — extra merge data scoped to this send.

### Dynamic Delay

A `delay` node's interval can come from the journey context instead of a hardcoded value — pass a context reference in `duration` (an ISO 8601 duration like `PT2H`) or `until` (a timestamp):

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

- `retain.type` — which collected events to keep: `first`, `last`, `highest`, or `lowest` (the latter two require `sort_key`). `count` is 0–25.
- `category_key` — events sharing this value batch together; different values batch separately.

### Add to Digest Node

Add the event to a digest keyed by a subscription topic; the digest releases on the topic's configured schedule (rather than per-journey timing):

```json
{ "type": "add-to-digest", "subscription_topic_id": "<topic-id>" }
```

### AI Node

Run an LLM prompt and merge a structured result (conforming to `output_schema`) into the journey context for downstream branching:

```json
{
  "type": "ai",
  "model": "gpt-4o-mini",
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

### Segment-Triggered Journey

Instead of `api-invoke`, start runs from your Segment event stream. Filter which events qualify with trigger `conditions`:

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
    { "id": "send-thanks", "type": "send", "message": { "template": "<thanks-template-id>" } }
  ],
  "enabled": true
}
```

For `track` events, the event's `userId` must be a valid Courier Profile ID or the journey won't start. Segment journeys have no `schema` — Courier receives whatever Segment sends.

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
| `400` | `invalid_request_error` | Malformed condition (`nodes.N.paths.M.conditions: Invalid input`) — e.g. `[[...]]` wrapping or non-string values |
| `422` | `validation_error` | `send` node in the create body (`send nodes are not allowed at journey creation; create the journey, then create notification templates scoped to it, then PUT to wire the send nodes`) |

Common **invoke** (`POST /journeys/{id}/invoke`) errors:

| Status | Cause | Example message |
|--------|-------|-----------------|
| `400` | Missing recipient | `User identifier or profile required. Provide user_id, ... or profile with contact info.` |
| `404` | Journey not found / not published | `Automation template abc-123 not found` |
| `422` | Trigger conditions not met | `Trigger conditions not met` |
| `422` | Journey archived | `Cannot invoke archived automation template abc-123` |
| `422` | Journey disabled (`enabled: false`) | `Cannot invoke disabled automation template abc-123` |

## Debugging Runs

Every invoke returns a `runId`. Use **[Run Inspection](https://www.courier.com/docs/platform/journeys/run-inspection)** to step through a run node-by-node: a delay shows `Waiting` until it releases; a branch shows every condition evaluated, the actual values compared, and which path was taken; a fetch shows the response and merged fields. Start here when a journey "ran but nothing sent."

---

## Migrating from Automations

If you have existing Courier Automations, they continue to work. For new multi-step flows, use Journeys instead. Here's how the concepts map:

| Automations | Journeys |
|------------|----------|
| `client.automations.invoke.invokeByTemplate(templateId, { recipient, data })` | `POST /journeys/{id}/invoke` with `user_id` and `data` |
| `cancelation_token` + `invokeAdHoc({ steps: [{ action: "cancel" }] })` | Build exit logic into the journey DAG (exit nodes, branch conditions) |
| Delay step (dashboard) | `delay` node with `mode: "duration"` or `mode: "until"` |
| Condition step (dashboard) | `branch` node with `paths[]` and conditions |
| Send step (references a workspace template) | `send` node (references a journey-scoped template) |
| Batch/digest step (dashboard) | `batch` node (collect + aggregate) or `add-to-digest` node (topic-scheduled digest); use `throttle` for rate-limiting |
| Dashboard-only configuration | Fully API-driven — create, version, publish, invoke via REST |

**Key difference:** Automations are configured in the dashboard and triggered via SDK. Journeys are defined entirely via API — your journey definition is code, versioned, and publishable.

---

## Related

- [Elemental](./elemental.md) — content format for journey-scoped templates
- [Templates](./templates.md) — workspace-level template CRUD (for templates outside of journeys)
- [Multi-Channel](./multi-channel.md) — channel routing and escalation patterns
- [Patterns](./patterns.md) — reusable code patterns (idempotency, consent, cancellation)
- [Reliability](./reliability.md) — retries, idempotency, webhook handling
- [Building Journeys via API](https://www.courier.com/docs/platform/journeys/building-journeys-via-api) — official Courier documentation
- [Journeys API Reference](https://www.courier.com/docs/api-reference/journeys/create-a-journey) — endpoint reference
- [Run Inspection](https://www.courier.com/docs/platform/journeys/run-inspection) — step through runs to debug
