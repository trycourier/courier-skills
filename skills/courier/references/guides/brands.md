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

## Attaching a brand to a send

Three ways, most specific first:

1. **Per send:** `message.brand_id` overrides everything for that one message.
   ```ts
   await client.send.message({
     message: { to: { user_id: "user-123" }, template: "welcome", brand_id: brand.id },
   });
   ```
2. **Per tenant:** set `brand_id` on the tenant; any send that carries that tenant
   (`to.tenant_id` or `message.context.tenant_id`) renders with it automatically. This is the
   B2B pattern, one template, per-customer branding. See [patterns.md](./patterns.md).
3. **Per template:** associate a brand with a stored template in the dashboard; it applies
   whenever that template sends without a more specific override.

Verify field shapes against the installed SDK types (`resources/brands.d.ts`), brand settings
carry more nested keys (email head/header/footer, in-app icons) than shown here.
