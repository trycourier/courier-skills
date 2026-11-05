# Elemental Content Format

Elemental is Courier's JSON-based templating language. It defines the `content` payload used in both inline sends and stored templates.

> Template lifecycle (create, publish, versions, the end-to-end example) is in [templates.md](./templates.md); the translation workflow is in [localization.md](./localization.md).

**Contents:** [Quick Reference](#quick-reference) · [Structure](#structure) · [Element Types](#element-types) · [Control Flow](#control-flow) · [Localization](#localization) · [Related](#related)

## Quick Reference

### Rules
- Every Elemental payload has exactly two required top-level fields: `version` and `elements`.
- `version` is always `"2022-01-01"` (the only supported version).
- The shorthand `{ title, body }` (ElementalContentSugar) only works for **inline sends**. Never for template creation via the API.
- **Wrap stored template content in `channel` elements**, one per channel. Create rejects flat top-level elements with a `400`. `replace` and `putContent` still store them, but Design Studio can't open the result, so wrap on every write. Inline sends need no `channel` wrapper.
- When `channel` elements appear at the top level, **every** top-level sibling must also be a `channel` element.
- Control flow (`if`, `loop`, `ref`, `channels`) works on any element type.

### Common Mistakes
- Nesting `channel` elements inside other `channel` elements (they must be top-level siblings).
- Using `loop` without a `group` wrapper when you need to repeat multiple elements per item.
- Placing `raw` provider payloads outside a `channel` element.

---

## Structure

### ElementalContentSugar (Inline Sends Only)

`{ "title": "Welcome!", "body": "Thanks for signing up." }` converts to a `meta` element (title) and a `text` element (body).

Both `title` and `body` are required, even for SMS, which sends only the body. For a body-only message on a channel that would show a title, use one `text` element in the full form instead.

### Base Element Properties

All element types share these optional properties:

| Property | Type | Description |
|----------|------|-------------|
| `channels` | `string[]` | Restrict this element to specific channels (e.g., `["email", "push"]`) |
| `ref` | `string` | Tag the element with a name for cross-element references |
| `if` | `string` \| structured condition array | JavaScript expression against the message (`data.*`); the element renders only when truthy. The SDK types only the string form |
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
| `style` | `"button"` \| `"secondary"` \| `"tertiary"` \| `"link"` | No | `button` (default) is filled, `secondary` outlined, `tertiary` the quietest, `link` inline text. Each channel draws them as closely as it can. |
| `align` | `"center"` \| `"left"` \| `"right"` \| `"full"` | No | Alignment (default: `"center"`) |
| `background_color` | `string` | No | The fill for `button`; the border and label for `secondary`; for `tertiary`, the label (underlined in email) and the fill in the Inbox |

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
| `channel` | `string` | Yes | Channel name: `"email"`, `"push"`, `"sms"`, `"inbox"`, `"direct_message"`, a provider like `"slack"`, or `"default"` (for every channel without its own block) |
| `elements` | `array` | No | Nested elements for this channel |
| `raw` | `object` | No | Raw provider-specific payload (required if `elements` is omitted) |

**`inbox` is a valid value and Design Studio writes it.** A template built in the designer for the in-app inbox stores `{ "type": "channel", "channel": "inbox", "elements": [...] }`, so wrap inbox content the same way. Channel-wrapped is the expected shape, not malformed.

**SDK typing gap.** The generated SDK types cover `text`, `meta`, `channel`, `image`, `action`, `divider`, `quote` and `html`. They have no `group`, `columns`, `list`, `jsonnet` or `comment` node, and `text` has no `elements` field (the styled form), so those fail with TS2322 or TS2353 even though they're documented (and Design Studio produces `group`). A `locales` entry is typed with `content` only, so `title`, `href` or `src` in one also fails with TS2353. Keep the shape and add `// @ts-expect-error accepted by the API, missing from the SDK type` on that line, or cast the node. Python accepts them at runtime. Don't drop an element to satisfy the compiler. A channel's own `elements` are typed in 9.12.0; TS2353 on those alone means an older SDK, so upgrade. See [inbox.md](../channels/inbox.md#elemental-content-for-inbox).

#### The channel element vs the three other places a channel is named

Four different fields can name a channel, and they are not alternatives to each other. The Elemental `channel` element selects **content**. Two of the others affect **delivery**. The fourth, `channel` on a journey `send` node, affects **nothing at delivery time** and is only a reporting label.

| Where | Selects | Documented in |
|---|---|---|
| Elemental `channel` element | Which content block **renders** for a channel | This section |
| `channel` on `POST /journeys/{id}/templates` | The journey-scoped template's delivery channel | [journeys.md](./journeys.md) |
| `channel` on a journey `send` node | Nothing at delivery time. An **analytics label only** | [journeys.md](./journeys.md#send-node-options) |
| `routing` / a routing strategy on the message | Which channels are **eligible**, and in what order | [routing-strategies.md](./routing-strategies.md) |

They don't override one another because they answer different questions. Routing picks the delivery channel, then rendering picks the matching content branch. A `channel` element for a channel that routing never selects never renders. To cover delivery channels with no block of their own, add a `"channel": "default"` block.

**Elemental blocks or raw HTML.** For email, a channel element carries either `elements` (Elemental blocks) or `raw` (your own HTML or MJML). Both render and both show in Design Studio, but only Elemental blocks are editable there with the drag-and-drop editor. Raw HTML has to be edited as HTML. Default to Elemental blocks unless the design needs markup the block set cannot express, and treat `raw` as a deliberate choice to give up in-app editing.

**Declare the Handlebars transformer on `raw.html`.** `{{variables}}` in `raw.html` resolve only when the channel's `raw` carries `"transformers": ["handlebars"]` (`["handlebars", "mjml"]` for MJML). A `meta` element still sets the subject:

```json
{ "type": "channel", "channel": "email", "raw": { "html": "<p>Hi {{profile.first_name}}</p>", "transformers": ["handlebars"] } }
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
| `text_style` | `"text"` \| `"h1"` \| `"h2"` \| `"subtext"` | No | Text styling. Defaults to `"text"` |

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

`column` also takes card styling and `columns` takes a `gap`, so cards, card grids and full-width panels build from native blocks:

| Property | On | Type | Description |
|----------|----|------|-------------|
| `gap` | `columns` | `string` | Gutter between columns (e.g., `"12px"`) |
| `background_color` | `column` | `string` | Card fill color |
| `padding` | `column` | `string` | Space inside the card (e.g., `"18px"`) |
| `border_radius` | `column` | `string` | Rounded corners (e.g., `"14px"`) |
| `border_color` | `column` | `string` | Border color |
| `border_width` | `column` | `string` | Border width |
| `vertical_align` | `column` | `"top"` \| `"middle"` \| `"bottom"` | Vertical alignment of the column's content |

```json
{ "type": "columns", "gap": "12px", "elements": [
  { "type": "column", "width": "50%", "background_color": "#EEF9F7", "padding": "18px", "border_radius": "14px",
    "elements": [{ "type": "text", "content": "**42%** faster onboarding", "format": "markdown", "align": "center" }] },
  { "type": "column", "width": "50%", "background_color": "#EEF9F7", "padding": "18px", "border_radius": "14px",
    "elements": [{ "type": "text", "content": "**3×** more engagement", "format": "markdown", "align": "center" }] }
] }
```

`gap` doesn't require narrower columns: equal widths plus a gap render correctly. A single 100%-width styled column makes a full-width panel aligned with the email's content column. Borders go on `column` (`border_color`/`border_width`).

### list / list-item

Ordered and unordered lists with nesting support (up to 5 levels deep).

```json
{
  "type": "list",
  "list_type": "unordered",
  "elements": [
    { "type": "list-item", "elements": [{ "type": "string", "content": "Email notifications configured" }] },
    { "type": "list-item", "elements": [{ "type": "string", "content": "SMS provider connected" }] },
    { "type": "list-item", "elements": [{ "type": "string", "content": "Push tokens registered" }] }
  ]
}
```

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `list_type` | `"ordered"` \| `"unordered"` | Yes | Numbered or bulleted |
| `elements` (on `list`) | `array` | Yes | `list-item` elements only |
| `elements` (on `list-item`) | `array` | Yes | The item's content: `string`, `link`, `img`, or a nested `list` |

### html

Raw HTML for formatting the other elements can't express. Renders in email only. Variables work (`{{order_id}}`), and so do Handlebars helpers such as `{{#each}}`. There is no `json` helper: `{{json x}}` fails the render with `Missing helper`. Put loops here or use `loop` on an element (see [Iteration](#iteration-loop)), never `{{#each}}` in a text element, which renders but can't be edited in the designer. The exception is an object, such as a journey batch's `batch.categories`, since `loop` only takes arrays. `$.item` is loop syntax for `loop`, not Handlebars.

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

`{ "type": "jsonnet", "template": "<Jsonnet source>" }`: evaluated to JSON at render time.

### comment

`{ "type": "comment", "comment": "Author note" }`: never renders. An optional `object` field holds structured notes.

---

## Control Flow

Control flow properties work on any element type, including `group` containers.

### Conditional Rendering (`if`)

The `if` expression is JavaScript, evaluated at render time against the message, with send data under `data.*`. `===`, `==` and `!==` all work.

```json
{
  "type": "text",
  "content": "As a premium member, you get early access.",
  "align": "left",
  "if": "data.tier === 'premium'"
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

Show an element only on some channels without a `channel` container: add `"channels": ["email"]` to the element.

---

## Localization

Elements carry translations in a `locales` map keyed by locale code (`"locales": { "es": { "content": "¡Bienvenido!" } }`). Which fields each element type can translate, how Courier picks the locale, and how to write translations (`putLocale`): [localization.md](./localization.md).

## Related

- [Templates](./templates.md), template lifecycle (create, publish, version, archive) and inline-vs-templated decisions
- [Multi-Channel](./multi-channel.md), routing strategies for the top-level `channel` elements
- [Elemental Overview](https://www.courier.com/docs/design/elemental/overview), official reference
- [Elements Reference](https://www.courier.com/docs/design/elemental/elements/text), one page per element type, starting with `text`
