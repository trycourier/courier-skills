# Device Preview

Device Preview renders a template's email on real email clients (Outlook, Gmail, Apple Mail, webmail, light and dark mode) and returns a screenshot from each. An agent can start a run, read the screenshots, fix what it sees, and run again, all before anything is sent.

Examples assume an initialized `client`. Install and API key setup are in [quickstart.md](./quickstart.md).

## Quick Reference

### Rules

- **It's a paid add-on, counted per device.** Each device in a run uses one preview from the plan's monthly allowance, then overage; the Courier Recommended set is 8. Tell the user how many previews a run will use before starting it.
- **A `402` means the add-on isn't enabled or its billing is suspended.** Stop and tell the user to check the console under **Settings → Billing**. Don't retry.
- **Rejected run requests aren't billed.** A `400`, `402`, `404`, or `422` never creates a run.
- **Only Design Studio templates with an email channel.** Anything else returns a `422`. To preview HTML from another platform, wrap it in a template first ([below](#preview-html-from-another-platform)).
- **It renders the latest draft by default.** Pass `template_version: "published"` for the live version, or a zero-padded published version such as `v002` (`v2` returns a `400`).
- **Name the devices with exactly one of `device_set_id` or `device_ids`.**
- **Look up Courier Recommended by name.** Every workspace has one, with a different `pvs_` id in each environment.
- **Pass test values in `data`**: `data.profile` fills `{{profile.*}}`, `data.tenant` fills `{{tenant.*}}`, and other keys fill the template's own variables.
- **Send an `Idempotency-Key`: a new one per run, the same one when retrying a create.** A key reused within 25 hours returns the earlier run; a retry with a new key starts, and bills, a second run.
- **Runs finish asynchronously**, in 10 to 120 seconds; Outlook clients usually report last. Read the run every 10 seconds for up to 5 minutes. It's done at `COMPLETED` or `FAILED`; each device settles on its own, and one failing device doesn't fail the run.
- **Screenshot URLs are short-lived signed links**, re-signed on every read. Download the images when you read the run, and read it again for fresh links later.
- Runs can't be cancelled or deleted. History is kept for a year: `client.notifications.previews.runs.list(templateId)` (MCP: `list_preview_runs`) and the editor's **Preview history**.

### Common Mistakes

- Running without `data`. A variable with no value renders as nothing, so the screenshot reads "Hi , your order has shipped." That's the most common "broken" preview
- Hardcoding a `pvs_` id copied from another environment
- Putting `template_id` in the body. The template is the path parameter; the body key is a `400`
- Filtering devices with `app === "outlook"` for Outlook desktop. That's the iPhone app; desktop versions are `outlook_2019`, `outlook_microsoft_365`, and so on
- Storing `screenshot_url` to show later. It expires
- Re-running the full set after every small fix. Re-run only the devices that looked wrong, then do one full pass

## Device Preview or rendered output?

| Need | Use |
|---|---|
| The exact subject, HTML, and text Courier handed the provider | `client.messages.content(messageId)` after a test send ([templates.md](./templates.md#verify-the-rendered-output)). No preview charge, but the test send is a real message |
| How that email looks in Outlook, Gmail, Apple Mail, dark mode, mobile | Device Preview. Uses previews, and needs no send |

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
recommended = next((s for s in sets if s.name == "Courier Recommended"), None)
if recommended is None:
    raise RuntimeError("No Courier Recommended set in this workspace")
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

if (!["COMPLETED", "FAILED"].includes(detail.status)) {
  console.warn(`Run ${run.id} is still ${detail.status} after 5 minutes; report the devices with no result yet`);
}

for (const r of detail.results) {
  if (r.status !== "COMPLETED" || !r.screenshot_url) continue;
  const res = await fetch(r.screenshot_url); // download now; the link expires
  if (!res.ok) throw new Error(`Download failed (${res.status}); read the run again for a fresh link`);
  const ext = (res.headers.get("content-type") ?? "image/png").split("/")[1];
  await writeFile(`preview-${r.device_id}.${ext}`, Buffer.from(await res.arrayBuffer()));
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

if detail.status not in ("COMPLETED", "FAILED"):
    print(f"Run {run.id} is still {detail.status} after 5 minutes; report the devices with no result yet")

for r in detail.results:
    if r.status == "COMPLETED" and r.screenshot_url:
        with urllib.request.urlopen(r.screenshot_url) as resp:  # download now; raises on an expired link
            ext = resp.headers.get_content_subtype()
            with open(f"preview-{r.device_id}.{ext}", "wb") as f:
                f.write(resp.read())
```

**MCP:** `get_preview_run` with the template id and run id.

`results` can be empty while the run is in progress; entries appear as devices report, in no fixed order, so match them by `device_id`. Each finished result has a full-size `screenshot_url` and a grid-size `thumbnail_url`. Most screenshots are PNG, but take the file type from `Content-Type`, as above. `detail.template_version` records what was rendered: the published version if the draft matches it, otherwise `draft`.

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
4. **Fix the draft you read, in place**: read it, change the element that's wrong, and write the whole tree back, keeping every `id` and `locales` ([Edit a Template in Place](./templates.md#edit-a-template-in-place) has the Node and Python code). Don't rebuild content from scratch: that deletes the translations. If the element you fixed has translations, update them with `putLocale` too ([localization.md](./localization.md)).
5. **Re-run only the devices that looked wrong** with `device_ids`, then one final run on the full set.
6. **Publish only when the user says so.** Previews render the draft, so nothing reaches recipients until then.

## Localized previews

Pass `locale` to render a translation. Use the key exactly as the template stores it (sends match locale codes case-sensitively; see [localization.md](./localization.md)), and check that the screenshot is actually in that language. A key that doesn't match likely renders the default content and still uses previews. Run once per language that matters: longer translations are where buttons wrap and Outlook tables overflow.

**Node:** `client.notifications.previews.runs.create("nt_01abc123", { device_ids: ["pvd_0rk8bz6ywhbydvhfh6xv0bw8ep"], locale: "de", data: { order_id: "1042" }, "Idempotency-Key": crypto.randomUUID() })`

**Python:** `client.notifications.previews.runs.create("nt_01abc123", device_ids=["pvd_0rk8bz6ywhbydvhfh6xv0bw8ep"], locale="de", data={"order_id": "1042"}, idempotency_key=str(uuid.uuid4()))`

## Choose devices

`client.previews.listDevices()` (Python: `client.previews.list_devices()`) returns the catalog. Each device has a `pvd_` id, a readable `name` (such as `Outlook Microsoft 365 (Windows 11, dark mode)`), and fields to filter on:

| Field | Values |
|---|---|
| `category` | `desktop`, `mobile`, `webmail` |
| `app` | Mobile: the app (`apple_mail`, `gmail`, `outlook`). Desktop: the app with its version (`apple_mail_16`, `outlook_2016` … `outlook_2024`, `outlook_microsoft_365`, `outlook_office_365`). Webmail: the service (`gmail_com`, `outlook_com`, `yahoo_com`, `aol_com`, and more) |
| `platform`, `platform_version` | Phone or browser (`iphone`, `pixel`, `chrome`, `edge`, `firefox`) and its model or version; `null` on desktop |
| `os`, `os_version` | `windows`, `macos`, `ios`, `android`, and the OS version |
| `theme` | `light`, `dark` |

Always filter on `category` as well as `app`: `outlook` alone is the iPhone app, and an `outlook` prefix also matches `outlook_com` webmail. A filter can match many devices (there are 14 Outlook desktop ones), so pick the ones you mean and check the count before running. The two 120-dpi Outlook devices match their 100% siblings on every field except `name`:

```typescript
const { results: devices } = await client.previews.listDevices();
const picks = [
  devices.find((d) => d.app === "outlook_microsoft_365" && d.os === "windows" && d.theme === "light"),
  devices.find((d) => d.app === "gmail_com" && d.theme === "dark"),
].filter((d) => d !== undefined);
const device_ids = picks.map((d) => d.id); // 2 devices = 2 previews
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
| `402` | The add-on isn't enabled, or its billing is suspended |
| `404` | The template, device set, or run doesn't exist. A run is only readable under the template it previewed |
| `409` | Changing or archiving Courier Recommended |
| `422` | A device id not in the catalog; a version the template doesn't have; not a Design Studio template or no email channel |

## Related

- [Templates](./templates.md): drafts, publishing, rendered output
- [Localization](./localization.md): translations to preview
- [Email](../channels/email.md): deliverability and the pre-send checklist
- [Device Preview docs](https://www.courier.com/docs/design/templates/device-preview): editor walkthrough and the full client catalog
