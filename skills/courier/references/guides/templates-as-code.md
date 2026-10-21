# Templates as Code

Run notification templates like software releases: your repo is the source of truth, every
change is validated before it ships, every release is verified against real rendered output,
and any prior version is one call away. All the pieces are native to the Templates API — this
page composes them into one repeatable workflow.

```
local files → validate → diff → push → publish → verify → (rollback if needed)
```

## Quick Reference

### Rules
- Local files are the source of truth; validate, diff against the draft, then push.
- Sends always use the published version, so drafts are free to iterate. Publishing is the release.
- Rollback is `publish { "version": "v001" }`. History is append-only, so the rollback itself lands as a new version.
- Sends take the `nt_...` ID or a template alias. Content, publish, versions and locales calls take the `nt_...` ID.
- Keep element `id`s and `locales` in the repo files. A push replaces the draft's whole content, translations included.

### Common Mistakes
- Pushing without diffing and overwriting dashboard edits.
- Stripping `id`s or `locales` from the repo files. Pushing them back gives every element a new id and deletes every translation made in Design Studio or with `putLocale`.
- Treating a push as a release. Nothing changes for recipients until you publish.

## 1. Local files are the source of truth

Keep one Elemental JSON file per template in your repo: the bare content document
(`version` + `elements`), as `GET /notifications/{id}/content?version=draft` returns it, minus
every `checksum` and the `_`-prefixed keys Design Studio adds inside `locales`. **Keep each
element's `id` and `locales`.** Translations are addressed by element id, and a push replaces
`locales` along with everything else (see [localization.md](./localization.md#replace-all-content)).
Save a draft in that format with one jq filter, reused for every diff below:

```bash
NORMALIZE='{version, elements}
  | walk(if type == "object"
         then with_entries(select(.key != "checksum" and (.key | startswith("_") | not)))
         else . end)'

curl -sf "https://api.courier.com/notifications/$TEMPLATE_ID/content?version=draft" \
  -H "Authorization: Bearer $COURIER_API_KEY" | jq -S "$NORMALIZE" > order-shipped.json
```

A brand-new template's file has no ids yet: create the template, then save it back through
`$NORMALIZE` so the repo holds the ids Courier assigned. The file looks like this:

```jsonc
// order-shipped.json
{ "version": "2022-01-01", "elements": [ /* ... */ ] }
```

Add a small map of file → template id. Template IDs are workspace-specific, so map per
environment for dev → prod promotion:

```jsonc
// templates.map.json
{
  "order-shipped": { "dev": "nt_01dev...", "prod": "nt_01prod..." },
  "welcome":       { "dev": "nt_02dev...", "prod": "nt_02prod..." }
}
```

Name templates by their trigger (`order-shipped`, not `email-v2-final`) and tag them by
category (`transactional`, `marketing`) — tags are filterable in the dashboard and the API.

## 2. Validate before pushing

`PUT /notifications/{id}/content` validates Elemental deeply and names the offending key in
its error message — which makes it an excellent pre-flight check. The request body nests the
content document under a `content` key, so wrap the file at request time. Probe against a
scratch template in CI and validation failures diagnose themselves:

```bash
jq '{content: .}' order-shipped.json | \
  curl --fail-with-body -X PUT "https://api.courier.com/notifications/$SCRATCH_ID/content" \
    -H "Authorization: Bearer $COURIER_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-
```

`--fail-with-body` makes curl exit non-zero on a validation error while still printing the
error body (the part that names the offending key) — without it, a 400 exits 0 and a CI
step passes green on broken content.

This probe doesn't check for channel blocks: only creating a template does. So also check
that every top-level element in the file is a `channel` element. Otherwise new templates fail
to create, and existing ones open empty in Design Studio (see
[templates.md](./templates.md#quick-reference)):

```bash
jq -e '[.elements[] | select(.type != "channel")] | length == 0' order-shipped.json
```

## 3. Diff against the draft before pushing

A push overwrites the template's **draft** — which is also where Design Studio edits land.
So fetch the draft (`?version=draft`), run it through the same `$NORMALIZE` filter, and compare
it to your local file before writing:

```bash
diff <(jq -S "$NORMALIZE" order-shipped.json) \
     <(curl -sf "https://api.courier.com/notifications/$TEMPLATE_ID/content?version=draft" \
         -H "Authorization: Bearer $COURIER_API_KEY" | jq -S "$NORMALIZE")
```

`-f` makes the fetch fail loudly on an HTTP error — a bad key or template id should stop the
check, not be diffed as if it were content. A non-empty diff on a *successful* fetch before
you've changed anything means the draft moved since your last sync — usually a teammate's
Design Studio edits or new translations. Don't overwrite either side. With no local changes
yet, save the draft through `$NORMALIZE` over your file. When both changed, merge the draft's
changes (usually new `locales`) into your file, then push. Pulling before you start editing
avoids the merge. To audit what's *live* rather than
what's in-progress, run the same diff with `?version=published`.

**If a translation tool owns the translations** rather than the repo, diff with
`"$NORMALIZE | del(.. | .locales?)"` on both sides. A push without `locales` deletes them, so
after each push re-apply the tool's translations with `putLocale`, then publish. See
[localization.md](./localization.md).

## 4. Push

Update content with `PUT .../content` (leaves name, tags, and routing untouched; writes to
the draft); create new templates as drafts. See
[Upload Content](./templates.md#upload-content-to-an-existing-template) and
[Create a Template](./templates.md#create-a-template) — and note that
`PUT /notifications/{id}` is a full replacement, so prefer `PUT .../content` for
content-only changes.

## 5. Publish deliberately

Sends always use the published version, so drafts are free to iterate — publishing is your
release step. Confirm the draft one last time (`GET .../content?version=draft`), then
publish. See [Draft/Publish Workflow](./templates.md#draftpublish-workflow).

## 6. Verify the release

Send a test and assert on the real rendered output — the exact subject, HTML, and text part
the recipient receives. Workflow and response shape:
[Verify the Rendered Output](./templates.md#verify-the-rendered-output).

## 7. Know your rollback

Inspect any historical version's content with `GET .../content?version=v001`, then republish
it with `publish {"version": "v001"}` — history is append-only, so the rollback itself lands
in the audit trail. Calls and details:
[List Versions and Roll Back](./templates.md#list-versions-and-roll-back).

## Template aliases

An alias is a name you choose that stands in for a template's `nt_...` ID on a send. It reads
better in app code, and you can point the name at a different template without touching call sites.

- **Set one** with `notification.alias` on `POST /notifications` or `PUT /notifications/{id}`, or in
  Design Studio under the template's settings, **Alias**.
- **Send by alias** by passing it as `template`.
- **An alias belongs to one template.** Claiming one that another template holds returns `409`, and
  nothing changes. An alias can't start with `tenant/` (`400`).
- **`PUT` without `alias` keeps the template's aliases.** A string replaces them. `null` removes them all.
- **Reads** return `alias` as a string, as an array for a template with several, or leave it out when
  there is none.
- **Management calls take the `nt_...` ID** (content, publish, versions, locales). Keep
  `templates.map.json` for pushes and promotion. The metrics endpoint also accepts an alias.

**TypeScript:**

```typescript
await client.notifications.create({
  notification: {
    name: "Order shipped",
    tags: [],
    brand: null,
    subscription: null,
    routing: null,
    content: {
      version: "2022-01-01",
      elements: [
        {
          type: "channel",
          channel: "email",
          elements: [
            { type: "meta", title: "Your order shipped" },
            { type: "text", content: "Order {{order_id}} is on its way." },
          ],
        },
      ],
    },
    alias: "order-shipped",
  },
});

await client.send.message({
  message: { to: { user_id: "user-123" }, template: "order-shipped", data: { order_id: "ORD-9042" } },
});
```

**Python:**

```python
client.send.message(
    message={"to": {"user_id": "user-123"}, "template": "order-shipped", "data": {"order_id": "ORD-9042"}}
)
```

Agent guidance:

- Use an alias when the user wants a readable name, or one they can repoint to another template.
- On `409`, pick another name, or clear the alias from the template that holds it first.
- Don't build an app-side alias map for sends. Courier resolves the alias.

## Promotion between workspaces

The same loop promotes templates between environments: validate → diff → push → publish →
verify against the target workspace's API key, with the per-environment ids from your map.
Because the content files are identical, dev and prod stay provably in sync.

## Related

- [Templates](./templates.md) - Full template lifecycle and API reference
- [Elemental](./elemental.md) - Element types and properties
- [Brands](./brands.md) - Brand resolution and unbranded sending
