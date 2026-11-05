# User Preferences

Subscription topics let users control which notifications they get and on which channels. Courier
checks them on every send, so the enforcement lives in Courier rather than in your code.

**Contents:** [Quick Reference](#quick-reference) · [The Model](#the-model) · [Setting It Up](#setting-it-up) · [User Preferences API](#user-preferences-api) · [Channel Selection](#channel-selection) · [Tenant Preferences (Multi-Tenant)](#tenant-preferences-multi-tenant) · [Hosted Preference Center](#hosted-preference-center) · [Digest Schedules](#digest-schedules) · [Embedded Preferences](#embedded-preferences) · [Tracking Preference Changes](#tracking-preference-changes) · [Workspace Sections and Topics API](#workspace-sections-and-topics-api) · [Related](#related)

## Quick Reference

### Rules
- **A user preference is an override on a topic's default**, not a standalone value. Topics are defined in the Preferences Editor with a default; a user falls back to it until they set their own choice
- **Two levels, easy to conflate.** A topic's `default_status` is `OPTED_IN`, `OPTED_OUT`, or `REQUIRED`. A user's own `status` is only `OPTED_IN` or `OPTED_OUT`. `REQUIRED` is a topic default that no user status overrides. Writing `OPTED_OUT` to a REQUIRED topic returns 400
- **Mapping a template to a topic is what makes enforcement happen.** An unmapped template sends regardless of preferences. Each template maps to exactly one topic
- **An opted-out send is skipped silently.** No error, no message. Check the logs, not the response
- **Channel selection is enabled per section**, not per topic
- **Editor changes are a draft until you publish.** Preview Page opens the draft; Publish makes it live
- **Preference and unsubscribe URLs need `to.user_id` on the send**, or they render empty
- **Preferences are keyed by `user_id`** (and by tenant when you pass `tenant_id`), never by email address. Two user IDs that share an email keep separate opt-outs, so opting one out doesn't stop sends to the other. Read a tenant-scoped opt-out with `tenant_id` on the read, or you get the user's workspace-level preference
- **Topic IDs are generated and can't be chosen.** Topic create has no `id` field, and `PUT` on an unknown topic ID returns `404`. Topics are per environment: **Migrate assets** on a template carries its topic with it, and topics you recreate by API get new IDs, so update templates that reference the old ones. A send whose template references a topic missing from that environment fails there

### Common Mistakes
- Using the wrong variable syntax for the editing context, which renders nothing at all (see [Linking to the page](#linking-to-the-page))
- Putting an unsubscribe link on a template mapped to a `REQUIRED` topic, where the opt-out silently does nothing
- Setting `custom_routing` without `has_custom_routing: true`, so the channel list is ignored
- Using bulk `PUT` when you meant `POST`, which resets every override you did not send

## The Model

### How preferences interact with routing

1. If the user opted out of the template's topic (and it isn't `REQUIRED`), the send is skipped silently
2. If the user set `has_custom_routing: true` with `custom_routing` channels, and the topic's section has channel selection enabled, those channels **replace** the template's `routing.channels`
3. Otherwise the template's routing applies unchanged

A template routed to `["email", "push", "sms"]`, for a user whose custom routing for that topic is `["email"]`, sends email only.

## Setting It Up

Everything is configured in the **Preferences Editor** ([Settings > Preferences](https://app.courier.com/settings/preferences)), top down:

**1. Page settings:** the [brand](./brands.md), heading, description, and the channel display names users see.

**2. Sections** group topics under a heading and are the unit that enables channel selection. Each has an auto-generated ID used in the API.

**3. Topics** each have a name, a section, and a default: `OPTED_IN` (On), `OPTED_OUT` (Off), or `REQUIRED` (users can't opt out, e.g. security alerts).

**4. Map templates to topics.** This is the step that makes enforcement happen. In Design Studio,
open the template's settings and choose a subscription topic. Through the API it is the
`subscription` field on the template, set to `{ "topic_id": "<TOPIC_ID>" }` or `null`:

```bash
curl -X POST https://api.courier.com/notifications \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"notification":{"name":"Order shipped","tags":[],"brand":null,"routing":null,
       "subscription":{"topic_id":"TOPIC_ID"},
       "content":{"version":"2022-01-01","elements":[]}}}'
```

To change an existing template's topic, `PUT /notifications/{id}` replaces the whole template, so
fetch it first, update `subscription`, and send the full payload back. See [templates.md](./templates.md).

**5. Publish.** Every change is a draft until you publish; users, including the embedded components, see the last published version. **Preview Page** opens the draft with a "Draft mode" banner.

## User Preferences API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/users/{user_id}/preferences` | List every topic with the user's status (their override, or the topic default) |
| `PUT` | `/users/{user_id}/preferences` | Replace the entire override set (bulk) |
| `POST` | `/users/{user_id}/preferences` | Create or update without touching others (bulk) |
| `GET` | `/users/{user_id}/preferences/{topic_id}` | Read one topic |
| `PUT` | `/users/{user_id}/preferences/{topic_id}` | Create or update one topic |
| `DELETE` | `/users/{user_id}/preferences/{topic_id}` | Reset one topic to its default |
| `GET` | `/preferences/logs` | List preference changes, newest first, for the whole environment or one `user_id`. See [Tracking preference changes](#tracking-preference-changes) |

Add a `tenant_id` query parameter to any of the `/users` calls to scope preferences to one tenant.

**Read:**
```typescript
const prefs = await client.users.preferences.retrieve("user-123");
// items[]: { topic_id, topic_name, status, default_status, has_custom_routing, custom_routing }
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

Python uses the same calls in snake_case: `client.users.preferences.retrieve(...)`, `update_or_create_topic(topic_id, user_id=..., topic={...})`.

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
| `custom_routing` | `email`, `sms`, `push`, `inbox`, `direct_message`, `webhook`. Applies only with `has_custom_routing: true` |
| `digest_schedule_id` | The user's digest schedule for the topic. Omit to keep, `null` to reset. See [digests.md](./digests.md#per-recipient-schedule) |

Reads also return `default_status` (the topic default, used when the user has no override), `topic_name`, `section_id`, and `section_name`.

## Channel Selection

Enabling channel selection on a **section** lets users pick channels for the topics inside it. Their
choices land in `custom_routing`, which only populates for sections where it's enabled. Users see the
channel display names configured in page settings, not the raw enum values.

> Template [send conditions](https://www.courier.com/docs/design/templates/template-settings)
> do not override a user's `custom_routing`. To drop a channel when required data is missing, use
> variable guardrails instead.

## Tenant Preferences (Multi-Tenant)

In a multi-tenant workspace a user can hold different preferences per tenant: alerts on for
`prod-project`, off for `stage-project`. At send time Courier resolves each topic through these
layers, top to bottom. A layer overrides the ones above it for the topics it sets:

1. Workspace-level topic defaults (the Preferences Editor)
2. The tenant's defaults (`default_preferences`, written with `tenants.preferences.items`). They inherit as one list, not topic by topic, see [tenants.md](./tenants.md#hierarchy-and-merging)
3. The user's global preferences
4. The user's per-tenant overrides (highest priority)

Read or write the per-tenant layer by adding `tenant_id` as a query parameter on any
[User Preferences API](#user-preferences-api) call. The embedded UI scopes the same way, via
`tenantId` on `signIn`.

## Hosted Preference Center

A Courier-hosted page where users manage their own preferences, with no frontend to build. Its topics, sections, and look come from the Preferences Editor and the [brand](./brands.md).

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

Put it in a template, or once in the brand footer to cover every message. Preview emails render a sample URL, not a live one.

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

A topic can deliver as a digest on a schedule the recipient picks in the hosted or embedded page, or that your backend sets with `digest_schedule_id`. Setup, the send payload, the digest template, and release are in **[digests.md](./digests.md)**.

## Embedded Preferences

For a native page inside your own app, use `<CourierPreferences>` from `@trycourier/courier-react` (React 17: `@trycourier/courier-react-17`). Sign in with a JWT carrying `read:preferences write:preferences` ([auth.md](../inbox/auth.md)); one sign-in covers inbox, toast, and preferences.

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

Props: `lightTheme` / `darkTheme` (merged over the defaults), `mode` (`"system"` by default), `title` / `subtitle`, `brandId`, `channelLabels` (e.g. `{ email: "E-mail" }`), `style`, `onError`. Theming goes through props, not `styled-components`. Tenant scope is set on `signIn`, never per component.

> The `userId` you sign in with must match `to.user_id` on your sends, or enforcement won't line up.

### Headless hooks

For a fully custom UI, read and write through `useCourier().preferences`:

| Method | Returns |
|---|---|
| `getUserPreferences({ paginationCursor? })` | `CourierUserPreferences`; `.items` holds the topics |
| `getUserPreferenceTopic({ topicId })` | One topic's preference |
| `putUserPreferenceTopic({ topicId, status, hasCustomRouting, customRouting, digestSchedule? })` | Updates status, routing, or digest schedule |
| `getDigestSchedules({ topicId })` | The digest schedule options configured for a topic |

Note these are camelCase (`topicId`, `hasCustomRouting`) while the server API is snake_case
(`topic_id`, `has_custom_routing`). Tenant scope comes from `signIn`; none of these take a
`tenantId` argument.

### Other surfaces

Non-React web apps use the `<courier-preferences>` web component. The mobile SDKs ship the same UI natively (`CourierPreferencesView` in SwiftUI; `CourierPreferences` in UIKit, Android, React Native, and Flutter) in topic or channels mode, with the same JWT scopes, rendering what is published. See each SDK's docs, e.g. [iOS](https://www.courier.com/docs/sdk-libraries/ios#preferences).

<a id="tracking-preference-changes"></a>

## Tracking Preference Changes

Courier records every time a user opts in, opts out, or changes a topic's channels, wherever it
happened: the hosted page, an unsubscribe link, the embedded preference center, or the API. See them
in the dashboard ([Users](https://app.courier.com/users) → select the user → preference log), list
them with `GET /preferences/logs`, or get each one pushed to you as a `preferences:user:updated`
[webhook](./webhooks.md#preference-events).

"The user says they unsubscribed but still gets email" is a preferences question before it is a
delivery question. Look up their changes, then check the template is mapped to the topic they opted
out of. An unmapped template ignores preferences entirely.

### Listing changes

```typescript
const changes = await client.workspacePreferences.listLogs({ user_id: "user-123" });
// changes.items: newest first. changes.paging: { more, cursor? }
```
```python
changes = client.workspace_preferences.list_logs(user_id="user-123")
```
```bash
courier workspace-preferences list-logs --user-id "user-123"
```

| Param | Notes |
|---|---|
| `user_id` | One user's changes. Omit for every change in the environment |
| `tenant_id` | One tenant context. Used together with `user_id` |
| `since` | Changes at or after this time. ISO 8601 date or date-time; a bare date is the start of that day in UTC |
| `limit` | 1 to 100, default 25 |
| `cursor` | `paging.cursor` from the previous page, while `paging.more` is `true` |

Each entry is one change to one topic, with `previous` holding the value it replaced. The fields
match the [webhook payload](./webhooks.md#preference-events), including the `id`. The endpoint allows
one request every two seconds, so page through it one request at a time. New changes appear within
about a minute.

### Mirroring preferences in another system

To keep a copy of users' choices in your CRM or database:

1. Load each user's current preferences with `GET /users/{user_id}/preferences`.
2. Apply each `preferences:user:updated` event as it arrives.
3. If your endpoint was down, list changes with `since` set a few minutes before the last change you applied, and skip any `id` you already have.

Resetting a topic to its default (`DELETE /users/{user_id}/preferences/{topic_id}`, or the topics a
bulk replace lists in `deleted`) removes the user's override rather than recording a change, so
it has no entry or event. Update your copy when your code makes those calls.

Your team's changes to the preference *configuration* (a topic created, its channels or default
changed) are in the workspace [audit trail](https://www.courier.com/docs/workspaces/audit-trail).

## Workspace Sections and Topics API

Sections and topics are the workspace-level structure of the preferences page, shared by all users. Manage sections with `client.workspacePreferences.*` (REST: `/preferences/sections/{section_id}`): `create({ name, description })`, `list()`, `retrieve(id)`, `replace(id, { name, description })`, `archive(id)`, and `publish()` to make preference changes live. Topics live under `client.workspacePreferences.topics.*`: `create(sectionId, {...})`, `list(sectionId)`, and `retrieve` / `replace` / `archive(topicId, {...})`.

A section carries `name` (required), an optional `description` (shown under the section on the hosted
page), and `has_custom_routing`.

A topic carries `name` and `default_status` (both required), `description`, `routing_options` (default
channels), `allowed_preferences` (`snooze`, `channel_preferences`), `include_unsubscribe_header`,
`topic_data` (arbitrary metadata), and `digest` (see [digests.md](./digests.md#configure-a-topics-digest)).
`replace` is a full replacement: optional fields you omit are cleared, except `digest`, which is left as is.

## Related

- [Multi-Channel](./multi-channel.md) - channel routing, and how `custom_routing` replaces it when channel selection is on
- [Brands](./brands.md) - what drives the hosted page's appearance
- [Tenants](./tenants.md) - tenant defaults that override workspace defaults
- [Digests](./digests.md) - digest schedules, the digest template, and the Send to Digest node
- [Webhooks](./webhooks.md#preference-events) - the `preferences:user:updated` event, signatures, retries
- [Hosted Preference Center](https://www.courier.com/docs/guides/build-a-preference-center#hosted-page) · [Preferences Editor](https://www.courier.com/docs/recipients/preferences/preferences-editor) · [Get and Set User Preferences](https://www.courier.com/docs/recipients/preferences/api) · [Track Preference Changes](https://www.courier.com/docs/recipients/preferences/api#track-preference-changes) · [Embedding](https://www.courier.com/docs/guides/build-a-preference-center#embedded-component)
