# Templates & Elemental

## Quick Reference

### Rules
- Template IDs use the `nt_` prefix (e.g., `nt_01kmrbq6ypf25tsge12qek41r0`)
- Human-friendly aliases are optional in app code, but this skill set uses Courier-generated `nt_...` IDs as the canonical pattern for agent consistency
- Treat template IDs as opaque, workspace-specific values (they vary by environment and should not encode business meaning)
- Templates are created in **DRAFT** state by default — they must be published before sends will use them
- **Canonical create flow is DRAFT → `notifications.publish`, not `state: "PUBLISHED"` on create.** When `state: "PUBLISHED"` is passed to `notifications.create`, the response body currently echoes `name: "Untitled"` and `tags: []` even though the template is stored correctly under the hood. Creating as DRAFT and calling `publish(id)` returns a response body whose `name`/`tags` match what you sent — safer for logging, validation, and lookup.
- `PUT /notifications/{id}` is a **full replacement** — every field is required, even if unchanged; omitted fields reset to empty/null
- Elemental version string is always `"2022-01-01"`
- ElementalContentSugar (`title`/`body`) only works for inline sends — use the full Elemental format (`version` + `elements`) when creating templates via the API
- Templates created via API appear in Design Studio, and vice versa
- A template needs a `routing.strategy_id` from your workspace to route through channels. Three ways to obtain one:
  1. **Create one programmatically** via `client.routingStrategies.create({ name, routing, channels, providers })` — returns an `rs_...` you can pass to `notifications.create`. See [routing-strategies.md](./routing-strategies.md).
  2. **Reuse an existing strategy** — copy its ID from an existing template via `GET /notifications/{id}` or list them with `client.routingStrategies.list()`.
  3. **Defer it** — set `routing: null` on create and assign a `strategy_id` later via `notifications.replace`.
- Archive a template with `DELETE /notifications/{id}` (or `client.notifications.archive(id)` in the SDK). Note: `POST /notifications/{id}/archive` does **not** exist and returns 404 — the archive operation uses the `DELETE` method.

### Common Mistakes
- Forgetting to publish after creating or updating (template exists but sends use the old published version, or fail silently if never published)
- Omitting fields on `PUT` (e.g., leaving out `tags` resets them to `[]`, leaving out `brand` resets to `null`)
- Nesting `channel` elements inside other `channel` elements (they must be top-level siblings)
- Using Sugar format (`title`/`body`) in template creation payloads (only works for inline sends via the Send API)
- Missing `routing.strategy_id` on create (template will exist but sends may fail routing)
- Sending to a template that has never been published (draft content is not used at send time)

### Templates

**Create and publish a template (TypeScript):**
```typescript
// 1. Create as DRAFT so the response echoes your name/tags correctly.
const template = await client.notifications.create({
  notification: {
    name: "Order Shipped",
    tags: ["transactional", "orders"],
    brand: null,
    subscription: null,
    routing: { strategy_id: "rs_..." },
    content: {
      version: "2022-01-01",
      elements: [
        { type: "meta", title: "Your order {{order_id}} has shipped" },
        { type: "text", content: "Hi {{name}}, your package is on the way." },
        { type: "action", content: "Track Shipment", href: "{{tracking_url}}" }
      ]
    }
  },
  state: "DRAFT"
});
// template.id → "nt_...", template.name === "Order Shipped", template.tags === [...]
//   (response fields are returned at the top level)

// 2. Publish it so sends use the new content.
await client.notifications.publish(template.id);
```

> Passing `state: "PUBLISHED"` to `create` also works and stores the template correctly, but the immediate response body echoes `name: "Untitled"` and `tags: []` even though a subsequent `GET /notifications/{id}` shows the real values. Prefer the DRAFT → `publish` flow above so the response you log/assert on matches what you sent.

---

## Inline vs Templated Sending

There are two ways to define notification content when calling the Send API:

| | Inline Content | Stored Template |
|--|----------------|-----------------|
| How | Pass `content` directly in the `client.send.message()` call | Pass `template` ID referencing a stored template |
| Content lives | In your code | In Courier (API-created or Design Studio) |
| Editable in dashboard | No | Yes |
| Version history | No | Yes (draft/publish cycle) |
| Approval workflows | No | Yes (submission checks) |
| Best for | Prototyping, ad-hoc sends, AI agent workflows, simple notifications | Production notifications, team-managed content, multi-channel templates |

**Inline send (content in code):**
```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    content: {
      title: "Your order has shipped",
      body: "Hi {{name}}, your package is on the way."
    },
    data: { name: "Jane" }
  }
});
```

**Templated send (reference stored template):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbq6ypf25tsge12qek41r0",
    data: { name: "Jane", order_id: "ORD-9042", tracking_url: "https://example.com/track/ORD-9042" }
  }
});
```

Inline sends support both ElementalContentSugar (`title`/`body`) and the full Elemental format (`version` + `elements`). Stored templates always use the full Elemental format.

---

## Template Aliases (Optional)

Courier APIs send by template ID (`nt_...`). For agent-generated code, keep `nt_...` as the default.

Aliases are an application-layer convenience that map a stable human name to a real template ID.

### Why aliases can help

- Easier to read in app code (`"order-shipped"` vs long ID)
- Safer refactors (swap the mapped ID without touching call sites)
- Useful per-environment mapping (dev/staging/prod can point to different IDs)

### TypeScript alias map example

```typescript
const TEMPLATE_IDS = {
  "order-shipped": "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
  "password-reset": "nt_01kmrbzj3q6x9v2d5c8n1w4ht",
} as const;

type TemplateAlias = keyof typeof TEMPLATE_IDS;

function resolveTemplate(alias: TemplateAlias): string {
  return TEMPLATE_IDS[alias];
}

await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: resolveTemplate("order-shipped"),
    data: { order_id: "ORD-9042" },
  },
});
```

### Python alias map example

```python
TEMPLATE_IDS = {
    "order-shipped": "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    "password-reset": "nt_01kmrbzj3q6x9v2d5c8n1w4ht",
}

def resolve_template(alias: str) -> str:
    return TEMPLATE_IDS[alias]

client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": resolve_template("order-shipped"),
        "data": {"order_id": "ORD-9042"},
    }
)
```

### Agent guidance

- Prefer direct `nt_...` IDs in generated examples unless the user explicitly asks for aliases.
- If aliases are used, always resolve them to `nt_...` before calling Courier.
- Do not assume a global alias registry exists unless the user provides one.

---

## Template CRUD — the Notifications API

All template operations use the `/notifications` endpoints. Authenticate with `Authorization: Bearer $COURIER_API_KEY`.

### API Overview

| Operation | Method | Endpoint | Description |
|-----------|--------|----------|-------------|
| List | `GET` | `/notifications` | Paginated list of all templates |
| Create | `POST` | `/notifications` | Create a new template (DRAFT or PUBLISHED) |
| Get | `GET` | `/notifications/{id}` | Retrieve a template by ID |
| Replace | `PUT` | `/notifications/{id}` | Full replacement of a template |
| Archive | `DELETE` | `/notifications/{id}` | Archive (soft-delete) a template |
| Publish | `POST` | `/notifications/{id}/publish` | Publish the current draft |
| Get content | `GET` | `/notifications/{id}/content` | Get published content blocks |
| Get draft | `GET` | `/notifications/{id}/draft/content` | Get draft content blocks |
| List versions | `GET` | `/notifications/{id}/versions` | Version history |

### Create a Template

Templates require a `notification` object with `name`, `tags`, `brand`, `subscription`, `routing`, and `content` — all fields are required. Set `state` to `"PUBLISHED"` to skip the draft step, or omit/set to `"DRAFT"` (default).

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

const response = await client.notifications.create({
  notification: {
    name: "Shipping Update",
    tags: ["transactional", "orders"],
    brand: null,
    subscription: null,
    routing: { strategy_id: "rs_..." },
    content: {
      version: "2022-01-01",
      elements: [
        { type: "meta", title: "Your order {{order_id}} has shipped" },
        {
          type: "text",
          content: "Hi {{name}}, your package is on the way. Tracking: {{tracking_url}}."
        },
        { type: "action", content: "Track Shipment", href: "{{tracking_url}}" }
      ]
    }
  },
  state: "DRAFT"
});

const templateId = response.id; // "nt_..." (response fields are at the top level)
```

**Python:**
```python
from courier import Courier

client = Courier()

response = client.notifications.create(
    notification={
        "name": "Shipping Update",
        "tags": ["transactional", "orders"],
        "brand": None,
        "subscription": None,
        "routing": {"strategy_id": "rs_..."},
        "content": {
            "version": "2022-01-01",
            "elements": [
                {"type": "meta", "title": "Your order {{order_id}} has shipped"},
                {
                    "type": "text",
                    "content": "Hi {{name}}, your package is on the way. Tracking: {{tracking_url}}.",
                },
                {"type": "action", "content": "Track Shipment", "href": "{{tracking_url}}"},
            ],
        },
    },
    state="DRAFT",
)

template_id = response.id  # "nt_..." (response fields are at the top level)
```

**curl:**
```bash
curl -X POST "https://api.courier.com/notifications" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "notification": {
      "name": "Shipping Update",
      "tags": ["transactional", "orders"],
      "brand": null,
      "subscription": null,
      "routing": { "strategy_id": "rs_..." },
      "content": {
        "version": "2022-01-01",
        "elements": [
          { "type": "meta", "title": "Your order {{order_id}} has shipped" },
          { "type": "text", "content": "Hi {{name}}, your package is on the way. Tracking: {{tracking_url}}." },
          { "type": "action", "content": "Track Shipment", "href": "{{tracking_url}}" }
        ]
      }
    },
    "state": "DRAFT"
  }'
```

**Minimal create** (empty template, DRAFT):

**TypeScript:**
```typescript
await client.notifications.create({
  notification: {
    name: "Placeholder",
    tags: [],
    brand: null,
    subscription: null,
    routing: null,
    content: { version: "2022-01-01", elements: [] }
  }
});
```

**Python:**
```python
client.notifications.create(
    notification={
        "name": "Placeholder",
        "tags": [],
        "brand": None,
        "subscription": None,
        "routing": None,
        "content": {"version": "2022-01-01", "elements": []},
    },
)
```

### Replace a Template

`PUT` replaces the entire template. You must send **all fields** — any field you omit resets to its default. This is not a partial update.

**TypeScript:**
```typescript
await client.notifications.replace("nt_01abc123", {
  notification: {
    name: "Shipping Update v2",
    tags: ["transactional", "orders"],
    brand: null,
    subscription: { topic_id: "order-updates" },
    routing: { strategy_id: "rs_..." },
    content: {
      version: "2022-01-01",
      elements: [
        { type: "meta", title: "Order {{order_id}} shipped — arriving {{eta}}" },
        { type: "text", content: "Hi {{name}}, your package shipped via {{carrier}}." },
        { type: "action", content: "Track Shipment", href: "{{tracking_url}}" }
      ]
    }
  },
  state: "DRAFT"
});
```

**Python:**
```python
client.notifications.replace(
    "nt_01abc123",
    notification={
        "name": "Shipping Update v2",
        "tags": ["transactional", "orders"],
        "brand": None,
        "subscription": {"topic_id": "order-updates"},
        "routing": {"strategy_id": "rs_..."},
        "content": {
            "version": "2022-01-01",
            "elements": [
                {"type": "meta", "title": "Order {{order_id}} shipped — arriving {{eta}}"},
                {"type": "text", "content": "Hi {{name}}, your package shipped via {{carrier}}."},
                {"type": "action", "content": "Track Shipment", "href": "{{tracking_url}}"},
            ],
        },
    },
    state="DRAFT",
)
```

**curl:**
```bash
curl -X PUT "https://api.courier.com/notifications/nt_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "notification": {
      "name": "Shipping Update v2",
      "tags": ["transactional", "orders"],
      "brand": null,
      "subscription": { "topic_id": "order-updates" },
      "routing": { "strategy_id": "rs_..." },
      "content": {
        "version": "2022-01-01",
        "elements": [
          { "type": "meta", "title": "Order {{order_id}} shipped — arriving {{eta}}" },
          { "type": "text", "content": "Hi {{name}}, your package shipped via {{carrier}}." },
          { "type": "action", "content": "Track Shipment", "href": "{{tracking_url}}" }
        ]
      }
    },
    "state": "DRAFT"
  }'
```

### Publish

Publishing moves the current draft to live. After publishing, sends that reference this template ID will use the newly published content.

**TypeScript:**
```typescript
await client.notifications.publish("nt_01abc123");
```

**Python:**
```python
client.notifications.publish("nt_01abc123")
```

**curl:**
```bash
curl -X POST "https://api.courier.com/notifications/nt_01abc123/publish" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Returns `204 No Content` on success.

### List Templates

**TypeScript:**
```typescript
const { results, paging } = await client.notifications.list();

for (const template of results) {
  console.log(template.id, template.title);
}
```

**Python:**
```python
response = client.notifications.list()

for template in response.results:
    print(template.id, template.title)
```

**CLI:**
```bash
courier notifications list --format json --transform "results.#.id"
```

**curl:**
```bash
curl -s "https://api.courier.com/notifications" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

Paginated — use `paging.cursor` for the next page.

### Get a Template

**TypeScript:**
```typescript
const template = await client.notifications.retrieve("nt_01abc123");
```

**Python:**
```python
template = client.notifications.retrieve("nt_01abc123")
```

**curl:**
```bash
curl -s "https://api.courier.com/notifications/nt_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

### Get Published Content

Inspect the live content blocks of a template:

```typescript
const content = await client.notifications.retrieveContent("nt_01abc123");
```

```bash
curl -s "https://api.courier.com/notifications/nt_01abc123/content" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

### Get Draft Content

Inspect the draft before publishing:

```bash
curl -s "https://api.courier.com/notifications/nt_01abc123/draft/content" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

### List Versions

Audit what was published and when:

```bash
curl -s "https://api.courier.com/notifications/nt_01abc123/versions" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

### Archive a Template

Archiving removes the template from normal catalog flows. Returns `204 No Content`.

```typescript
await client.notifications.archive("nt_01abc123");
```

```bash
curl -X DELETE "https://api.courier.com/notifications/nt_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

### Draft/Publish Workflow

Templates have a two-phase lifecycle:

```
Create (DRAFT) → Edit (Replace) → Publish → Live
                      ↑                        |
                      └── Edit again ──────────┘
```

1. **Create** with `state: "DRAFT"` (or omit `state`)
2. **Iterate** using `PUT /notifications/{id}` — the draft updates but the published version stays unchanged
3. **Review** the draft with `GET /notifications/{id}/draft/content`
4. **Publish** with `POST /notifications/{id}/publish` — the draft becomes the live version
5. **Verify** with `GET /notifications/{id}/content`

To skip the draft step entirely, set `state: "PUBLISHED"` on create or replace.

### Submission Checks (Approval Workflows)

Templates support approval workflows via submission checks. When enabled, publishing requires external review — Courier emits webhooks on submission, locks the draft, and publishes only after checks are resolved via the checks API (`GET/PUT/DELETE /notifications/{id}/{submissionId}/checks`). See [Template Approval Workflow](https://www.courier.com/docs/platform/content/template-approval-workflow) for setup.

---

## Elemental Content Format

Template `content` uses Courier's JSON-based templating language, **Elemental**. Every payload has two required fields (`version` and `elements`), plus an optional shorthand (`{ title, body }`) for inline sends only.

For the full element-by-element reference — all element types, properties, control flow (`if`, `loop`, `ref`, `channels`), and localization — see **[Elemental](./elemental.md)**. The example below uses Elemental; consult the Elemental guide when you need more than `meta`, `text`, `action`, and `channel`.

<!-- OLD ELEMENTAL REFERENCE REMOVED — moved to elemental.md. Keep this pointer. -->

<details>
<summary>Minimal Elemental shape (for context)</summary>

```json
{
  "version": "2022-01-01",
  "elements": [
    { "type": "meta", "title": "Order #{{order_id}} Confirmed" },
    { "type": "text", "content": "Hi {{name}}, thanks for your order.", "align": "left" },
    { "type": "action", "content": "Track", "href": "{{tracking_url}}" }
  ]
}
```

Inline sends also accept the shorthand `{ "title": "…", "body": "…" }`. **Not** valid for template creation via `POST /notifications` — the full `version` + `elements` shape is required.

</details>

<!-- ELEMENTAL_REFERENCE_START
     The detailed element reference that was here has been moved to elemental.md
     to keep this file focused on the template lifecycle. Do not re-inline it.
ELEMENTAL_REFERENCE_END -->

<details>
<summary>Skipped here: full element reference</summary>

The previous version of this file inlined ~425 lines covering every element type (`meta`, `text`, `action`, `image`, `channel`, `divider`, `quote`, `group`, `columns`/`column`, `list`/`list-item`, `html`, `jsonnet`, `comment`), all control-flow properties (`if`, `loop`, `ref`, `channels`), and the `locales` shape. That content now lives in [Elemental](./elemental.md). Fetch that file when you need element-specific details.

</details>

### Base Element Properties (quick recap)

All element types share four optional properties: `channels`, `ref`, `if`, and `loop`. See [Elemental](./elemental.md) for their semantics and examples.

---

## Element Types (reference moved)

Detailed per-element documentation (all types, properties, examples) lives in [Elemental](./elemental.md). Fetch that file when the user asks about specific element types.

Element types and their properties are documented in [Elemental](./elemental.md):

- Content: `meta`, `text`, `action`, `image`, `divider`, `quote`
- Containers: `channel`, `group`, `columns` / `column`, `list` / `list-item`
- Escape hatches: `html`, `jsonnet`, `comment`

## Control Flow (reference moved)

Conditional rendering (`if`), iteration (`loop`), element references (`ref`), and channel filtering (`channels`) are documented in [Elemental](./elemental.md).

## Localization (reference moved)

The `locales` property on `text`, `action`, `quote`, and `meta` elements is documented in [Elemental](./elemental.md). For full localization setup, see the official [Locales](https://www.courier.com/docs/platform/content/elemental/locales) docs.

---

## Full Lifecycle Example

End-to-end: create a multi-channel order confirmation template, publish it, then send.

> **Step 0 (optional) — create a routing strategy if you don't already have one:**
>
> TypeScript:
> ```typescript
> const strategy = await client.routingStrategies.create({
>   name: "Orders — email + SMS fallback",
>   routing: { method: "single", channels: ["email", "sms"] },
>   channels: {
>     email: { providers: ["sendgrid", "aws-ses"] },
>     sms: { providers: ["twilio"] }
>   }
> });
> // then use strategy.id as routing.strategy_id below
> ```
>
> Python:
> ```python
> strategy = client.routing_strategies.create(
>     name="Orders — email + SMS fallback",
>     routing={"method": "single", "channels": ["email", "sms"]},
>     channels={
>         "email": {"providers": ["sendgrid", "aws-ses"]},
>         "sms": {"providers": ["twilio"]},
>     },
> )
> # then use strategy.id as routing["strategy_id"] below
> ```
>
> See [routing-strategies.md](./routing-strategies.md) for the full CRUD lifecycle.

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

// 1. Create the template
const template = await client.notifications.create({
  notification: {
    name: "Order Confirmation",
    tags: ["transactional", "orders"],
    brand: null,
    subscription: null,
    routing: { strategy_id: "rs_..." },
    content: {
      version: "2022-01-01",
      elements: [
        {
          type: "channel",
          channel: "email",
          elements: [
            { type: "meta", title: "Order #{{order_id}} Confirmed" },
            { type: "text", content: "Hi {{name}}, thanks for your order!", align: "left" },
            {
              type: "group",
              loop: "data.items",
              elements: [
                { type: "text", content: "• {{$.item.name}} × {{$.item.qty}} — ${{$.item.price}}", align: "left" }
              ]
            },
            { type: "divider" },
            { type: "text", content: "Total: ${{total}}", text_style: "h2", align: "left" },
            { type: "action", content: "Track Order", href: "{{tracking_url}}" }
          ]
        },
        {
          type: "channel",
          channel: "sms",
          elements: [
            { type: "text", content: "Order #{{order_id}} confirmed! Total: ${{total}}. Track: {{tracking_url}}", align: "left" }
          ]
        }
      ]
    }
  },
  state: "DRAFT"
});

const templateId = template.id; // response fields are at the top level

// 2. Publish
await client.notifications.publish(templateId);

// 3. Send using the template
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: templateId,
    data: {
      order_id: "ORD-9042",
      name: "Jane",
      items: [
        { name: "Courier Hoodie", qty: 1, price: "59.00" },
        { name: "Sticker Pack", qty: 2, price: "9.00" }
      ],
      total: "77.00",
      tracking_url: "https://example.com/track/ORD-9042"
    }
  }
});
```

**Python:**
```python
from courier import Courier

client = Courier()

# 1. Create the template
response = client.notifications.create(
    notification={
        "name": "Order Confirmation",
        "tags": ["transactional", "orders"],
        "brand": None,
        "subscription": None,
        "routing": {"strategy_id": "rs_..."},
        "content": {
            "version": "2022-01-01",
            "elements": [
                {
                    "type": "channel",
                    "channel": "email",
                    "elements": [
                        {"type": "meta", "title": "Order #{{order_id}} Confirmed"},
                        {"type": "text", "content": "Hi {{name}}, thanks for your order!", "align": "left"},
                        {
                            "type": "group",
                            "loop": "data.items",
                            "elements": [
                                {"type": "text", "content": "• {{$.item.name}} × {{$.item.qty}} — ${{$.item.price}}", "align": "left"}
                            ],
                        },
                        {"type": "divider"},
                        {"type": "text", "content": "Total: ${{total}}", "text_style": "h2", "align": "left"},
                        {"type": "action", "content": "Track Order", "href": "{{tracking_url}}"},
                    ],
                },
                {
                    "type": "channel",
                    "channel": "sms",
                    "elements": [
                        {"type": "text", "content": "Order #{{order_id}} confirmed! Total: ${{total}}. Track: {{tracking_url}}", "align": "left"}
                    ],
                },
            ],
        },
    },
    state="DRAFT",
)

template_id = response.id  # response fields are at the top level

# 2. Publish
client.notifications.publish(template_id)

# 3. Send using the template
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": template_id,
        "data": {
            "order_id": "ORD-9042",
            "name": "Jane",
            "items": [
                {"name": "Courier Hoodie", "qty": 1, "price": "59.00"},
                {"name": "Sticker Pack", "qty": 2, "price": "9.00"},
            ],
            "total": "77.00",
            "tracking_url": "https://example.com/track/ORD-9042",
        },
    }
)
```

---

## Workspace vs Tenant Templates

This guide covers **workspace templates** — the `/notifications/...` endpoints. These are the templates visible in your Courier dashboard and shared across all tenants.

For **per-tenant templates** (Courier Create), use the `/tenants/{tenant_id}/templates/...` endpoints. See the [Courier Create API](https://www.courier.com/docs/platform/create/courier-create-api) and [Courier Create tutorial](https://www.courier.com/docs/tutorials/content/how-to-use-courier-create-api) for those routes.

## Related

- [Elemental](./elemental.md) - Full element-type reference (moved out of this file)
- [Quickstart](./quickstart.md) - Send your first notification
- [Patterns](./patterns.md) - Reusable code patterns (idempotency, retry, multi-channel)
- [Routing Strategies](./routing-strategies.md) - Create/list/replace `rs_...` routing strategies via API
- [Providers](./providers.md) - Configure provider integrations (SendGrid, Twilio, etc.) via API
- [Multi-Channel](./multi-channel.md) - Routing strategies and channel priority
- [CLI](./cli.md) - CLI for ad-hoc template operations (`courier notifications list`)
- [Reliability](./reliability.md) - Idempotency keys for sends using templates
- [Elemental Overview](https://www.courier.com/docs/platform/content/elemental/elemental-overview) - Full Elemental documentation
- [Elements Reference](https://www.courier.com/docs/platform/content/elemental/elements/index) - Complete element type reference
- [Templates API](https://www.courier.com/docs/platform/content/templates-api) - API endpoint reference
- [Templates API Tutorial](https://www.courier.com/docs/tutorials/content/how-to-use-templates-api) - Step-by-step walkthrough

<!-- Target line budget: <= 750 lines. If you are about to push this past 800, split further rather than letting it grow. Elemental reference lives in elemental.md. -->
<!-- Target line budget (elemental.md): <= 500 lines. -->

