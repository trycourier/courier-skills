# Localization

A template holds its content once, in the default language, and each element carries a translation per locale in a `locales` map. At send time Courier picks the recipient's locale and swaps in the matching text, element by element.

## Quick Reference

### Rules

- **Courier takes the locale from `message.to.locale`**, or from the `locale` on the recipient's profile when the send doesn't set one. With neither, the default content sends.
- **Locale codes match exactly, including case.** A template translated as `es` serves `es` only. A recipient set to `es-MX` or `ES` gets the default content, with no fallback to the base language. Design Studio names locales in lowercase (`es`, `es-mx`), so store the same form on profiles.
- **An element with no translation for the locale sends in the default language.** Partial translations are safe.
- **Write translations with `putLocale`**, one locale per call. It merges: it touches only the locale in the path, only the elements you list, and only the fields you send.
- **Keep element `id`s.** Translations are addressed by element `id`. A content write that leaves ids out gives every element a new one.
- **A full content write replaces `locales` too.** `putContent` (or `replace`) with content that has no `locales` deletes every translation, including ones made in Design Studio.
- **`putElement` replaces the whole element.** Leave out `locales` and they're gone. Don't use it for text or translation changes.
- **Writes land on the draft; sends use the published version.** Publish after writing, or pass `state: "PUBLISHED"` on the locale write (it publishes the whole draft, including other people's edits).
- Keep `{{variables}}` exactly as written in every translation.

### Common Mistakes

- Stripping `locales` or element ids before `putContent`. Remove only `checksum` fields and Design Studio's `_`-prefixed keys (see [Replace all content](#replace-all-content))
- Sending a Design Studio read back unchanged. Its `locales` carry keys like `_sourceHash`, and the write returns `400 Unrecognized key: "_sourceHash"`
- Storing `es-MX` on profiles when the template is translated as `es`
- Writing translations and never publishing
- Translating a subject with `content`. The subject is `title` on the `meta` element; `content` returns a `400` naming the field
- Uploading a `.po` file with the SDK's `translations.update`. It JSON-encodes the string. Upload with a raw HTTP `PUT` (see [Workspace translation strings](#workspace-translation-strings))
- Using `{{t}}` for recipients who have no locale. The send fails

## How it works

```json
{
  "id": "elem_01kx4h2jdafq8bk9b0d2c6yv9p",
  "type": "text",
  "content": "Order {{order_number}} is confirmed.",
  "locales": {
    "es": { "content": "El pedido {{order_number}} está confirmado." },
    "fr": { "content": "La commande {{order_number}} est confirmée." }
  }
}
```

Each locale stores only the fields it translates, so a layout change carries into every language. The same `locales` map works on inline content passed to `message.content`.

Two ways to produce translations, and they write the same `locales` data, so one template can use both:

- **The API**: export the strings, translate them anywhere (your translators, a translation tool, or the agent itself), write each locale back. Below.
- **Design Studio AI Translation**: see [below](#design-studio-ai-translation).

## Translate a template with the API

| Step | Call |
|---|---|
| 1. Export the strings | `client.notifications.retrieveContent(id, { version: "draft" })` |
| 2. Translate | Outside Courier, keyed by element `id` |
| 3. Write each locale | `client.notifications.putLocale(localeId, { id, elements })` |
| 4. Publish | `client.notifications.publish(id)` |
| 5. Send | `client.send.message` with `to.locale` |

### 1. Export the strings

Read the draft. Without `version`, you get the published version, and a template that has never been published returns `404`.

**Node:**
```typescript
const content = await client.notifications.retrieveContent("nt_01abc123", { version: "draft" });
```

**Python:**
```python
content = client.notifications.retrieve_content("nt_01abc123", version="draft")
```

Every element comes back with an `id` and a `checksum`, plus any `locales` already stored:

```json
{
  "version": "2022-01-01",
  "elements": [
    {
      "id": "elem_01kx4h2jdafq8bk9b07z4mq2wd", "type": "channel", "channel": "email", "checksum": "0557…",
      "elements": [
        { "id": "elem_01kx4h2jdafq8bk9b0a8x3rt5n", "type": "meta", "title": "Order confirmed", "checksum": "ec7f…" },
        { "id": "elem_01kx4h2jdafq8bk9b0d2c6yv9p", "type": "text", "content": "Order {{order_number}} is confirmed.", "checksum": "5114…" },
        { "id": "elem_01kx4h2jdafq8bk9b0g5k7hs1e", "type": "action", "content": "View order", "href": "https://acme.com/orders", "checksum": "88d1…" }
      ]
    }
  ]
}
```

Templates from the legacy designer return `blocks` and `channels` instead of `elements`. This workflow is for Elemental templates.

### 2. Translate

Walk every `elements` array and skip the `locales` maps. Take `title` from `meta`, and `content` from `text`, `action`, `quote`, and `html`. Each channel holds its own copy, so a template that sends email and inbox has two of each string. Keep each string's element `id`, field, and `checksum`:

```json
[
  { "id": "elem_01kx4h2jdafq8bk9b0a8x3rt5n", "field": "title", "text": "Order confirmed", "note": "Email subject" },
  { "id": "elem_01kx4h2jdafq8bk9b0d2c6yv9p", "field": "content", "text": "Order {{order_number}} is confirmed.", "note": "Email body" },
  { "id": "elem_01kx4h2jdafq8bk9b0g5k7hs1e", "field": "content", "text": "View order", "note": "Button label" }
]
```

When the agent translates the strings itself, keep `{{variables}}`, Handlebars helpers, and URLs unchanged, and match the tone of the source. A text element built from inline nodes needs its translation written as nodes too, see [Formatted text](#formatted-text).

### 3. Write each locale

One call per locale. Each entry names an element by `id` and carries its translated fields. Add localized links yourself.

**Node:**
```typescript
await client.notifications.putLocale("es", {
  id: "nt_01abc123",
  elements: [
    { id: "elem_01kx4h2jdafq8bk9b0a8x3rt5n", title: "Pedido confirmado" },
    { id: "elem_01kx4h2jdafq8bk9b0d2c6yv9p", content: "El pedido {{order_number}} está confirmado." },
    { id: "elem_01kx4h2jdafq8bk9b0g5k7hs1e", content: "Ver pedido", href: "https://acme.com/es/orders" },
  ],
});
```

**Python:**
```python
client.notifications.put_locale(
    "es",
    id="nt_01abc123",
    elements=[
        {"id": "elem_01kx4h2jdafq8bk9b0a8x3rt5n", "title": "Pedido confirmado"},
        {"id": "elem_01kx4h2jdafq8bk9b0d2c6yv9p", "content": "El pedido {{order_number}} está confirmado."},
        {"id": "elem_01kx4h2jdafq8bk9b0g5k7hs1e", "content": "Ver pedido", "href": "https://acme.com/es/orders"},
    ],
)
```

**CLI:** `courier notifications put-locale --id nt_01abc123 --locale-id es --element '{id: elem_01kx4h2jdafq8bk9b0a8x3rt5n, title: Pedido confirmado}'`. **MCP:** `put_notification_locale`.

- **It merges.** Other locales, other elements, and fields you leave out keep their values, so you can send only the strings that changed. Leave untranslated strings out and they send in the default language.
- **Every `id` must exist.** An unknown id returns a `400` and nothing is written, not even the valid entries.
- **Fields depend on the element type**, see [Which fields a locale can override](#which-fields-a-locale-can-override). A field the type doesn't take returns a `400` naming it.

### 4. Publish and send

**Node:**
```typescript
await client.notifications.publish("nt_01abc123");

await client.send.message({
  message: {
    to: { user_id: "user_123", locale: "es" },
    template: "nt_01abc123",
    data: { order_number: "1042" },
  },
});
```

**Python:**
```python
client.notifications.publish("nt_01abc123")

client.send.message(
    message={
        "to": {"user_id": "user_123", "locale": "es"},
        "template": "nt_01abc123",
        "data": {"order_number": "1042"},
    }
)
```

Or store `locale` on the profile so every send picks it up. Check the result with `client.messages.content(messageId)` (see [Verify the Rendered Output](./templates.md#verify-the-rendered-output)), and see how each language lays out on real email clients with a [localized Device Preview](./device-preview.md#localized-previews). Longer languages (German, French) are where buttons wrap and Outlook tables break.

### 5. Re-translate only what changed

An element's `checksum` changes when its own content changes, and a container's changes when anything inside it does. Writing translations doesn't change it; each translation carries its own `checksum` inside `locales`. Store each string's `id` and `checksum` at export. On the next export (always `version=draft`):

| Next export shows | Do |
|---|---|
| Same `id`, changed `checksum` | Re-translate it |
| New `id` | New string, translate it |
| `id` gone | Nothing |

## Which fields a locale can override

| Field | Element types | For |
|---|---|---|
| `content` | `text`, `action`, `quote`, `html` | Body copy, button labels |
| `title` | `meta` | Email subject, push and chat title |
| `href` | `action`, `image` | Language-specific links |
| `src` | `image` | Images with text in them |
| `raw` | `channel` | Provider-native overrides, such as a translated `subject` or a whole `html` body |
| `elements` | `text`, `list-item` (inline nodes); `channel`, `group`, `column`, `columns`, `list` (child nodes) | Nested content |

`divider`, `jsonnet`, `partial`, and `comment` take no locale entry. Sending `elements` or `raw` in a locale replaces that field's whole value, so send all of it each time.

### Formatted text

A text element can hold its copy as a `content` string or as an `elements` array of inline nodes. If the default uses `elements` (bold, italic, links), give each translation as `elements` too. A translation given as `content` renders as one plain node and loses the formatting.

## Other write paths

### Replace all content

`putContent` writes the whole element tree, translations included. To round-trip a draft (for example from a repo), read it with `version=draft`, then:

- remove every `checksum`, on elements and inside `locales`
- remove `_`-prefixed keys inside `locales` (Design Studio adds them)
- keep every element's `id` and `locales`

```bash
jq 'del(.. | .checksum?)
    | walk(if type == "object" and has("locales")
           then .locales |= map_values(with_entries(select(.key | startswith("_") | not)))
           else . end)'
```

[templates-as-code.md](./templates-as-code.md) uses this filter for repo sync.

### Remove a locale

`putLocale` only adds and updates. To drop a language, read the draft, delete that code from each element's `locales`, and write the content back with `putContent`.

### Journey templates

A template that belongs to a journey takes the same bodies under the journey: `client.journeys.templates.retrieveContent`, `client.journeys.templates.putLocale`, and `client.journeys.templates.publish`. See [journeys.md](./journeys.md).

## Design Studio AI Translation

In Design Studio, open the template, click the globe icon, and add a language. With **Translate with AI** checked (the default), Courier translates every string: subject, headings, body, buttons. Review it side by side with the default and edit any string. When the default changes, Courier flags translations that may be out of date, and you re-translate them one at a time or all together. Publish to send them.

AI Translation uses AI credits, available on the Business and Enterprise plans. Each translation request costs credits, and a long template can take more than one request per locale. Reach for the API path when templates live in code, when translations come from a translation tool, or when the agent is doing the translating.

## Workspace translation strings

Separate from template locales: workspace `.po` files, one per locale, rendered with the `{{t}}` Handlebars helper (`{{t "welcome_headline"}}`). Use them for a shared glossary of short strings reused across templates. Put a notification's own copy in template locales.

```bash
curl -X PUT "https://api.courier.com/translations/default/es" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: text/plain" \
  --data-binary @es.po
```

- **Send the `.po` file as the raw body with `Content-Type: text/plain`.** The SDK's `translations.update` JSON-encodes the string, which stores a broken file.
- **The domain is always `default`.** Anything else returns a `400`.
- Read a locale's file back with `client.translations.retrieve("es", { domain: "default" })` (Python: `client.translations.retrieve("es", domain="default")`) to compare it with your translation system.
- **`{{t}}` needs a recipient locale with an uploaded file.** With no locale, or a locale that has no file, the send fails with `translate helper: Could not find translations`. A key missing from an uploaded file renders as the key itself.
- Translations are per workspace. A tenant that needs different wording needs a different template.

## Related

- [Templates](./templates.md): create, publish, versions, rendered output
- [Templates as Code](./templates-as-code.md): repo sync that keeps translations
- [Device Preview](./device-preview.md): check each language on real email clients
- [Elemental](./elemental.md): element types and the `locales` property
- [Template translations](https://www.courier.com/docs/design/elemental/locales): official docs
