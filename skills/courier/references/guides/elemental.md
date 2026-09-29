# Elemental Content Format

Elemental is Courier's JSON-based templating language. It defines the `content` payload used in both inline sends and stored templates.

> **Where to read what:** This file is the element-by-element reference. For the **template lifecycle** (create, publish, version, archive via `/notifications`) and inline-vs-templated decision, see [Templates](./templates.md). For a full end-to-end example combining both, see the "Full Lifecycle Example" section in [Templates](./templates.md).

## Quick Reference

### Rules
- Every Elemental payload has exactly two required top-level fields: `version` and `elements`.
- `version` is always `"2022-01-01"` (the only supported version).
- The shorthand `{ title, body }` (ElementalContentSugar) only works for **inline sends**. Never for template creation via the API.
- **Wrap stored template content in `channel` elements**, one per channel. Flat top-level elements send, but the template does not display or edit properly in Design Studio.
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

- `version`. Always `"2022-01-01"` (the only supported version)
- `elements`, array of element objects

### ElementalContentSugar (Inline Sends Only)

For simple inline sends, use the shorthand:

```json
{
  "title": "Welcome!",
  "body": "Thanks for signing up, {{name}}."
}
```

Courier auto-converts this to a `meta` element (title) and a `text` element (body). This format does **not** work when creating templates via `POST /notifications`. Use the full `version` + `elements` structure.

### Base Element Properties

All element types share these optional properties:

| Property | Type | Description |
|----------|------|-------------|
| `channels` | `string[]` | Restrict this element to specific channels (e.g., `["email", "push"]`) |
| `ref` | `string` | Tag the element with a name for cross-element references |
| `if` | `string` | Conditional expression, element renders only when truthy |
| `loop` | `string` | Path to an array, element renders once per item |

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
| `content` | `string` | Yes* | Text content (supports `{{variables}}`). *Either `content` or `elements` |
| `align` | `"left"` \| `"center"` \| `"right"` | No | Text alignment. Defaults to `"left"`; include it explicitly to avoid ambiguity across renderers |
| `text_style` | `"text"` \| `"h1"` \| `"h2"` \| `"subtext"` | No | Heading level or subtext |
| `format` | `"markdown"` | No | Enable markdown rendering (`**bold**`, `*italic*`, links) |

**Styled text:** for color, bold, and other rich styling, `text` takes nested children via `elements` (instead of `content`), with the styling carried on the `string`/`link` children. This form works everywhere — inline sends and stored templates.

```json
{ "type": "text", "align": "left", "elements": [
    { "type": "string", "content": "Available now", "color": "#006B56", "bold": true }
] }
```

Styling properties on `string`/`link` children:

| Property | Type | Description |
|----------|------|-------------|
| `color` | `string` | CSS text color |
| `highlight` | `string` | CSS highlight (background) color |
| `bold` | `boolean` | Apply bold |
| `italic` | `boolean` | Apply italic |
| `strikethrough` | `boolean` | Apply strikethrough |
| `underline` | `boolean` | Apply underline |

Inline sends via `POST /send` also tolerate these styling properties flat on the `text` element itself, but the Templates API accepts only the nested form — use the nested form everywhere.

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
| `style` | `"button"` \| `"secondary"` \| `"tertiary"` \| `"link"` | No | `button` (default) is filled, `secondary` outlined, `tertiary` the quietest, `link` inline text. Each channel draws them as closely as it can. The SDK type lists only `button` and `link`, so the other two need `// @ts-expect-error` in TypeScript |
| `align` | `"center"` \| `"left"` \| `"right"` \| `"full"` | No | Alignment (default: `"center"`) |
| `background_color` | `string` | No | The fill for `button`; the border and label for `secondary`; the label for `tertiary` |

### image

Embedded image with optional link.

```json
{
  "type": "image",
  "src": "https://example.com/product.jpg",
  "alt_text": "Product photo",
  "width": "300px",
  "href": "https://example.com/products/123",
  "align": "center"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `src` | `string` | Yes | Image URL |
| `href` | `string` | No | Link URL when image is clicked |
| `alt_text` | `string` | No | Alt text for accessibility |
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
| `channel` | `string` | Yes | Channel name: `"email"`, `"push"`, `"sms"`, `"inbox"`, `"direct_message"`, or a provider like `"slack"` |
| `elements` | `array` | No | Nested elements for this channel |

**`inbox` is a valid value and Design Studio writes it.** A template built in the designer for the in-app inbox stores `{ "type": "channel", "channel": "inbox", "elements": [...] }`, so wrap inbox content the same way. Channel-wrapped is the expected shape, not malformed.

**SDK typing gap.** The generated SDK types have no `group` node, so `type: "group"` fails in TypeScript with TS2322 even though the API accepts it and Design Studio produces it. Keep the shape and add `// @ts-expect-error accepted by the API, missing from the SDK type` on that line, or cast the node. Python accepts it at runtime. Do not drop `group` to satisfy the compiler. Channel `elements` are typed; if an older SDK rejects them with TS2353, upgrade. See [inbox.md](../channels/inbox.md#elemental-content-for-inbox).

#### The channel element vs the three other places a channel is named

Four different fields can name a channel, and they are not alternatives to each other. The Elemental `channel` element selects **content**. Two of the others affect **delivery**. The fourth, `channel` on a journey `send` node, affects **nothing at delivery time** and is only a reporting label.

| Where | Selects | Documented in |
|---|---|---|
| Elemental `channel` element | Which content block **renders** for a channel | This section |
| `channel` on `POST /journeys/{id}/templates` | The journey-scoped template's delivery channel | [journeys.md](./journeys.md) |
| `channel` on a journey `send` node | Nothing at delivery time. An **analytics label only** | [journeys.md](./journeys.md#send-node-options) |
| `routing` / a routing strategy on the message | Which channels are **eligible**, and in what order | [routing-strategies.md](./routing-strategies.md) |

They don't override one another because they answer different questions. Routing picks the delivery channel, then rendering picks the matching content branch. A `channel` element for a channel that routing never selects simply never renders, and a delivery channel with no matching `channel` element falls back to the template's unwrapped content.
| `raw` | `object` | No | Raw provider-specific payload (required if `elements` is omitted) |

**Elemental blocks or raw HTML.** For email, a channel element carries either `elements` (Elemental blocks) or `raw` (your own HTML or MJML). Both render and both show in Design Studio, but only Elemental blocks are editable there with the drag-and-drop editor. Raw HTML has to be edited as HTML. Default to Elemental blocks unless the design needs markup the block set cannot express, and treat `raw` as a deliberate choice to give up in-app editing.

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
        { "type": "image", "src": "{{product_image}}", "alt_text": "{{product_name}}" },
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
  "border_color": "#1a73e8",
  "text_style": "text"
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `content` | `string` | Yes | Quote text |
| `align` | `"center"` \| `"left"` \| `"right"` \| `"full"` | No | Alignment |
| `border_color` | `string` | No | CSS border color |
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
        { "type": "image", "src": "{{product_image}}", "alt_text": "Product" }
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

Columns are also Elemental's design surface: `column` accepts background, padding, and border styling, and `columns` accepts `gap` — so colored cards, card grids with gutters, and full-width section panels are all buildable in native blocks.

| Property | On | Type | Description |
|----------|----|------|-------------|
| `gap` | `columns` | `string` | Gutter between columns (e.g., `"12px"`) |
| `background_color` | `column` | `string` | Card fill color |
| `padding` | `column` | `string` | Space inside the card (e.g., `"18px"`) |
| `border_radius` | `column` | `string` | Rounded corners (e.g., `"14px"`) |
| `border_color` | `column` | `string` | Border color |
| `border_width` | `column` | `string` | Border width |
| `vertical_align` | `column` | `"top"` \| `"middle"` \| `"bottom"` | Vertical alignment of the column's content |

A card grid — one styled `column` per card, repeated for each card in the row (a three-up
grid is three of these at `"33.33%"`):

```json
{
  "type": "columns",
  "gap": "12px",
  "elements": [
    {
      "type": "column",
      "width": "50%",
      "background_color": "#EEF9F7",
      "padding": "18px",
      "border_radius": "14px",
      "elements": [
        { "type": "text", "content": "**42%**", "format": "markdown", "align": "center" },
        { "type": "text", "content": "faster onboarding", "align": "center" }
      ]
    },
    {
      "type": "column",
      "width": "50%",
      "background_color": "#EEF9F7",
      "padding": "18px",
      "border_radius": "14px",
      "elements": [
        { "type": "text", "content": "**3×**", "format": "markdown", "align": "center" },
        { "type": "text", "content": "more engagement", "align": "center" }
      ]
    }
  ]
}
```

`gap` adds the gutter without requiring you to reduce column widths — equal-width columns
with a gap render correctly.

A single 100%-width styled column makes a full-width section panel — it aligns with the email's content column for a consistent layout. Set borders on `column` via `border_color`/`border_width` (that's where they render).

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

Raw HTML for formatting the other elements can't express. Renders in email only. Variables work (`{{order_id}}`), and so do Handlebars helpers such as `{{#each}}`. Put loops here or use `loop` on an element (see [Iteration](#iteration-loop)), never `{{#each}}` in a text element, which renders but can't be edited in the designer. `$.item` is loop syntax for `loop`, not Handlebars.

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

The `if` expression is evaluated as **Jsonnet** against the send `data` object (not JavaScript). Use Jsonnet equality (`==`, `!=`), logical operators (`&&`, `||`, `!`), and string literals in single quotes. The other common pitfall is triple-equals (`===`). That's JavaScript-only and will fail to parse.

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
  "alt_text": "Welcome banner",
  "channels": ["email"]
}
```

---

## Localization

Elements carry translations in a `locales` map keyed by locale code. Each locale stores only the fields it translates:

```json
{
  "type": "text",
  "content": "Welcome, {{name}}!",
  "locales": {
    "es": { "content": "¡Bienvenido, {{name}}!" },
    "fr": { "content": "Bienvenue, {{name}} !" }
  }
}
```

The translatable field depends on the type: `content` on `text`, `action`, `quote`, and `html`; `title` on `meta` (the subject); `href` on `action` and `image`; `src` on `image`; `raw` on `channel`; and `elements` on `text`, `list-item`, and containers. `divider`, `jsonnet`, `partial`, and `comment` take none.

Courier picks the locale from `message.to.locale`, else the profile's `locale`, and matches it exactly (`es-MX` doesn't fall back to `es`). To translate a stored template, use `putLocale` rather than hand-editing `locales` into a full content write. Workflow, rules, and Design Studio AI Translation: [localization.md](./localization.md).

## Related

- [Templates](./templates.md), template lifecycle (create, publish, version, archive) and inline-vs-templated decisions
- [Multi-Channel](./multi-channel.md), routing strategies for the top-level `channel` elements
- [Quickstart](./quickstart.md). Send your first notification
- [Elemental Overview](https://www.courier.com/docs/design/elemental/overview), official reference
- [Elements Reference](https://www.courier.com/docs/design/elemental/elements/text), one page per element type, starting with `text`

<!-- Target line budget: <= 550 lines. If you are about to push this past 575, split (e.g., control flow + localization out) rather than letting it grow. -->
