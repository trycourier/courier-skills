# Templates & Elemental

## Quick Reference

### Rules
- Template IDs use the `nt_` prefix (e.g., `nt_01kmrbq6ypf25tsge12qek41r0`)
- Human-friendly aliases are optional in app code, but this skill set uses Courier-generated `nt_...` IDs as the canonical pattern for agent consistency
- Treat template IDs as opaque, workspace-specific values (they vary by environment and should not encode business meaning)
- Templates are created in **DRAFT** state by default — they must be published before sends will use them
- `PUT /notifications/{id}` is a **full replacement** — every field is required, even if unchanged; omitted fields reset to empty/null
- Elemental version string is always `"2022-01-01"`
- ElementalContentSugar (`title`/`body`) only works for inline sends — use the full Elemental format (`version` + `elements`) when creating templates via the API
- Templates created via API appear in Design Studio, and vice versa
- A template needs a `routing.strategy_id` from your workspace to route through channels — if you have existing templates, copy the value from one via `GET /notifications/{id}` or the Studio UI; if starting from scratch, create a template in the [Design Studio](https://app.courier.com/designer) first, then retrieve its `routing.strategy_id` via the API to use in programmatic template creation. You can also set `routing: null` on create and assign routing later.

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
const { notification } = await client.notifications.create({
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
  state: "PUBLISHED"
});
// notification.id → "nt_..."
```

---

## Inline vs Templated Sending

There are two ways to define notification content when calling the Send API:

| | Inline Content | Stored Template |
|--|----------------|-----------------|
| How | Pass `content` directly in the `send()` call | Pass `template` ID referencing a stored template |
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

const templateId = response.notification.id; // "nt_..."
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

template_id = response.notification.id  # "nt_..."
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
    id="nt_01abc123",
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

```typescript
const template = await client.notifications.retrieve("nt_01abc123");
```

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

Elemental is Courier's JSON-based templating language. It defines the `content` payload used in both inline sends and stored templates.

### Structure

Every Elemental template has two required fields:

```json
{
  "version": "2022-01-01",
  "elements": []
}
```

- `version` — always `"2022-01-01"` (the only supported version)
- `elements` — array of element objects

### ElementalContentSugar (Inline Sends Only)

For simple inline sends, use the shorthand:

```json
{
  "title": "Welcome!",
  "body": "Thanks for signing up, {{name}}."
}
```

Courier auto-converts this to a `meta` element (title) and a `text` element (body). This format does **not** work when creating templates via `POST /notifications` — use the full `version` + `elements` structure.

### Base Element Properties

All element types share these optional properties:

| Property | Type | Description |
|----------|------|-------------|
| `channels` | `string[]` | Restrict this element to specific channels (e.g., `["email", "push"]`) |
| `ref` | `string` | Tag the element with a name for cross-element references |
| `if` | `string` | Conditional expression — element renders only when truthy |
| `loop` | `string` | Path to an array — element renders once per item |

---

## Element Types

### meta

Sets the notification title (email subject line, push notification title).

```json
{ "type": "meta", "title": "Order #{{order_id}} Confirmed" }
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `title` | `string` | No | Title displayed by channels that support it |

### text

Body text content with optional formatting.

```json
{ "type": "text", "content": "Hi {{name}}, welcome to the platform.", "align": "left" }
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `content` | `string` | Yes | Text content (supports `{{variables}}`) |
| `align` | `"left"` \| `"center"` \| `"right"` | Yes | Text alignment |
| `text_style` | `"text"` \| `"h1"` \| `"h2"` \| `"subtext"` | No | Heading level or subtext |
| `format` | `"markdown"` | No | Enable markdown rendering (`**bold**`, `*italic*`, links) |
| `color` | `string` | No | CSS color value |
| `bold` | `string` | No | Apply bold |
| `italic` | `string` | No | Apply italic |
| `strikethrough` | `string` | No | Apply strikethrough |
| `underline` | `string` | No | Apply underline |

**Heading example:**
```json
{ "type": "text", "content": "Order Summary", "text_style": "h1", "align": "left" }
```

**Markdown example:**
```json
{ "type": "text", "content": "**Important:** Your trial ends in {{days}} days.", "format": "markdown", "align": "left" }
```

### action

Clickable button or link.

```json
{
  "type": "action",
  "content": "Reset Password",
  "href": "https://example.com/reset?token={{token}}",
  "style": "button",
  "align": "center",
  "background_color": "#1a73e8"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `content` | `string` | Yes | Button/link label |
| `href` | `string` | Yes | Target URL |
| `action_id` | `string` | No | Unique ID for tracking clicks |
| `style` | `"button"` \| `"link"` | No | Render as button (default) or text link |
| `align` | `"center"` \| `"left"` \| `"right"` \| `"full"` | No | Alignment (default: `"center"`) |
| `background_color` | `string` | No | Button background CSS color |

### image

Embedded image with optional link.

```json
{
  "type": "image",
  "src": "https://example.com/product.jpg",
  "altText": "Product photo",
  "width": "300px",
  "href": "https://example.com/products/123",
  "align": "center"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `src` | `string` | Yes | Image URL |
| `href` | `string` | No | Link URL when image is clicked |
| `altText` | `string` | No | Alt text for accessibility |
| `width` | `string` | No | CSS width (e.g., `"300px"`, `"50%"`) |
| `align` | `"center"` \| `"left"` \| `"right"` \| `"full"` | No | Image alignment |

### channel

Channel-specific content branches. When present at the top level, **all** sibling elements must also be `channel` elements.

```json
{
  "type": "channel",
  "channel": "email",
  "elements": [
    { "type": "meta", "title": "Order #{{order_id}} Confirmed" },
    { "type": "text", "content": "Full order details with images and tracking.", "align": "left" },
    { "type": "action", "content": "Track Order", "href": "{{tracking_url}}" }
  ]
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `channel` | `string` | Yes | Channel name: `"email"`, `"push"`, `"sms"`, `"direct_message"`, or a provider like `"slack"` |
| `elements` | `array` | No | Nested elements for this channel |
| `raw` | `object` | No | Raw provider-specific payload (required if `elements` is omitted) |

**Multi-channel example:**
```json
{
  "version": "2022-01-01",
  "elements": [
    {
      "type": "channel",
      "channel": "email",
      "elements": [
        { "type": "meta", "title": "Order #{{order_id}} Confirmed" },
        { "type": "text", "content": "Hi {{name}}, here are your full order details...", "align": "left" },
        { "type": "image", "src": "{{product_image}}", "altText": "{{product_name}}" },
        { "type": "action", "content": "Track Order", "href": "{{tracking_url}}" }
      ]
    },
    {
      "type": "channel",
      "channel": "sms",
      "elements": [
        { "type": "text", "content": "Order #{{order_id}} confirmed! Track: {{tracking_url}}", "align": "left" }
      ]
    },
    {
      "type": "channel",
      "channel": "push",
      "elements": [
        { "type": "meta", "title": "Order Confirmed" },
        { "type": "text", "content": "Your order #{{order_id}} is confirmed.", "align": "left" }
      ]
    }
  ]
}
```

### divider

Visual separator between content sections.

```json
{ "type": "divider" }
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `color` | `string` | No | CSS color for the line (e.g., `"#eee"`) |

### quote

Blockquote for highlighted text or testimonials.

```json
{
  "type": "quote",
  "content": "The best notification platform we've used.",
  "borderColor": "#1a73e8",
  "text_style": "text"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `content` | `string` | Yes | Quote text |
| `align` | `"center"` \| `"left"` \| `"right"` \| `"full"` | No | Alignment |
| `borderColor` | `string` | No | CSS border color |
| `text_style` | `"text"` \| `"h1"` \| `"h2"` \| `"subtext"` | Yes | Text styling |

### group

Container element for applying control flow (`if`, `loop`) to multiple elements at once.

```json
{
  "type": "group",
  "if": "data.items.length > 0",
  "elements": [
    { "type": "text", "content": "Your items:", "text_style": "h2", "align": "left" },
    { "type": "divider" }
  ]
}
```

A `group` renders its `elements` array but adds no visual output itself.

### columns / column

Multi-column layouts for email and other rich channels.

```json
{
  "type": "columns",
  "elements": [
    {
      "type": "column",
      "width": "40%",
      "elements": [
        { "type": "image", "src": "{{product_image}}", "altText": "Product" }
      ]
    },
    {
      "type": "column",
      "width": "60%",
      "elements": [
        { "type": "text", "content": "**{{product_name}}**", "format": "markdown", "align": "left" },
        { "type": "text", "content": "${{price}}", "align": "left" }
      ]
    }
  ]
}
```

`columns` contains `column` children. Each `column` has a `width` (CSS percentage or pixel value) and its own `elements` array.

### list / list-item

Ordered and unordered lists with nesting support (up to 5 levels deep).

```json
{
  "type": "list",
  "elements": [
    { "type": "list-item", "content": "Email notifications configured" },
    { "type": "list-item", "content": "SMS provider connected" },
    { "type": "list-item", "content": "Push tokens registered" }
  ]
}
```

### html

Raw HTML content for custom formatting not available through other element types. Primarily renders in email.

```json
{
  "type": "html",
  "content": "<table style=\"width:100%\"><tr><td>Item</td><td>Qty</td><td>Price</td></tr></table>"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `content` | `string` | Yes | Raw HTML markup |

### jsonnet

Programmatic content generation using Jsonnet templates. Useful for complex Slack Block Kit or Teams Adaptive Card payloads.

```json
{
  "type": "jsonnet",
  "content": "local data = std.extVar('data');\n{ blocks: [{ type: 'section', text: { type: 'mrkdwn', text: '*Order ' + data.order_id + '*' } }] }"
}
```

### comment

Non-rendered documentation within templates. Comments are stripped from the final output.

```json
{ "type": "comment", "content": "TODO: add product image after launch" }
```

---

## Control Flow

Control flow properties work on any element type, including `group` containers.

### Conditional Rendering (`if`)

The `if` expression is evaluated as JavaScript against the send `data` object:

```json
{
  "type": "text",
  "content": "As a premium member, you get early access.",
  "align": "left",
  "if": "data.tier === 'premium'"
}
```

```json
{
  "type": "action",
  "content": "Upgrade to Premium",
  "href": "https://example.com/upgrade",
  "if": "data.tier !== 'premium'"
}
```

### Iteration (`loop`)

Repeat an element for each item in an array. Use `{{$.item}}` for the current item and `{{$.index}}` for the zero-based index:

```json
{
  "type": "group",
  "loop": "data.products",
  "elements": [
    {
      "type": "text",
      "content": "{{$.item.name}} — ${{$.item.price}}",
      "align": "left"
    }
  ]
}
```

### Element References (`ref`)

Tag an element and reference it from another:

```json
[
  { "type": "text", "content": "Welcome back!", "align": "left", "ref": "greeting" },
  {
    "type": "text",
    "content": "Since you're here, check out what's new.",
    "align": "left",
    "if": "refs.greeting.visible"
  }
]
```

### Channel Filtering (`channels`)

Show an element only on specific channels without using a `channel` container:

```json
{
  "type": "image",
  "src": "https://example.com/banner.jpg",
  "altText": "Welcome banner",
  "channels": ["email"]
}
```

---

## Localization

Elements that support text content (`text`, `action`, `quote`, `meta`) accept a `locales` property for multi-language content. Courier serves the right locale based on the recipient's profile.

```json
{
  "type": "text",
  "content": "Welcome, {{name}}!",
  "align": "left",
  "locales": {
    "es": { "content": "¡Bienvenido, {{name}}!" },
    "fr": { "content": "Bienvenue, {{name}} !" },
    "de": { "content": "Willkommen, {{name}}!" }
  }
}
```

```json
{
  "type": "meta",
  "title": "Your order has shipped",
  "locales": {
    "es": { "content": "Tu pedido ha sido enviado" },
    "fr": { "content": "Votre commande a été expédiée" }
  }
}
```

For full localization setup, see [Locales](https://www.courier.com/docs/platform/content/elemental/locales).

---

## Full Lifecycle Example

End-to-end: create a multi-channel order confirmation template, publish it, then send.

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

// 1. Create the template
const { notification } = await client.notifications.create({
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

const templateId = notification.id;

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

template_id = response.notification.id

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

- [Quickstart](./quickstart.md) - Send your first notification
- [Patterns](./patterns.md) - Reusable code patterns (idempotency, retry, multi-channel)
- [Multi-Channel](./multi-channel.md) - Routing strategies and channel priority
- [CLI](./cli.md) - CLI for ad-hoc template operations (`courier notifications list`)
- [Reliability](./reliability.md) - Idempotency keys for sends using templates
- [Elemental Overview](https://www.courier.com/docs/platform/content/elemental/elemental-overview) - Full Elemental documentation
- [Elements Reference](https://www.courier.com/docs/platform/content/elemental/elements/index) - Complete element type reference
- [Templates API](https://www.courier.com/docs/platform/content/templates-api) - API endpoint reference
- [Templates API Tutorial](https://www.courier.com/docs/tutorials/content/how-to-use-templates-api) - Step-by-step walkthrough
