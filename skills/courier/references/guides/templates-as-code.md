# Templates as Code

Run notification templates like software releases: your repo is the source of truth, every
change is validated before it ships, every release is verified against real rendered output,
and any prior version is one call away. All the pieces are native to the Templates API — this
page composes them into one repeatable workflow.

```
local files → validate → diff → push → publish → verify → (rollback if needed)
```

## 1. Local files are the source of truth

Keep one Elemental JSON file per template in your repo — the bare content document, exactly
the shape `GET /notifications/{id}/content` returns:

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
  curl -X PUT "https://api.courier.com/notifications/$SCRATCH_ID/content" \
    -H "Authorization: Bearer $COURIER_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-
```

## 3. Diff against the draft before pushing

A push overwrites the template's **draft** — which is also where Design Studio edits land.
So fetch the draft (`?version=draft`) and compare it to your local file before writing.
Normalize both sides: sort keys and drop the server-managed `id` and `checksum` fields so
the diff shows only real content changes:

```bash
diff <(jq -S 'del(.. | .id?, .checksum?)' order-shipped.json) \
     <(curl -s "https://api.courier.com/notifications/$TEMPLATE_ID/content?version=draft" \
         -H "Authorization: Bearer $COURIER_API_KEY" | jq -S 'del(.. | .id?, .checksum?)')
```

A non-empty diff before you've changed anything means the draft moved since your last sync —
usually a teammate's Design Studio edits. Pull those into the repo (the response body *is*
your file format) instead of overwriting them. To audit what's *live* rather than what's
in-progress, run the same diff with `?version=published`.

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

## Promotion between workspaces

The same loop promotes templates between environments: validate → diff → push → publish →
verify against the target workspace's API key, with the per-environment ids from your map.
Because the content files are identical, dev and prod stay provably in sync.

## Related

- [Templates](./templates.md) - Full template lifecycle and API reference
- [Elemental](./elemental.md) - Element types and properties
- [Brands](./brands.md) - Brand resolution and unbranded sending
