# Templates & Elemental

## Quick Reference

### Rules
- Template IDs use the `nt_` prefix (e.g., `nt_01kmrbq6ypf25tsge12qek41r0`)
- Human-friendly aliases are optional in app code, but this skill set uses Courier-generated `nt_...` IDs as the canonical pattern for agent consistency
- Treat template IDs as opaque, workspace-specific values (they vary by environment and should not encode business meaning)
- Templates are created in **DRAFT** state by default. They must be published before sends will use them
- **Canonical create flow is DRAFT → `notifications.publish`, not `state: "PUBLISHED"` on create.** When `state: "PUBLISHED"` is passed to `notifications.create`, the response body currently echoes `name: "Untitled"` and `tags: []` even though the template is stored correctly under the hood. Creating as DRAFT and calling `publish(id)` returns a response body whose `name`/`tags` match what you sent, safer for logging, validation, and lookup.
- `PUT /notifications/{id}` is a **full replacement**, every field is required, even if unchanged; omitted fields reset to empty/null
- Elemental version string is always `"2022-01-01"`
- ElementalContentSugar (`title`/`body`) only works for inline sends. Use the full Elemental format (`version` + `elements`) when creating templates via the API
- Templates created via API appear in Design Studio, and vice versa
- A template needs a `routing.strategy_id` from your workspace to route through channels. Three ways to obtain one:
  1. **Create one programmatically** via `client.routingStrategies.create({ name, routing, channels, providers })`, returns an `rs_...` you can pass to `notifications.create`. See [routing-strategies.md](./routing-strategies.md).
  2. **Reuse an existing strategy:** copy its ID from an existing template via `GET /notifications/{id}` or list them with `client.routingStrategies.list()`.
  3. **Defer it**. Set `routing: null` on create and assign a `strategy_id` later via `notifications.replace`.
- Archive a template with `DELETE /notifications/{id}` (or `client.notifications.archive(id)` in the SDK). Note: `POST /notifications/{id}/archive` does **not** exist and returns 404, the archive operation uses the `DELETE` method.
- Confirm final visuals from a rendered test send — `GET /messages/{id}/output` returns the exact email recipients receive (see [Verify the Rendered Output](#verify-the-rendered-output))
- Managing templates from a repo (CI, drift detection, promotion): see [Templates as Code](./templates-as-code.md)

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

## Template Aliases (moved)

Human-friendly alias maps for template IDs — why, TypeScript/Python examples, and agent guidance — live in [Templates as Code](./templates-as-code.md#template-aliases-in-application-code). For agent-generated code, keep `nt_...` IDs as the default and resolve aliases to `nt_...` before calling Courier.

---

## Template CRUD, the Notifications API

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
| Get content | `GET` | `/notifications/{id}/content` | Content blocks. `?version=` accepts `draft`, `published` (default), or `vNNN` |
| **Upload content** | `PUT` | `/notifications/{id}/content` | Replace a template's content only, leaves name, tags, and routing untouched |
| Update one element | `PUT` | `/notifications/{id}/elements/{elementId}` | Update a single element (V2/Elemental templates only) |
| List versions | `GET` | `/notifications/{id}/versions` | Version history |

### Create a Template

Templates require a `notification` object with `name`, `tags`, `brand`, `subscription`, `routing`, and `content`, all fields are required. Set `state` to `"PUBLISHED"` to skip the draft step, or omit/set to `"DRAFT"` (default).

`brand` is required on create: an object (`{"id": "..."}`) or `null` (no brand chrome on template sends). Resolution rules and unbranded sending: [Brands](./brands.md).

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

`PUT` replaces the entire template. You must send **all fields**, any field you omit resets to its default. This is not a partial update.

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

### Upload Content to an Existing Template

`putContent` replaces just the **content** of a template, its Elemental `elements`, without touching name, tags, brand, subscription, or routing. Reach for it when you're syncing template bodies from code (a CMS export, a generated layout) and don't want to resend the whole `notification` object as `replace` requires. It writes to the **draft** by default (`state` defaults to `"DRAFT"`), so publish afterward to go live.

**TypeScript:**
```typescript
await client.notifications.putContent("nt_01abc123", {
  content: {
    version: "2022-01-01",
    elements: [
      { type: "meta", title: "Your order {{order_id}} has shipped" },
      { type: "text", content: "Hi {{name}}, your package is on the way." },
      { type: "action", content: "Track Shipment", href: "{{tracking_url}}" }
    ]
  }
});
await client.notifications.publish("nt_01abc123");
```

**Python:**
```python
client.notifications.put_content(
    "nt_01abc123",
    content={
        "version": "2022-01-01",
        "elements": [
            {"type": "meta", "title": "Your order {{order_id}} has shipped"},
            {"type": "text", "content": "Hi {{name}}, your package is on the way."},
            {"type": "action", "content": "Track Shipment", "href": "{{tracking_url}}"},
        ],
    },
)
client.notifications.publish("nt_01abc123")
```

To change a single element instead of the whole body, `client.notifications.putElement(elementId, { id, type, data, state })` updates one element in place (V2/Elemental templates only). Element `id`s and checksums make templates safe to share between agents and Design Studio users: `putElement` targets exactly one element by `id`, and a changed checksum tells you a teammate edited it since you last read — so you can detect their edits before overwriting them. For per-locale content, `client.notifications.putLocale(...)`. See [Localization](./elemental.md#localization).

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

### Verify the Rendered Output

`GET /messages/{id}/output` returns exactly what Courier rendered and handed to the delivery provider — subject, HTML, and plain-text part, per channel. This makes end-to-end verification a first-class workflow: send a test, fetch the output, and confirm the email is precisely what you intended.

```
POST /send  →  requestId  →  GET /messages/{requestId}/output  →  results[].content.html
```

The response is the real thing — merge variables resolved, brand chrome applied, channel formatting done — so you can assert on it programmatically. Each entry in `results[]` carries `channel` and a `content` object: for email, `subject`, `html`, and `text`; other channels use `title`/`body` (and `blocks` for chat channels). It's the definitive release sign-off for visual details like image dimensions and typography: template sends render the *published* version, so publish, send a test to yourself, and confirm the output before real recipients see it. It pairs naturally with the Design Studio — arrange and iterate on the canvas, then confirm the final render here.

The same operation in each interface: REST `GET /messages/{id}/output` · SDK `client.messages.content(messageId)` · CLI `courier messages content --message-id`. For a single-recipient send the `requestId` doubles as the message id; list and audience sends fan out to one message per recipient — resolve their ids with `courier messages list --trace-id "<requestId>"` (see [CLI](./cli.md)).

Rendered output becomes available once the message renders — a send is accepted as `ENQUEUED` first, so if the call 404s or `results` is empty immediately after sending, re-check after a few seconds (see [Reliability](./reliability.md) for status semantics).

Tip: a stored template's plain-text part is delivered as stored — Handlebars variables are not rendered in it — so write the text part as final copy and keep `{{variables}}` in the Elemental/HTML content.

### List Templates

**TypeScript:**
```typescript
const { results, paging } = await client.notifications.list();

for (const template of results) {
  // V2 templates expose `name`; legacy templates expose `title`. Fall back across both.
  console.log(template.id, (template as any).name ?? (template as any).title);
}
```

**Python:**
```python
response = client.notifications.list()

for template in response.results:
    # V2 templates expose `name`; legacy templates expose `title`. Fall back across both.
    print(template.id, getattr(template, "name", None) or getattr(template, "title", None))
```

**CLI:**
```bash
courier notifications list --format json --transform "results.#.id"
# Names: prefer `name` (V2). For workspaces with a mix of V2 and legacy templates,
# request both fields and pick whichever is populated:
courier notifications list --format json --transform "results.#.{id:id,name:name,title:title}"
```

**curl:**
```bash
curl -s "https://api.courier.com/notifications" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

Paginated. Use `paging.cursor` for the next page.

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

### Get Content (published, draft, or any version)

One endpoint serves every version of a template's content — `version` accepts `draft`,
`published` (the default), or a historical `vNNN`:

```typescript
const live = await client.notifications.retrieveContent("nt_01abc123");
const draft = await client.notifications.retrieveContent("nt_01abc123", { version: "draft" });
const v1 = await client.notifications.retrieveContent("nt_01abc123", { version: "v001" });
```

```bash
curl -s "https://api.courier.com/notifications/nt_01abc123/content?version=draft" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

The response is the content document (`version` + `elements`, with per-element checksums).

### List Versions and Roll Back

Every publish is preserved in version history, so you can ship with confidence — any prior release is one call away.

```typescript
const versions = await client.notifications.listVersions("nt_01abc123");
```

```bash
curl -s "https://api.courier.com/notifications/nt_01abc123/versions" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

Returns `draft`, the current `published:vNNN`, and every historical `vNNN` (paginated, up to 10 per page — use the `cursor` parameter for older history). Inspect any version's content before restoring it with `GET /notifications/{id}/content?version=v001`, then roll back by republishing the version you want:

```typescript
await client.notifications.publish("nt_01abc123", { version: "v001" });
```

```bash
curl -X POST "https://api.courier.com/notifications/nt_01abc123/publish" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"version": "v001"}'
```

History is append-only: republishing v001 mints a fresh version (a copy of v001) rather than moving a pointer, so the audit trail always tells the complete story — rollbacks included.

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
2. **Iterate** using `PUT /notifications/{id}`, the draft updates but the published version stays unchanged
3. **Review** the draft with `GET /notifications/{id}/content?version=draft`
4. **Publish** with `POST /notifications/{id}/publish`, the draft becomes the live version
5. **Verify** with `GET /notifications/{id}/content`

To skip the draft step entirely, set `state: "PUBLISHED"` on create or replace.

Sends always use the published version — drafts iterate freely, and publish is the release step.

### Submission Checks (Approval Workflows)

Templates support approval workflows via submission checks. When enabled, publishing requires external review. Courier emits webhooks on submission, locks the draft, and publishes only after checks are resolved via the checks API (`GET/PUT/DELETE /notifications/{id}/{submissionId}/checks`). See [Template Approval Workflow](https://www.courier.com/docs/platform/content/template-approval-workflow) for setup.

---

## Elemental Content Format

Template `content` uses Courier's JSON-based templating language, **Elemental**. Every payload has two required fields (`version` and `elements`), plus an optional shorthand (`{ title, body }`) for inline sends only.

For the full element-by-element reference, all element types, properties, control flow (`if`, `loop`, `ref`, `channels`), and localization. See **[Elemental](./elemental.md)**. The example below uses Elemental; consult the Elemental guide when you need more than `meta`, `text`, `action`, and `channel`.

<!-- OLD ELEMENTAL REFERENCE REMOVED, moved to elemental.md. Keep this pointer. -->

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

Inline sends also accept the shorthand `{ "title": "…", "body": "…" }`. **Not** valid for template creation via `POST /notifications`, the full `version` + `elements` shape is required.

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

> **Step 0 (optional). Create a routing strategy if you don't already have one:**
>
> TypeScript:
> ```typescript
> const strategy = await client.routingStrategies.create({
>   name: "Orders, email + SMS fallback",
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
>     name="Orders, email + SMS fallback",
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
const { requestId } = await client.send.message({
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

// 4. Verify the rendered output — the exact email the recipient receives
//    (single send: the requestId doubles as the message id)
const output = await client.messages.content(requestId);
// output.results[].content → { subject, html, text } — see "Verify the Rendered Output"
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
send_response = client.send.message(
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

# 4. Verify the rendered output — the exact email the recipient receives
#    (single send: the request_id doubles as the message id)
output = client.messages.content(send_response.request_id)
# output.results[].content → subject, html, text — see "Verify the Rendered Output"
```

---

## Workspace vs Tenant Templates

This guide covers **workspace templates**, the `/notifications/...` endpoints. These are the templates visible in your Courier dashboard and shared across all tenants.

For **per-tenant templates** (Courier Create), use the `/tenants/{tenant_id}/templates/...` endpoints. See the [Courier Create API](https://www.courier.com/docs/platform/create/courier-create-api) and [Courier Create tutorial](https://www.courier.com/docs/tutorials/content/how-to-use-courier-create-api) for those routes.

## Related

- [Templates as Code](./templates-as-code.md) - Run templates like software releases: repo as source of truth, CI validation, drift detection, verified releases, rollback
- [Journeys](./journeys.md) - Use templates in multi-step flows (journey-scoped templates)
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
<!-- Target line budget (elemental.md): see the footer comment in elemental.md itself. -->

