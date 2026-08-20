# Brands

A brand is reusable visual styling (colors, logo, email header/footer, in-app widget theme)
that Courier applies when rendering a template. Define it once, attach it, and every send
picks it up without touching message content.

## The Brand object

`name` and `settings.colors` (`primary` + `secondary`) are the minimum; everything else is optional.

```jsonc
{
  "id": "brand_abc",              // generated, or supply your own on create
  "name": "Acme",
  "settings": {
    "colors": { "primary": "#9D3789", "secondary": "#FFFFFF" },
    "email": {                     // optional email chrome
      "header": { /* logo, barColor */ },
      "footer": { /* markdown, social links */ },
      "head":   { /* raw <head> inject */ }
    },
    "inapp": {                     // optional in-app inbox theme
      "colors": { "primary": "#9D3789", "secondary": "#FFFFFF" },
      "icons": { /* … */ },
      "widgetBackground": { /* … */ },
      "borderRadius": "8px",
      "placement": "bottom"        // top | bottom | left | right
    }
  },
  "snippets": { "items": [{ "name": "greeting", "value": "Hi there" }] }
}
```

## SDK methods

| Operation | Node | Python |
|---|---|---|
| Create | `client.brands.create({ name, settings })` | `client.brands.create(name=…, settings=…)` |
| Get | `client.brands.retrieve(brandId)` | `client.brands.retrieve(brand_id)` |
| Update | `client.brands.update(brandId, { name, settings })` | `client.brands.update(brand_id, …)` |
| List | `client.brands.list()` | `client.brands.list()` |
| Delete | `client.brands.delete(brandId)` | `client.brands.delete(brand_id)` |

`update` replaces `settings`. Send the full object, not a partial, or you drop the omitted keys.

```ts
const brand = await client.brands.create({
  name: "Acme",
  settings: { colors: { primary: "#9D3789", secondary: "#FFFFFF" } },
});
```

## Brand resolution by send type

Brand resolution follows the send type, giving you precise control over branding either way:

| Send type | Brand applied |
|---|---|
| Inline content (`message.content`) | `message.brand_id`, else the workspace default |
| Stored template (`message.template`) | The template's own `brand` field |

1. **Inline sends:** pass `message.brand_id` to pick a brand for that one message; omit it
   and the workspace default brand applies — inline email always arrives branded.
   ```ts
   await client.send.message({
     message: {
       to: { user_id: "user-123" },
       content: { title: "Welcome!", body: "Thanks for signing up." },
       brand_id: brand.id,
     },
   });
   ```
2. **Template sends:** the template's `brand` field is the single source of truth, so a
   template always renders consistently no matter who sends it. Set it on create
   (`brand: {id: "brand_abc"}`) or in the dashboard.
3. **Per tenant:** set `brand_id` on the tenant; any send that carries that tenant
   (`to.tenant_id` or `message.context.tenant_id`) renders with it automatically. This is the
   B2B pattern, one template, per-customer branding. See [patterns.md](./patterns.md).

## Sending unbranded email

Courier gives you full control of branding — down to none at all. Store the template with
`brand: null` and send by template id: the output renders completely chrome-free, ideal for
plain personal-feeling emails or fully custom designs where your content is the whole email.

Since inline sends always carry a brand (yours or the workspace default), the working
pattern is: **preview inline, ship by template id** — the template's `brand: null` is the
off switch.

Verify field shapes against the installed SDK types (`resources/brands.d.ts`), brand settings
carry more nested keys (email head/header/footer, in-app icons) than shown here.
