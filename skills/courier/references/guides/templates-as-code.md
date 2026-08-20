# Templates as Code

Run notification templates like software releases: your repo is the source of truth, every
change is validated before it ships, every release is verified against real rendered output,
and any prior version is one call away. All the pieces are native to the Templates API — this
page composes them into one repeatable workflow.

```
local files → validate → push → diff → publish → verify → (rollback if needed)
```

## 1. Local files are the source of truth

Keep one Elemental JSON file per template in your repo, plus a small map of file → template
id. Template IDs are workspace-specific, so map per environment for dev → prod promotion:

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
its error message — which makes it an excellent pre-flight check. Probe your content against
a scratch template in CI and validation failures diagnose themselves:

```bash
curl -X PUT "https://api.courier.com/notifications/$SCRATCH_ID/content" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d @order-shipped.json
```

## 3. Push

Create new templates as drafts, update existing ones with `PUT .../content` (which leaves
name, tags, and routing untouched). See [Create a Template](./templates.md#create-a-template)
and [Upload Content](./templates.md#upload-content-to-an-existing-template) — and note that
`PUT /notifications/{id}` is a full replacement, so prefer `PUT .../content` for
content-only changes.

## 4. Diff stored vs local

Before each push, fetch the stored content and compare it to your local file. Sort keys on
both sides and drop server-managed element fields (`id`, `checksum`) so the diff shows only
real content changes:

```bash
diff <(jq -S 'del(.. | .id?, .checksum?)' order-shipped.json) \
     <(curl -s "https://api.courier.com/notifications/$TEMPLATE_ID/content" \
         -H "Authorization: Bearer $COURIER_API_KEY" | jq -S 'del(.. | .id?, .checksum?)')
```

This keeps repo and workspace in sync in both directions: it surfaces edits made in the
Design Studio (so you can pull them into the repo instead of overwriting a teammate's work)
and confirms the workspace holds exactly what you think it does before you release.

## 5. Publish deliberately

Sends always use the published version, so drafts are free to iterate — publishing is your
release step. Confirm the draft (`GET .../draft/content`), then publish. See
[Draft/Publish Workflow](./templates.md#draftpublish-workflow).

## 6. Verify the release

Send a test and assert on the real rendered output — subject, HTML, and text part:

```
POST /send  →  requestId  →  GET /messages/{requestId}/output  →  results[].content.html
```

This is the exact email recipients receive, with merge variables, brand chrome, and channel
formatting applied — the definitive sign-off. See
[Verify the Rendered Output](./templates.md#verify-the-rendered-output).

## 7. Know your rollback

Every publish is preserved. `GET /notifications/{id}/versions` lists every release;
`POST /notifications/{id}/publish` with `{"version": "vNNN"}` republishes any of them.
History is append-only — a rollback mints a new version, so the audit trail stays complete.
See [List Versions and Roll Back](./templates.md#list-versions-and-roll-back).

## Promotion between workspaces

The same loop promotes templates between environments: validate → push → diff → publish →
verify against the target workspace's API key, with the per-environment ids from your map.
Because the content files are identical, dev and prod stay provably in sync.

## Related

- [Templates](./templates.md) - Full template lifecycle and API reference
- [Elemental](./elemental.md) - Element types and properties
- [Brands](./brands.md) - Brand resolution and unbranded sending
