# Templates & Elemental

**Contents:** [Quick Reference](#quick-reference) · [Inline vs Templated Sending](#inline-vs-templated-sending) · [Template Aliases](#template-aliases) · [Variables](#variables) · [Send conditions](#send-conditions) · [Legacy templates](#legacy-templates) · [Template CRUD, the Notifications API](#template-crud-the-notifications-api) · [Elemental Content Format](#elemental-content-format) · [Full Lifecycle Example](#full-lifecycle-example) · [Workspace vs Tenant Templates](#workspace-vs-tenant-templates) · [Related](#related)

## Quick Reference

### Rules
- Template IDs use the `nt_` prefix (e.g., `nt_01kmrbq6ypf25tsge12qek41r0`). Older templates may have other formats, and the prefix doesn't tell you which editor built a template (see [Legacy templates](#legacy-templates))
- Create templates with `content.scope: "strict"` and prefix every variable: `{{data.order_id}}`, `{{profile.email}}`. Without it `{{data.order_id}}` renders empty (see [Variables](#variables))
- Send by the `nt_...` ID or by a template alias passed as `template`. Set an alias with `notification.alias` on create or replace, or in Design Studio. See [Templates as Code](./templates-as-code.md#template-aliases)
- Treat template IDs as opaque, workspace-specific values (they vary by environment and should not encode business meaning)
- Templates are created in **DRAFT** by default, and sends use only the published version. Publish with `publish(id)`, or pass `state: "PUBLISHED"` on create to do both in one call
- **`POST /notifications` needs more than `name` and `content`.** `tags` (an array), `brand`, `subscription` and `routing` must all be **present** in the body; the last three accept `null`. Omit any one and the call fails with a `400` naming the missing key.
- `PUT /notifications/{id}` is a **full replacement**, every field is required, even if unchanged; omitted fields reset to empty/null, except `alias`: omit it and the template keeps its aliases
- Elemental version string is always `"2022-01-01"`
- ElementalContentSugar (`title`/`body`) only works for inline sends. Use the full Elemental format (`version` + `elements`) when creating templates via the API
- **Wrap template content in `channel` elements** (`{ type: "channel", channel: "email", elements: [...] }`), one per channel. Create rejects flat top-level elements (`400 Template content must place its elements inside a channel block`); `replace` and `putContent` still store them, but Design Studio can't open the result, so wrap on every write. Inline sends accept flat elements. SDK type gaps (`group`, `columns`, styled `text`) and Elemental blocks vs raw HTML: [elemental.md](./elemental.md#channel).
- A template needs a `routing.strategy_id` from your workspace to route through channels: create one with `client.routingStrategies.create(...)` ([routing-strategies.md](./routing-strategies.md)), reuse one from `client.routingStrategies.list()`, or pass `routing: null` on create and attach one later with `notifications.replace`.
- **Check what `routing` actually came back as.** The create body accepts `routing` in exactly one shape, `{ "strategy_id": "rs_..." }`. Anything else is rejected, and a strategy id that doesn't exist is a `400` (`Routing strategy rs_... not found`). Templates nonetheless turn up with `routing: null` in practice, including ones built in Design Studio, and a template with `routing: null` goes `UNROUTABLE` when sent by id unless the send carries `routing`. Read it back with `GET /notifications/{id}` rather than trusting the create response, and attach one with `PUT /notifications/{id}` (`notifications.replace`) if it's null. On the inbox this surfaces as `UNROUTABLE` / `PROVIDER_ERROR` "No provider(s) courier ... : undefined", see [inbox.md](../channels/inbox.md#troubleshooting).
- Archive a template with `DELETE /notifications/{id}` (or `client.notifications.archive(id)` in the SDK). Note: `POST /notifications/{id}/archive` does **not** exist and returns 404, the archive operation uses the `DELETE` method.
- Confirm final visuals from a rendered test send — `GET /messages/{id}/output` returns the exact email recipients receive (see [Verify the Rendered Output](#verify-the-rendered-output))
- To see the email on real clients (Outlook, Gmail, Apple Mail, dark mode) before sending, run a [Device Preview](./device-preview.md) on the draft
- Keep `scope`, element `id`s and `locales` when you write content back: a `putContent` without them resets scope and deletes translations ([localization.md](./localization.md))
- Managing templates from a repo (CI, drift detection, promotion): see [Templates as Code](./templates-as-code.md)

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

**Keep JSON out of inline content.** Courier reads `{…}` in inline `content` as a variable, so a JSON string can render as `[Error]` (a nested object did in testing). Send the payload as an object in `data` instead:

```typescript
const event = {
  userId: "user-123",
  notification: { id: "n_456", domain: "posts", kind: "comment" },
  eventTimestamp: 1793601748,
};

// Before: the body renders as {"userId":"user-123","notification":[Error],"eventTimestamp":1793601748}
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: { title: "New notification", body: JSON.stringify(event) },
  },
});

// After: readable text in content, the payload in data
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: { title: "New comment", body: "Jane replied to your post." },
    data: event,
  },
});
```

The Inbox feed returns `data` as a parsed object with its nesting intact, so your client reads `message.data.notification.id` directly.

Inline sends support both ElementalContentSugar (`title`/`body`) and the full Elemental format (`version` + `elements`). Stored templates always use the full Elemental format.

---

## Template Aliases

A template alias is a name you choose that stands in for the `nt_...` ID on a send. Set it with `notification.alias` on create or replace, or in Design Studio, then pass it as `template`. Rules, the `409` on a taken alias, and examples are in [Templates as Code](./templates-as-code.md#template-aliases).

---

## Variables

Every variable names its root. Write `{{data.order_id}}`, never `{{order_id}}`:

```handlebars
Hi {{profile.first_name}}, your order {{data.order_id}} shipped to {{profile.email}}.
```

| Root | Comes from | Example |
|---|---|---|
| `data` | The `data` object on the send | `{{data.order.total}}` |
| `profile` | The recipient's profile (sent inline or stored) | `{{profile.email}}` |
| `tenant` | The tenant on the send's `context` | `{{tenant.name}}` |
| `brand` | The brand applied to the send | `{{brand.colors.primary}}` |
| `$.item` | The current item inside a List block loop | `{{$.item.sku}}` |

- **Design Studio templates are `scope: "strict"`.** A bare `{{order_id}}` resolves to nothing, and a bare helper name (`{{path}}`) calls the helper. Default scope (API-created without `scope`, older designer, inline sends) spreads `data` onto the root: bare names work, `{{data.order_id}}` renders empty.
- **Read the tenant through `{{tenant.id}}`.** `{{context.tenant_id}}` resolves to an empty string.
- **Profile values aren't copied into `data`.** If the email is on the profile, write `{{profile.email}}`; `{{data.email}}` only works when you send it in `data`.
- **A missing variable doesn't fail the send.** A missing double-brace variable (`{{data.coupon}}`) renders as an empty string; supply a fallback with `{{default data.value "fallback"}}`. A missing single-brace variable (`{order.total}`, the older designer's syntax) stays in the output as literal text.
- **The designer's preview substitutes variables but doesn't run helpers.** `{{datetime-format}}` or `{{truncate}}` can look wrong in preview and render correctly on send, so check helper output in a test send's [rendered output](#verify-the-rendered-output).

---

## Send conditions

A template condition (Design Studio, template settings, **Conditions**) enables or disables the whole template at send time, on every channel. To skip one channel and still deliver the rest, put the condition on that channel instead, in the channel's **Conditions** tab or on the send:

```typescript
await client.send.message({
  message: {
    to: { user_id: "user_123" },
    template: "order-shipped",
    data: { priority: "low" },
    channels: { sms: { if: "data.priority === 'high'" } }, // SMS only for high priority
  },
});
```

Condition changes in a template take effect after you publish it.

---

## Legacy templates

Templates built in the older designer (labeled **Design Studio Classic** in the console) keep sending with the same ID and alias, with no deadline and no migration step. The ID doesn't tell you which editor built a template: both produce `nt_` IDs, and older ones may have other formats.

- **Reads work.** `GET /notifications/{id}` and `GET /notifications/{id}/content` return legacy templates. Their content comes back as blocks and channels, not Elemental `elements`.
- **Writes and version history don't.** `PUT .../content`, `PUT .../elements/{id}` and `GET .../versions` return `422` with "created in the Legacy Designer and is not supported by this endpoint". `PUT .../locales/{locale}` returns `204` but writes nothing, so check with a `GET` after any locale write.
- **There's no converter.** To move a legacy template to Design Studio, create a new template (it gets a new ID), carry over its subscription topic, then point your sends at the new ID or alias. `GET /notifications` lists legacy templates with a `topic_id`; set it as `notification.subscription.topic_id` on the new template.

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
| Metrics | `GET` | `/notifications/{id}/metrics` | Delivery funnel as a time series. See [metrics.md](./metrics.md) |

### Create a Template

Every key below must be present (see the Rules above); `brand: null` sends with no brand chrome, see [Brands](./brands.md). Set `state` to `"PUBLISHED"` to skip the draft step.

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
      // @ts-expect-error accepted by the API, missing from the SDK type
      scope: "strict",
      elements: [
        {
          type: "channel",
          channel: "email",
          elements: [
            { type: "meta", title: "Your order {{data.order_id}} has shipped" },
            {
              type: "text",
              content: "Hi {{data.name}}, your package is on the way. Tracking: {{data.tracking_url}}."
            },
            { type: "action", content: "Track Shipment", href: "{{data.tracking_url}}" }
          ]
        }
      ]
    }
  },
  state: "DRAFT"
});

const templateId = response.id; // "nt_..." (response fields are at the top level)
```

Content with no elements is accepted, and a message rendered from it goes out with subject
`(no subject)` and an empty body, with no error. Fill in the content before publishing.

### Replace a Template

`PUT` replaces the whole template: send every field of the create body (`state` optional), or omitted fields reset (`tags` to `[]`, `brand` to `null`). `alias` is the exception: omit it to keep the template's aliases. For content-only changes use [`putContent`](#upload-content-to-an-existing-template).

### Upload Content to an Existing Template

`putContent` replaces just the **content** of a template, its Elemental `elements`, without touching name, tags, brand, subscription, or routing. Reach for it when you're syncing template bodies from code (a CMS export, a generated layout) and don't want to resend the whole `notification` object as `replace` requires. It writes to the **draft** by default (`state` defaults to `"DRAFT"`), so publish afterward to go live.

It replaces the whole element tree, translations included. The example below builds content from scratch, which is right for a new template. For a template that already has translations or Design Studio edits, [edit it in place](#edit-a-template-in-place) instead.

```typescript
await client.notifications.putContent("nt_01abc123", {
  content: { version: "2022-01-01", elements: [/* channel blocks, as in Create a Template */] },
});
await client.notifications.publish("nt_01abc123");
```

### Edit a Template in Place

To change part of an existing template, read the draft, change the element, and write the whole tree back. This keeps every element's `id` and `locales`. Strip what the write rejects first: every `checksum` (on elements and inside `locales`) and the `_`-prefixed keys Design Studio adds to translations (`_sourceHash` returns a `400`). Element checksums also tell you a teammate changed an element since you last read it.

**TypeScript:**
```typescript
const draft = await client.notifications.retrieveContent("nt_01abc123", { version: "draft" });
if (!("elements" in draft)) throw new Error("Legacy template: no Elemental elements to edit");

// Drop what the write rejects: checksums anywhere, and `_` keys (Design Studio's, inside locales).
const strip = (node: any): void => {
  if (Array.isArray(node)) return node.forEach(strip);
  if (node && typeof node === "object") {
    for (const key of Object.keys(node)) {
      if (key === "checksum" || key.startsWith("_")) delete node[key];
      else strip(node[key]);
    }
  }
};
const edit = (els: any[]): void => els.forEach((el) => {
  if (el.id === "elem_01kx4h2jdafq8bk9b0g5k7hs1e") el.content = "Track your order"; // the change
  if (el.elements) edit(el.elements);
});

strip(draft.elements);
edit(draft.elements);
await client.notifications.putContent("nt_01abc123", { content: { version: draft.version, scope: (draft as any).scope, elements: draft.elements } as any });
```

**Python:** the same calls are `retrieve_content(id, version="draft")` (a plain dict) and `put_content(id, content={"version": ..., "elements": ...})`; strip and edit the dict the same way.

If the element you changed has translations, they still hold the old text. Update them with `putLocale` ([localization.md](./localization.md)).

`client.notifications.putElement(elementId, { id: templateId, type, ... })` replaces the element with exactly the body you send (anything left out, including `locales`, is gone) and doesn't validate it. Prefer the read-modify-write above, and `putLocale` for translations.

### Publish

Publishing moves the current draft to live. After publishing, sends that reference this template ID will use the newly published content.

**TypeScript:**
```typescript
await client.notifications.publish("nt_01abc123");
```

Returns `204 No Content` on success.

### Verify the Rendered Output

`GET /messages/{id}/output` (SDK `client.messages.content(messageId)`, CLI `courier messages content --message-id`) returns exactly what Courier handed the provider, with variables resolved and brand chrome applied. Each `results[]` entry has `channel` and `content`: `subject`, `html` and `text` for email; `title`/`body` (plus `blocks` on chat channels) elsewhere. Template sends render the *published* version, so publish, send a test to yourself, and assert on this before real recipients see it.

For a single-recipient send the `requestId` is the message id; list and audience sends fan out to `<requestId>:<user_id>` ids (see [CLI](./cli.md)). A `404` or empty `results` right after sending means it hasn't rendered yet (`ENQUEUED`); re-check after a few seconds.

A stored template's plain-text part is delivered as stored, with Handlebars variables unrendered, so write it as final copy and keep `{{variables}}` in the Elemental/HTML content.

### List Templates

**TypeScript:**
```typescript
const { results, paging } = await client.notifications.list();

for (const template of results) {
  // V2 templates expose `name`; legacy templates expose `title`. Fall back across both.
  console.log(template.id, (template as any).name ?? (template as any).title);
}
```

Paginated. Use `paging.cursor` for the next page.

### List Versions and Roll Back

`client.notifications.listVersions(id)` returns `draft`, the current `published:vNNN`, and every historical `vNNN` (10 per page; pass `cursor` for older). Inspect one with `retrieveContent(id, { version: "v001" })`, then roll back by republishing it:

```typescript
await client.notifications.publish("nt_01abc123", { version: "v001" });
```

History is append-only: republishing v001 mints a new version (a copy of v001), so the rollback shows in the audit trail.

### Duplicate a Template

There is no duplicate method. Read the source template's content, then create a new template with it.

```typescript
// Read the draft: it has the latest edits and exists even if the template was never published.
const source = await client.notifications.retrieve("nt_01abc123", { version: "draft" });
const content = await client.notifications.retrieveContent("nt_01abc123", { version: "draft" });
if (!("elements" in content)) throw new Error("Legacy template: no Elemental elements to copy");

// Drop what the write rejects: checksums anywhere, and `_` keys (Design Studio's, inside locales).
const elements = JSON.parse(
  JSON.stringify(content.elements, (key, value) => (key === "checksum" || key.startsWith("_") ? undefined : value))
);

const copy = await client.notifications.create({
  notification: {
    name: `${source.name} (copy)`,
    tags: source.tags,
    brand: source.brand,
    subscription: source.subscription,
    routing: source.routing,
    content: { version: content.version, scope: (content as any).scope, elements } as any,
  },
});
```

Python makes the same calls: `client.notifications.retrieve(..., version="draft")`, `client.notifications.retrieve_content(..., version="draft")` (a plain dict), then `client.notifications.create(notification={...})`. Create rejects flat top-level elements, so if the source was stored without channel blocks, wrap its elements in one first.
The copy starts as a fresh draft, so [publish](#publish) it before sending.

### Draft/Publish Workflow

Writes (`replace`, `putContent`, `putLocale`) land on the draft; sends keep using the published version until you `publish`. Review with `retrieveContent(id, { version: "draft" })` first. `state: "PUBLISHED"` on create or replace skips the separate publish.

If the workspace uses submission checks (approval workflows), publishing locks the draft until the checks resolve: [Template Approval Workflow](https://www.courier.com/docs/design/templates/api#approval-workflow).

---

## Elemental Content Format

Template `content` is Elemental: `version: "2022-01-01"` plus `elements`, wrapped in `channel` blocks (see the Rules above). Element types, control flow (`if`, `loop`, `ref`, `channels`) and `locales`: [elemental.md](./elemental.md). Translation workflow: [localization.md](./localization.md).

---

## Full Lifecycle Example

End-to-end: create a multi-channel order confirmation template, publish it, then send.

Needs a routing strategy id (`rs_...`); create one first if you have none ([routing-strategies.md](./routing-strategies.md)).

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
      // @ts-expect-error accepted by the API, missing from the SDK type
      scope: "strict",
      elements: [
        {
          type: "channel",
          channel: "email",
          elements: [
            { type: "meta", title: "Order #{{data.order_id}} Confirmed" },
            { type: "text", content: "Hi {{data.name}}, thanks for your order!", align: "left" },
            {
              // @ts-expect-error accepted by the API, missing from the SDK type
              type: "group",
              loop: "data.items",
              elements: [
                { type: "text", content: "• {{$.item.name}} × {{$.item.qty}} — ${{$.item.price}}", align: "left" }
              ]
            },
            { type: "divider" },
            { type: "text", content: "Total: ${{data.total}}", text_style: "h2", align: "left" },
            { type: "action", content: "Track Order", href: "{{data.tracking_url}}" }
          ]
        },
        {
          type: "channel",
          channel: "sms",
          elements: [
            { type: "text", content: "Order #{{data.order_id}} confirmed! Total: ${{data.total}}. Track: {{data.tracking_url}}", align: "left" }
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

---

## Workspace vs Tenant Templates

This guide covers workspace templates (`/notifications`). Per-tenant overrides of a template (`client.tenants.templates.*`) are in [tenants.md](./tenants.md#tenant-scoped-templates).

## Related

- [Templates as Code](./templates-as-code.md) - repo sync, CI, drift detection, aliases, promotion
- [Elemental](./elemental.md) - element types and control flow
- [Localization](./localization.md) - translating a template
- [Device Preview](./device-preview.md) - screenshots on real email clients
- [Template Metrics](./metrics.md) - delivery funnel per template as a time series
- [Routing Strategies](./routing-strategies.md) - the `rs_...` a template routes through
- [Journeys](./journeys.md) - journey-scoped templates
- [Templates API](https://www.courier.com/docs/design/templates/api) - API endpoint reference

