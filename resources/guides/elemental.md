# Elemental Content Format

Elemental is Courier's JSON-based templating language. It defines the `content` payload used in both inline sends and stored templates.

> **Where to read what:** This file is the element-by-element reference. For the **template lifecycle** (create, publish, version, archive via `/notifications`) and inline-vs-templated decision, see [Templates](./templates.md). For a full end-to-end example combining both, see the "Full Lifecycle Example" section in [Templates](./templates.md).

## Quick Reference

### Rules
- Every Elemental payload has exactly two required top-level fields: `version` and `elements`.
- `version` is always `"2022-01-01"` (the only supported version).
- The shorthand `{ title, body }` (ElementalContentSugar) only works for **inline sends** — never for template creation via the API.
- When `channel` elements appear at the top level, **every** top-level sibling must also be a `channel` element.
- Control flow (`if`, `loop`, `ref`, `channels`) works on any element type.

### Common Mistakes
- Nesting `channel` elements inside other `channel` elements (they must be top-level siblings).
- Using Sugar `{ title, body }` inside `POST /notifications` payloads (the API expects the full `version` + `elements` form).
- The `text` element supports an `align` property (`"left"`, `"center"`, `"right"`). It defaults to `"left"` when omitted, but including it explicitly is recommended to avoid ambiguity across renderers.
- Using `loop` without a `group` wrapper when you need to repeat multiple elements per item.
- Placing `raw` provider payloads outside a `channel` element.

---

## Structure

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
{ "type": "comment", "content": "Stripped at render time — use for template author notes, like 'add product image after launch'" }
```

---

## Control Flow

Control flow properties work on any element type, including `group` containers.

### Conditional Rendering (`if`)

The `if` expression is evaluated as **Jsonnet** against the send `data` object (not JavaScript). Use Jsonnet equality (`==`, `!=`), logical operators (`&&`, `||`, `!`), and string literals in single quotes. The other common pitfall is triple-equals (`===`) — that's JavaScript-only and will fail to parse.

```json
{
  "type": "text",
  "content": "As a premium member, you get early access.",
  "align": "left",
  "if": "data.tier == 'premium'"
}
```

```json
{
  "type": "action",
  "content": "Upgrade to Premium",
  "href": "https://example.com/upgrade",
  "if": "data.tier != 'premium'"
}
```

```json
{
  "type": "text",
  "content": "Reminder: your trial ends soon.",
  "align": "left",
  "if": "data.trial == true && data.days_left <= 3"
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

The `meta` element carries `title` (used as the email subject and push/chat title), so its `locales` entries override `title` — not `content`:

```json
{
  "type": "meta",
  "title": "Your order has shipped",
  "locales": {
    "es": { "title": "Tu pedido ha sido enviado" },
    "fr": { "title": "Votre commande a été expédiée" }
  }
}
```

For full localization setup, see the official [Locales](https://www.courier.com/docs/platform/content/elemental/locales) docs and the [Translations API](https://www.courier.com/docs/api-reference/translations/get-a-translation) for workspace-wide string management.

## Related

- [Templates](./templates.md) — template lifecycle (create, publish, version, archive) and inline-vs-templated decisions
- [Multi-Channel](./multi-channel.md) — routing strategies for the top-level `channel` elements
- [Quickstart](./quickstart.md) — send your first notification
- [Elemental Overview](https://www.courier.com/docs/platform/content/elemental/elemental-overview) — official reference
- [Elements Reference](https://www.courier.com/docs/platform/content/elemental/elements/index) — complete element type reference
