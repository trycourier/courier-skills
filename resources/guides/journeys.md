# Journeys

Build multi-step notification workflows as code using directed acyclic graphs (DAGs). A journey is a sequence of nodes — send, delay, branch, fetch, throttle, AI, and exit — that Courier executes asynchronously when you invoke the journey via API or a Segment event.

> **Journeys are the recommended way to build multi-step flows.** If you have existing Courier Automations, they continue to work — see [Migrating from Automations](#migrating-from-automations) at the bottom of this file.

## Quick Reference

### Rules
- A journey must have at least one `trigger` node — it is the entry point for all runs
- Journey-scoped templates are **not** workspace templates — they live under `POST /journeys/{id}/templates` and cannot be referenced from the Send API or shared across journeys
- Journeys must be **published** before they can be invoked — draft changes are not executed
- `PUT /journeys/{id}` is a **full replacement** of the draft — include all nodes, not just the ones you changed
- `POST /journeys/{id}/invoke` returns `202` with a `runId` — processing is asynchronous
- Node `id` values must be unique within a journey
- Elemental version string for journey-scoped templates is always `"2022-01-01"` — see [Elemental](./elemental.md)
- Delay durations use ISO 8601 format (e.g., `"PT1H"` for one hour, `"PT30M"` for 30 minutes, `"P1D"` for one day)
- Conditions use tuple syntax: `[path, operator, value]` for binary, `[path, operator]` for unary

### Common Mistakes
- Forgetting to publish after creating or updating the journey (invoke uses the last published version, not the draft)
- Referencing workspace template IDs (`nt_...`) in send nodes — send nodes require journey-scoped template IDs created under `POST /journeys/{id}/templates`
- Creating send nodes before creating the journey-scoped templates they reference (the template must exist to wire its ID)
- Omitting the trigger node when replacing a journey via `PUT` (every journey needs at least one trigger)
- Using `POST /journeys/{id}/invoke` on an unpublished journey — returns an error; publish first
- Passing `data` that doesn't match the trigger's `schema` — Courier validates the payload against the JSON Schema at invocation time

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
| `api-invoke` | You call `POST /journeys/{id}/invoke` | None beyond discriminators. Optional: `schema` (JSON Schema to validate `data`). |
| `segment` | A matching Segment event arrives | `request_type` (`identify`, `group`, or `track`). Optional: `event_id`. |

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
      }
    ],
    "enabled": true
  }'
```

Save the `id` from the response — you'll use it in every subsequent request.

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

Start a run. Pass a `user_id` (or `profile` with contact info) and optional `data` payload. Returns `202` with a `runId`. Courier processes the run asynchronously, validating `data` against the trigger's JSON Schema and walking through the DAG.

> **Tip:** If any downstream `fetch` node references `{{data.user_id}}` in its URL, also include `user_id` inside `data` — the top-level `user_id` is used for recipient resolution, but Courier does not guarantee it is projected into `data` for variable interpolation. Passing it both places is the safe default.

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
| AI | `type: "ai"` | `output_schema`. Optional: `model`, `user_prompt`, `web_search`, `conditions`. |
| Exit | `type: "exit"` | None. Optional: `id`. |

---

## Conditions

Several node types support a `conditions` field for conditional execution. Conditions are tuples:

**Binary (3 elements):** `[path, operator, value]`

```json
["data.plan", "is equal", "pro"]
```

**Unary (2 elements):** `[path, operator]`

```json
["data.email", "exists"]
```

### Available Operators

| Type | Operators |
|------|-----------|
| Binary | `is equal`, `is not equal`, `contains`, `does not contain`, `starts with`, `ends with`, `greater than`, `greater than or equal`, `less than`, `less than or equal` |
| Unary | `exists`, `does not exist` |

Conditions can be grouped with `AND` / `OR` logic, and groups can be nested for complex expressions.

---

## Merge Strategies (Fetch Nodes)

When a fetch node receives a response, `merge_strategy` determines how the response is incorporated into run state:

| Strategy | Behavior |
|----------|----------|
| `overwrite` | Deep-merges response into state. Response values overwrite existing fields. |
| `soft-merge` | Adds new fields from the response without overwriting existing values. |
| `replace` | Replaces the entire run state with the response. |
| `none` | Discards the response body. Useful for fire-and-forget requests. |

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
        "url": "https://api.yourapp.com/users/{{data.user_id}}/setup-status",
        "merge_strategy": "overwrite",
        "headers": { "Authorization": "Bearer {{secrets.APP_API_KEY}}" }
      },
      {
        "id": "branch-setup",
        "type": "branch",
        "paths": [
          {
            "label": "Setup complete",
            "conditions": [["data.setup_complete", "is equal", true]],
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
      "conditions": [["data.user_tier", "is equal", "high-value"]]
    }
  ],
  "enabled": true
}
```

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
| Batch/digest step (dashboard) | `throttle` node (user/global/dynamic scope) + `delay` node |
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
- [Journeys API Reference](https://www.courier.com/api-reference/journeys/create-a-journey) — endpoint reference
