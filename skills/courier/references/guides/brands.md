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
| Stored template (`message.template`) | The template's own `brand` field — on `POST /send`, a `message.brand_id` does not override it. (Bulk API jobs document their own job-level `brand` — see [bulk.md](./bulk.md)) |
| Any send carrying `tenant_id` | The tenant's `brand_id` is applied to the rendered template — the B2B pattern |

1. **Inline sends** always arrive branded:
   ```ts
   await client.send.message({
     message: {
       to: { user_id: "user-123" },
       content: { title: "Welcome!", body: "Thanks for signing up." },
       brand_id: brand.id,
     },
   });
   ```
2. **Template sends:** set the template's `brand` on create (`brand: {id: "brand_abc"}`) or
   in the dashboard.
3. **Tenant sends:** set `brand_id` on the tenant; the send carries the tenant via
   `to.tenant_id` or `message.context.tenant_id` — one template, per-customer branding. See
   [patterns.md](./patterns.md).

## Sending unbranded email

Courier gives you full control of branding — down to none at all. Store the template with
`brand: null` and send by template id: the output renders completely chrome-free, ideal for
plain personal-feeling emails or fully custom designs where your content is the whole email.

Since inline sends always carry a brand (yours or the workspace default), the working
pattern is: **iterate inline, ship by template id** — the template's `brand: null` is the
off switch. Inline previews will show brand chrome, so confirm the final chrome-free render
from a test send of the template itself (`GET /messages/{id}/output`).

In multi-tenant workspaces, a send that carries `tenant_id` may still apply that tenant's
brand to the rendered template — for chrome-free output on tenant-scoped sends, confirm with
a rendered test send (`GET /messages/{id}/output`).

Verify field shapes against the installed SDK types (`resources/brands.d.ts`), brand settings
carry more nested keys (email head/header/footer, in-app icons) than shown here.
