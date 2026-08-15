# User Preferences

Subscription topics let users control which notifications they get and on which channels. Courier
checks them on every send, so the enforcement lives in Courier rather than in your code.

## Quick Reference

### Rules
- **A user preference is an override on a topic's default**, not a standalone value. Topics are defined in the Preferences Editor with a default; a user falls back to it until they set their own choice
- **Two levels, easy to conflate.** A topic's `default_status` is `OPTED_IN`, `OPTED_OUT`, or `REQUIRED`. A user's own `status` is only `OPTED_IN` or `OPTED_OUT`. `REQUIRED` is a topic default that no user status overrides
- **Mapping a template to a topic is what makes enforcement happen.** An unmapped template sends regardless of preferences. Each template maps to exactly one topic
- **An opted-out send is skipped silently.** No error, no message. Check the logs, not the response
- **Channel selection is enabled per section**, not per topic
- **Editor changes are a draft until you publish.** Preview Page opens the draft; Publish makes it live
- **Preference and unsubscribe URLs need `to.user_id` on the send**, or they render empty

### Common Mistakes
- Leaving a template unmapped from any topic, then wondering why preferences aren't applied
- Using the wrong variable syntax for the editing context, which renders nothing at all (see [Linking to the page](#linking-to-the-page))
- Putting an unsubscribe link on a template mapped to a `REQUIRED` topic, where the opt-out silently does nothing
- Setting `custom_routing` without `has_custom_routing: true`, so the channel list is ignored
- Using bulk `PUT` when you meant `POST`, which resets every override you did not send
- Reimplementing suppression in application code instead of letting topic status gate the send

## The Model

| Piece | What it is | Where it lives |
|---|---|---|
| **Topic** | A category users opt in or out of, with a default state | Preferences Editor |
| **Section** | A named group of topics, and the unit that enables channel selection | Preferences Editor |
| **Template mapping** | Ties a template to one topic, which is what triggers enforcement | Design Studio template settings, or the API |
| **User preference** | That user's override on a topic's default | User Preferences API, hosted page, or embedded UI |

Reading returns the user's `status` alongside the topic's `default_status`. Writing sets overrides,
so you only need to send topics where the user differs from the default. Deleting an override
reverts that topic to its default.

Topics also carry arbitrary metadata you set through the API, useful for filtering or driving layout
in a custom preference page.

### How preferences interact with routing

1. Courier builds the channel list from `routing.channels`
2. It removes any channel the user disabled for the mapped topic
3. With `method: "single"` it tries the remaining channels in order
4. If nothing remains, the message is skipped silently

Routing of `["email", "push", "sms"]` where the user dropped SMS for this topic tries email and push only.

## Setting It Up

Everything is configured in the **Preferences Editor** ([Settings > Preferences](https://app.courier.com/settings/preferences)),
which is organised top down: page settings, then sections, then topics. Templates map to topics from
the template side.

**1. Page settings** apply to the whole page: the [brand](./brands.md) (logo, colors, typography),
the heading, the description, and the **channel names** users see. Rename channels to match your
product's language, for example "In-App" to "Inbox" or "Push" to "Mobile Push".

**2. Create a section.** Sections group related topics under a heading you name, and are the unit
that enables channel selection. Each has an auto-generated **ID** used in the API, a heading, and an
optional description shown beneath it. Reorder them to control how they appear.

**3. Create topics inside the section.** Each topic has a name, its section, and a default state:

| Default | Behavior |
|---|---|
| **On** (`OPTED_IN`) | Users receive these unless they opt out |
| **Off** (`OPTED_OUT`) | Users receive nothing until they opt in |
| **Required** (`REQUIRED`) | Users can't opt out. For things like security alerts |

**4. Map templates to topics.** This is the step that makes enforcement happen. In Design Studio,
open the template's settings and choose a subscription topic. Through the API it is the
`subscription` field on the template, set to `{ "topic_id": "<TOPIC_ID>" }` or `null`:

```bash
curl -X POST https://api.courier.com/notifications \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"notification":{"name":"Order shipped","subscription":{"topic_id":"TOPIC_ID"},
       "content":{"version":"2022-01-01","elements":[]}}}'
```

To change an existing template's topic, `PUT /notifications/{id}` replaces the whole template, so
fetch it first, update `subscription`, and send the full payload back. See [templates.md](./templates.md).

**5. Publish.** Editing preferences never affects users immediately. Every change saves as a draft
and users keep seeing the last published version until you publish.

| Control | Does |
|---|---|
| **Save** | Keeps changes as a draft |
| **Preview Page** | Opens the page as a user would see it, with unpublished changes and a "Draft mode" banner |
| **Publish** | Makes the draft live. **View Page** then opens the live page |

Embedded preferences render whatever is published, so use Preview Page to check a draft first.

## User Preferences API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/users/{user_id}/preferences` | List the user's overrides |
| `PUT` | `/users/{user_id}/preferences` | Replace the entire override set (bulk) |
| `POST` | `/users/{user_id}/preferences` | Create or update without touching others (bulk) |
| `GET` | `/users/{user_id}/preferences/{topic_id}` | Read one topic |
| `PUT` | `/users/{user_id}/preferences/{topic_id}` | Create or update one topic |
| `DELETE` | `/users/{user_id}/preferences/{topic_id}` | Reset one topic to its default |

Add a `tenant_id` query parameter to any of these to scope preferences to one tenant.

**Read:**
```typescript
const prefs = await client.users.preferences.retrieve("user-123");
// items[]: { topic_id, topic_name, status, default_status, has_custom_routing, custom_routing }
```
```python
prefs = client.users.preferences.retrieve("user-123")
```

**Write one topic.** The topic must already exist in the Preferences Editor; these calls set the
*user's* preference, they do not create the topic definition. An unknown topic returns 404. Note that
the body wraps the preference in a `topic` object:

```typescript
await client.users.preferences.updateOrCreateTopic("weekly-digest", {
  user_id: "user-123",
  topic: {
    status: "OPTED_IN",
    has_custom_routing: true,          // required, or custom_routing is ignored
    custom_routing: ["email", "push"],
  },
});
```
```python
client.users.preferences.update_or_create_topic(
    "weekly-digest",
    user_id="user-123",
    topic={"status": "OPTED_OUT"},
)
```

### Replace vs update

Both bulk endpoints take a `topics` array. They differ in what happens to the topics you **don't** send.

| | Replace (`PUT`) | Update (`POST`) |
|---|---|---|
| Scope | The user's entire override set | Only the topics you send |
| Omitted topics | **Reset to their default** | Left untouched |
| Failure handling | Atomic. One bad topic fails the whole request | Partial. Bad topics land in `errors` with a reason |
| Response | `items` plus `deleted` (overrides that were reset) | `items` plus `errors` |
| Best for | Syncing a user to a source of truth | Adding or changing a few topics |

An empty `topics` array on `PUT` clears every override. That is the trap: a partial `PUT` silently
resets everything you left out.

**Importing existing preferences** from another system is the main use for `PUT`. Define the topics
first so you have their IDs, then send one request per user carrying only the topics where they
differ from the default. It's idempotent, so the import is safe to re-run.

### Field reference

| Field | Notes |
|---|---|
| `topic_id` | The subscription topic the preference applies to |
| `status` | `OPTED_IN` or `OPTED_OUT`. `REQUIRED` is a topic default, not a user choice |
| `has_custom_routing` | Must be `true` for `custom_routing` to apply |
| `custom_routing` | `email`, `sms`, `push`, `inbox`, `direct_message`, `webhook` |
| `default_status` | The topic's default, returned on reads. Applies when the user has no override |
| `topic_name` | Display name, returned on reads |

## Channel Selection

Enabling channel selection on a **section** lets users pick channels for the topics inside it. Their
choices land in `custom_routing`, which only populates for sections where it's enabled. Users see the
channel display names configured in page settings, not the raw enum values.

> Template [send conditions](https://www.courier.com/docs/platform/content/template-settings/send-conditions)
> do not override a user's `custom_routing`. To drop a channel when required data is missing, use
> variable guardrails instead.

## Tenant Preferences (Multi-Tenant)

In a multi-tenant workspace a user can hold different preferences per tenant: alerts on for
`prod-project`, off for `stage-project`. At send time Courier merges five layers top to bottom,
each overriding the one above it, with only explicitly set fields applied:

1. Workspace-level topic defaults (the Preferences Editor)
2. Parent tenant defaults (inherited down the tenant hierarchy)
3. The tenant's own defaults (`tenants.preferences.items`, see [tenants.md](./tenants.md#per-tenant-preference-overrides))
4. The user's global preferences
5. The user's per-tenant overrides (highest priority)

Read or write the per-tenant layer by adding `tenant_id` as a query parameter on any
[User Preferences API](#user-preferences-api) call. The embedded UI scopes the same way, via
`tenantId` on `signIn`.

## Hosted Preference Center

A Courier-hosted, responsive page where users manage their own preferences, with no frontend to
build. Everything on it comes from the Preferences Editor: the topics and sections users see, and the
[brand](./brands.md) supplying logo, colors, and typography. Update the brand and the page follows.

Changes stay in a draft until you publish. **Preview Page** opens it in draft mode.

<a id="linking-to-the-page"></a>

### Linking to the page

Courier generates a secure, per-user URL at send time from the `urls.preferences` variable. You never
construct it yourself, but the send must include `to.user_id` or it resolves empty.

**The syntax depends on the editing context, and the wrong one renders nothing at all:**

| Context | Syntax |
|---|---|
| Content blocks (Text, Markdown, Quote, List) | `{{$.urls.preferences}}` |
| Handlebars (Template blocks, email templates, brand templates) | `{{var "urls.preferences"}}` |
| Elemental JSON (action buttons, links) | `{$.urls.preferences}` |

```json
{ "type": "action", "content": "Manage preferences", "href": "{$.urls.preferences}", "style": "button" }
```

Put it in a template's content for contextual access, or once in the brand footer so it appears on
every message. Preview emails render a sample URL rather than a live one, since they aren't sent to real users.

### Unsubscribe links

`urls.unsubscribe` is a one-click opt-out from the topic tied to that notification, removing the user
from all of that topic's templates and channels. Same three syntaxes as above. Clicking it lands on a
hosted confirmation page showing the updated status.

Two ways it silently does nothing:

- **The template has no topic assigned.** The URL resolves to an empty string. Assign a topic first.
- **The topic's default is `REQUIRED`.** The link renders and the confirmation page loads, but the
  opt-out has no effect and the user stays subscribed. Leave unsubscribe links off templates mapped
  to Required topics rather than showing a control that does nothing.

`List-Unsubscribe` headers are **not** automatic. Each topic has an **Unsubscribe Headers** setting
controlling whether Courier adds the header for that topic's emails, and it also has to be enabled in
your email provider's own settings (SendGrid, Mailgun, and so on).

## Digest Schedules

Digests are configured per topic in the Preferences Editor under **Digest settings**, and recipients
pick their frequency in the preference center. Add up to four delivery schedules; the first is the
default and they can be reordered.

| Frequency | Delivers |
|---|---|
| Instant | Immediately, not collected. This is how a recipient opts out of batching |
| Daily | Once a day (time, timezone) |
| Every weekday | Monday to Friday (time, timezone) |
| Multiple days | On the days you choose (time, timezone) |
| Weekly | Once a week (day, time, timezone) |
| Monthly | Once a month (day of month, time, timezone) |

Two different templates are involved: the ones **mapped to the topic** are what get collected, and
the **digest template** set in Digest settings renders them as one message. **Until you link a digest
template, the topic's notifications send individually instead of batching.** Collected requests show
a `DIGESTED` status in the logs.

### Categories and the template payload

Categories are optional and separate different kinds of item within one digest, so a single digest
can group, say, comments and mentions under distinct sections. Up to five. Each has a name and a
**retain** setting deciding which items survive when more arrive than the digest shows:

| Retain | Keeps |
|---|---|
| First 10 | The first items received in the window |
| Last 10 | The most recent items received |
| 10 Highest / 10 Lowest | Top or bottom by a data attribute (needs a sort key) |

The digest template receives the collected items grouped by category name, each with a `count` and
the retained `items`:

```json
{ "category_name": { "count": 25, "items": [ /* up to 10 events, per the retain setting */ ] } }
```

Reference `category_name.count` for the total and loop over `category_name.items` to render each event.

**Trigger Empty** sends the digest on schedule even when nothing was collected, which is what you
want when your own system supplies the data the digest renders. Off by default.

Digest settings are part of the preference page, so **publish the preferences** for changes to reach
recipients.

> Two different digest mechanisms share a name. This one is **preference-driven**: the recipient
> picks a frequency and Courier collects the topic's sends. The `batch` and `add-to-digest`
> **journey nodes** in [batching.md](./batching.md) aggregate inside a single journey run and are not
> recipient-selectable. Reach for this one when the user should control cadence.

## Embedded Preferences

For a native experience inside your own app instead of the hosted page, use the
[Courier React SDK](https://www.courier.com/docs/sdk-libraries/courier-react-web).

```bash
npm install @trycourier/courier-react     # React 18+; use @trycourier/courier-react-17 for React 17
```

**Preferences authenticate with a JWT, not a client key.** Generate it server-side with the
`read:preferences` and `write:preferences` scopes. Auth is shared across every Courier component, so
if you already signed in for Inbox or Toast you don't sign in again.

```tsx
import { CourierPreferences, useCourier } from "@trycourier/courier-react";

function PreferencePage({ userId, jwt }: { userId: string; jwt: string }) {
  const courier = useCourier();
  useEffect(() => {
    courier.shared.signIn({ userId, jwt });   // add tenantId to scope to a tenant
  }, [userId, jwt]);
  return <CourierPreferences />;
}
```

`<CourierPreferences>` renders topics, channel selection, and digest schedules, with native theming
and built-in dark mode.

| Prop | Purpose |
|---|---|
| `lightTheme` / `darkTheme` | Themes merged over the defaults, so override only what you need |
| `mode` | `"light"`, `"dark"`, or `"system"` (default) |
| `title` / `subtitle` | Override the component's text |
| `brandId` | Render using a specific brand's styling |
| `channelLabels` | Rename channels in the UI, e.g. `{ email: "E-mail" }` |
| `style` / `onError` | Container styles; error callback |

Theming is applied through props, not `styled-components`. `defaultPreferencesLightTheme`,
`defaultPreferencesDarkTheme`, and `mergePreferencesTheme(mode, overrideTheme)` are exported for
building on the defaults. Tenant scope is set on `signIn`, never per component.

> The `userId` you sign in with must match `to.user_id` on your sends, or enforcement won't line up.

### Headless hooks

For a fully custom UI, read and write through `useCourier().preferences`:

```tsx
const { preferences } = useCourier();

const prefs = await preferences.getUserPreferences();   // prefs.items holds the topics

await preferences.putUserPreferenceTopic({
  topicId: topic.topicId,
  status: topic.status === "OPTED_IN" ? "OPTED_OUT" : "OPTED_IN",
  hasCustomRouting: topic.hasCustomRouting,
  customRouting: topic.customRouting,
});
```

| Method | Returns |
|---|---|
| `getUserPreferences({ paginationCursor? })` | `CourierUserPreferences`; `.items` holds the topics |
| `getUserPreferenceTopic({ topicId })` | One topic's preference |
| `putUserPreferenceTopic({ topicId, status, hasCustomRouting, customRouting, digestSchedule? })` | Updates status, routing, or digest schedule |
| `getDigestSchedules({ topicId })` | The digest schedule options configured for a topic |
| `getNotificationCenterUrl({ clientKey })` | The hosted preference center URL |

Note these are camelCase (`topicId`, `hasCustomRouting`) while the server API is snake_case
(`topic_id`, `has_custom_routing`). Tenant scope comes from `signIn`; none of these take a
`tenantId` argument.

### Picking an approach

| Approach | Best for | Effort |
|---|---|---|
| Hosted page | No frontend work at all | Lowest |
| `<CourierPreferences>` (React) | A standard UI inside your web app, themed | Low |
| Headless hooks | Custom workflows and UX, complete control | Higher |
| `<courier-preferences>` web component | Any non-React web framework | Low |
| Mobile SDKs | Native preference screens on iOS, Android, React Native, Flutter | Low |
| User Preferences API | Backend-managed preferences, imports, sync | Varies |

**The mobile SDKs ship the same prebuilt UI natively**: `CourierPreferencesView` (SwiftUI) /
`CourierPreferences` (UIKit, Android, React Native, Flutter widget). Each supports **topic mode**
(toggle topics on/off) and **channels mode** (per-channel controls per topic), authenticates with
the same JWT scopes, and renders whatever is published in the Preferences Editor. See the
[iOS](https://www.courier.com/docs/sdk-libraries/ios#preferences),
[Android](https://www.courier.com/docs/sdk-libraries/android#preferences),
[React Native](https://www.courier.com/docs/sdk-libraries/react-native#preferences), and
[Flutter](https://www.courier.com/docs/sdk-libraries/flutter#preferences) docs.

See [inbox/auth.md](../inbox/auth.md) for JWT issuing and refresh.

## Auditing: Who Changed What, When

"The user says they unsubscribed but still gets email" is a preferences question before it is a
delivery question. The dashboard keeps a per-user preference log: [Users](https://app.courier.com/users)
→ select the user → preference log shows every opt-in, opt-out, and change with timestamps. The API
returns current state only, so the history lives in the dashboard.

While there, check the template is actually mapped to the topic the user opted out of. An unmapped
template ignores preferences entirely, which looks identical from the outside.

## Workspace Sections and Topics API

The topics above are **per-user** state. **Preference sections** are the workspace-level structure of
the preferences page, named groups that contain topics, shared across all users. Manage them with
`client.workspacePreferences.*` (REST: `/preferences/sections/{section_id}`).

| Operation | Node |
|---|---|
| Create a section | `client.workspacePreferences.create({ name, description })` |
| List sections | `client.workspacePreferences.list()` |
| Get a section | `client.workspacePreferences.retrieve(sectionId)` |
| Replace a section | `client.workspacePreferences.replace(sectionId, { name, description })` |
| Archive a section | `client.workspacePreferences.archive(sectionId)` |
| Publish preference changes | `client.workspacePreferences.publish()` |

Topics within a section live under `client.workspacePreferences.topics.*`:
`create(sectionId, {...})`, `list(sectionId)`, and `retrieve`/`replace`/`archive(topicId, {...})`.

A section carries `name` (required), an optional `description` (shown under the section on the hosted
page), and `has_custom_routing`. Confirm topic-body shapes against the installed types under
`resources/workspace-preferences/`.

## Related

- [Multi-Channel](./multi-channel.md) - channel routing, and how `custom_routing` narrows it
- [Brands](./brands.md) - what drives the hosted page's appearance
- [Tenants](./tenants.md) - tenant defaults that override workspace defaults
- [Batching](./batching.md) - digest and batch nodes inside journeys
- [Hosted Preference Center](https://www.courier.com/docs/platform/preferences/hosted-page) · [Preferences Editor](https://www.courier.com/docs/platform/preferences/preferences-editor) · [Get and Set User Preferences](https://www.courier.com/docs/platform/preferences/user-preference-management) · [Embedding](https://www.courier.com/docs/platform/preferences/embedding-preferences)
