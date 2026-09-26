# Device Preview

Device Preview renders a template's email on real email clients (Outlook, Gmail, Apple Mail, webmail, light and dark mode) and returns a screenshot from each. An agent can start a run, read the screenshots, fix what it sees, and run again, all before anything is sent.

## Quick Reference

### Rules

- **It's a paid add-on, billed per device.** Each device in a run is one preview; the Courier Recommended set is 8. Tell the user how many previews a run will use before starting it.
- **A `402` means the add-on isn't enabled.** Stop and tell the user to enable it in the console under **Settings → Billing**. Don't retry.
- **Rejected requests aren't billed.** A `400`, `402`, `404`, `409`, or `422` never creates a run.
- **Only Design Studio templates with an email channel.** Anything else returns a `422`. To preview HTML from another platform, wrap it in a template first ([below](#preview-html-from-another-platform)).
- **It renders the latest draft by default.** Pass `template_version: "published"` for the live version, or a zero-padded published version such as `v002` (`v2` returns a `400`).
- **Name the devices with exactly one of `device_set_id` or `device_ids`.**
- **Look up Courier Recommended by name.** Every workspace has one, with a different `pvs_` id in each environment.
- **Pass test values in `data`**: `data.profile` fills `{{profile.*}}`, `data.tenant` fills `{{tenant.*}}`, and other keys fill the template's own variables. A variable with no value renders as nothing.
- **Send a new `Idempotency-Key` per run.** A key reused within 25 hours returns the earlier run instead of starting one.
- **Runs finish asynchronously.** Read the run every 10 seconds for up to 5 minutes. It's done at `COMPLETED` or `FAILED`; each device settles on its own, and one failing device doesn't fail the run.
- **Screenshot URLs are short-lived signed links**, re-signed on every read. Download the images when you read the run, and read it again for fresh links later.
- Runs can't be cancelled or deleted. History is kept for a year and shows in the editor's **Preview history**.

### Common Mistakes

- Running without `data`, so the screenshot reads "Hi , your order has shipped." That's the most common "broken" preview
- Hardcoding a `pvs_` id copied from another environment
- Putting `template_id` in the body. The template is the path parameter; the body key is a `400`
- Filtering devices with `app === "outlook"` for Outlook desktop. That's the iPhone app; desktop versions are `outlook_2019`, `outlook_microsoft_365`, and so on
- Storing `screenshot_url` to show later. It expires
- Re-running the full set after every small fix. Re-run only the devices that looked wrong, then do one full pass
- Using Device Preview to check exact HTML or merge values. `messages.content` after a test send is free and exact

## Device Preview or rendered output?

| Need | Use |
|---|---|
| The exact subject, HTML, and text Courier handed the provider | `client.messages.content(messageId)` after a test send ([templates.md](./templates.md#verify-the-rendered-output)). Free |
| How that email looks in Outlook, Gmail, Apple Mail, dark mode, mobile | Device Preview. Paid, and no send needed |

## Run a preview

### 1. Find the device set

**Node:**
```typescript
const { results: sets } = await client.previews.listDeviceSets();
const recommended = sets.find((s) => s.name === "Courier Recommended");
if (!recommended) throw new Error("No Courier Recommended set in this workspace");
```

**Python:**
```python
sets = client.previews.list_device_sets().results
recommended = next(s for s in sets if s.name == "Courier Recommended")
```

### 2. Start the run

**Node:**
```typescript
const run = await client.notifications.previews.runs.create("nt_01abc123", {
  device_set_id: recommended.id,
  data: {
    profile: { name: "Sarah Bennett", email: "sarah@acme.com" },
    tenant: { name: "Acme Corp" },
    order_id: "1042",
  },
  "Idempotency-Key": crypto.randomUUID(),
});
// run.status === "PENDING", run.device_ids lists the devices it will render
```

**Python:**
```python
import uuid

run = client.notifications.previews.runs.create(
    "nt_01abc123",
    device_set_id=recommended.id,
    data={
        "profile": {"name": "Sarah Bennett", "email": "sarah@acme.com"},
        "tenant": {"name": "Acme Corp"},
        "order_id": "1042",
    },
    idempotency_key=str(uuid.uuid4()),
)
```

**CLI:** `courier notifications:previews:runs create --id nt_01abc123 --device-set-id "$SET_ID" --data '{"order_id": "1042"}' --idempotency-key "$(uuidgen)"`. **MCP:** `list_preview_device_sets`, then `create_preview_run`.

Optional: `template_version` (`published`, `v002`) and `locale` (see [Localized previews](#localized-previews)).

### 3. Wait, then download

**Node:**
```typescript
import { writeFile } from "node:fs/promises";

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
const deadline = Date.now() + 5 * 60_000;
let detail = await client.notifications.previews.runs.retrieve(run.id, { id: run.template_id });
while (!["COMPLETED", "FAILED"].includes(detail.status) && Date.now() < deadline) {
  await wait(10_000);
  detail = await client.notifications.previews.runs.retrieve(run.id, { id: run.template_id });
}

for (const r of detail.results) {
  if (r.status !== "COMPLETED" || !r.screenshot_url) continue;
  const res = await fetch(r.screenshot_url); // download now; the link expires
  await writeFile(`preview-${r.device_id}.png`, Buffer.from(await res.arrayBuffer()));
}
```

**Python:**
```python
import time, urllib.request

deadline = time.monotonic() + 5 * 60
detail = client.notifications.previews.runs.retrieve(run.id, id=run.template_id)
while detail.status not in ("COMPLETED", "FAILED") and time.monotonic() < deadline:
    time.sleep(10)
    detail = client.notifications.previews.runs.retrieve(run.id, id=run.template_id)

for r in detail.results:
    if r.status == "COMPLETED" and r.screenshot_url:
        urllib.request.urlretrieve(r.screenshot_url, f"preview-{r.device_id}.png")  # download now
```

**MCP:** `get_preview_run` with the template id and run id.

`results` can be empty while the run is in progress; entries appear as devices report, in no fixed order, so match them by `device_id`. Most screenshots are PNG; check each file's `Content-Type` rather than trusting the extension.

| Run `status` | Meaning |
|---|---|
| `PENDING`, `RENDERED`, `SUBMITTED` | In progress |
| `COMPLETED` | Every device has settled; check each result |
| `FAILED` | The run as a whole failed. `failure_reason` is `NO_EMAIL_CHANNEL`, `TEMPLATE_NOT_SUPPORTED`, `RENDER_FAILED`, `ALL_DEVICES_UNSUPPORTED` (pick other devices), or `VENDOR_ERROR` |

| Result `status` | Meaning |
|---|---|
| `PENDING`, `PROCESSING` | Still rendering; `screenshot_url` is `null` |
| `COMPLETED` | Screenshot ready |
| `TIMED_OUT` | The device didn't report in time |
| `UNSUPPORTED` | The device has been retired |
| `FAILED` | That device's render failed; `DELIVERY_FAILED` is an infrastructure fault, not the template |

## Review loop for agents

1. **Say what it will cost.** "This run uses 8 previews." For iteration, start with 1 to 3 devices via `device_ids`, such as one Outlook desktop, one mobile, and one dark mode.
2. **Run with realistic `data`** for every variable the template uses.
3. **Download and look at every screenshot.** Check:
   - blank gaps or stray punctuation from missing variables
   - copy that doesn't match its section
   - the subject line, on clients that show the inbox. Many screenshots show only the body, so check the subject with `messages.content` after a test send
   - broken or missing images
   - Outlook desktop layout: collapsed columns, oversized images, lost padding
   - mobile: columns that don't stack, text too small, buttons off-screen
   - dark mode: unreadable text, logos that disappear on dark backgrounds
4. **Fix the draft you read, in place.** Read it with `retrieveContent(id, { version: "draft" })`, change the one element that's wrong, drop the `checksum` fields, and `putContent` the whole tree back. Don't rebuild content from scratch: a write without the elements' `id`s and `locales` deletes the translations. For one language's text, use `putLocale` instead ([localization.md](./localization.md)).

   **Node:**
   ```typescript
   const draft = await client.notifications.retrieveContent("nt_01abc123", { version: "draft" });
   if (!("elements" in draft)) throw new Error("Legacy template: no Elemental elements to edit");
   const fix = (els: any[]) => els.forEach((el) => {
     delete el.checksum;
     if (el.locales) Object.values(el.locales).forEach((l: any) => delete l.checksum);
     if (el.id === "elem_01kx4h2jdafq8bk9b0g5k7hs1e") el.content = "Track your order"; // the change
     if (el.elements) fix(el.elements);
   });
   fix(draft.elements);
   await client.notifications.putContent("nt_01abc123", { content: { version: draft.version, elements: draft.elements as any } });
   ```

   **Python:**
   ```python
   content = client.notifications.retrieve_content("nt_01abc123", version="draft")  # a plain dict

   def fix(els):
       for el in els:
           el.pop("checksum", None)
           for l in (el.get("locales") or {}).values():
               l.pop("checksum", None)
           if el.get("id") == "elem_01kx4h2jdafq8bk9b0g5k7hs1e":
               el["content"] = "Track your order"  # the change
           fix(el.get("elements") or [])

   fix(content["elements"])
   client.notifications.put_content("nt_01abc123", content={"version": content["version"], "elements": content["elements"]})
   ```
5. **Re-run only the devices that looked wrong** with `device_ids`, then one final run on the full set.
6. **Publish only when the user says so.** Previews render the draft, so nothing reaches recipients until then.

## Localized previews

Pass `locale` to render a translation. It must be the exact locale key the template uses (case included), the same rule as sends; see [localization.md](./localization.md). Run once per language that matters. Longer translations are where buttons wrap and Outlook tables overflow.

**Node:** `client.notifications.previews.runs.create("nt_01abc123", { device_ids, locale: "de", data, "Idempotency-Key": crypto.randomUUID() })`

**Python:** `client.notifications.previews.runs.create("nt_01abc123", device_ids=device_ids, locale="de", data=data, idempotency_key=str(uuid.uuid4()))`

## Choose devices

`client.previews.listDevices()` (Python: `client.previews.list_devices()`) returns the catalog. Each device has a `pvd_` id, a readable `name` (such as `Outlook Microsoft 365 (Windows 11, dark mode)`), and fields to filter on:

| Field | Values |
|---|---|
| `category` | `desktop`, `mobile`, `webmail` |
| `app` | One per client and version: `apple_mail`, `gmail` (the mobile app), `gmail_com` (webmail), `outlook` (the iPhone app), `outlook_2016` … `outlook_2024`, `outlook_microsoft_365`, `outlook_office_365`, `outlook_com`, `yahoo_com`, and more |
| `platform` | Hardware or browser: `iphone`, `pixel`, `chrome`, `edge`, `firefox`; `null` on desktop |
| `os`, `os_version` | `windows`, `macos`, `ios`, `android` |
| `theme` | `light`, `dark` |

Match app families by prefix, since each Outlook version is its own `app`:

```typescript
const { results: devices } = await client.previews.listDevices();
const outlookDesktop = devices.filter((d) => d.category === "desktop" && d.app.startsWith("outlook")).map((d) => d.id);
const gmailDark = devices.filter((d) => d.app.startsWith("gmail") && d.theme === "dark").map((d) => d.id);
```

- **One-off run:** pass `device_ids` instead of `device_set_id` (CLI: repeat `--device-id pvd_...` once per device). An id not in the catalog returns a `422`.
- **Reusable set:** `client.previews.createDeviceSet({ name, device_ids })` (Python: `create_device_set(name=..., device_ids=...)`). It also appears in the editor's **Targets** dropdown.
- `updateDeviceSet(id, { name, device_ids })` replaces both fields in full. `archiveDeviceSet(id)` archives it; past runs keep their own copy of the devices.
- **Courier Recommended can't be changed or archived** (`409`). Copy its `device_ids` into your own set to adjust it.
- MCP: `list_preview_devices`, `create_preview_device_set`, `replace_preview_device_set`, `archive_preview_device_set`.

## Preview HTML from another platform

Device Preview doesn't need Courier to send the email. Create a template around the existing HTML, with a `meta` element for the subject and an `html` element for the markup, then run a preview on its `id`:

```json
{
  "notification": {
    "name": "Order shipped (preview)",
    "tags": [], "brand": null, "subscription": null, "routing": null,
    "content": {
      "version": "2022-01-01",
      "elements": [
        {
          "type": "channel", "channel": "email",
          "elements": [
            { "type": "meta", "title": "Your order has shipped" },
            { "type": "html", "content": "<table role=\"presentation\" width=\"600\"><tr><td>Hi {{profile.name}}, order {{order_id}} is on its way.</td></tr></table>" }
          ]
        }
      ]
    }
  },
  "state": "DRAFT"
}
```

Send that body with `client.notifications.create(...)` (see [templates.md](./templates.md#create-a-template)).

## Errors

| Status | When |
|---|---|
| `400` | Both or neither of `device_set_id` and `device_ids`; an unknown body key such as `template_id`; a malformed version such as `v2` |
| `402` | The add-on isn't enabled |
| `404` | The template, device set, or run doesn't exist. A run is only readable under the template it previewed |
| `409` | Changing or archiving Courier Recommended |
| `422` | A device id not in the catalog; a version the template doesn't have; not a Design Studio template or no email channel |

## Related

- [Templates](./templates.md): drafts, publishing, rendered output
- [Localization](./localization.md): translations to preview
- [Email](../channels/email.md): deliverability and the pre-send checklist
- [Device Preview docs](https://www.courier.com/docs/design/templates/device-preview): editor walkthrough and the full client catalog
