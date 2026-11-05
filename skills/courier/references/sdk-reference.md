# SDK Method Reference

Method-name lookup for the Node (`@trycourier/courier`) and Python (`trycourier`) SDKs.
Both follow the same structure, Node is camelCase, Python is snake_case.

**This lists method names, not signatures.** The authoritative source is the installed package's
own type definitions, `node_modules/@trycourier/courier/resources/*.d.ts` or the Python
package stubs. When they disagree with this file, they win. See
[Verifying Against Live Sources](../SKILL.md#verifying-against-live-sources).

**Staying current.** Check the installed version (`npm ls @trycourier/courier`, `pip show trycourier`) and verify shapes against its types. Minor versions have moved whole namespaces, so a namespace that is `undefined` on the client usually means upgrade (`npm install @trycourier/courier@latest`), not a missing method. Flag a major-version jump as a breaking migration and check the release notes.

## Namespaces

**The 23 namespaces are the complete SDK surface.** If an operation isn't here, it isn't in the SDK; use MCP, the CLI, or REST:

```
audiences  auditEvents  auth      automations  brands
broadcasts  bulk        digests   inbound      journeys
lists      messages     notifications  previews  profiles
providers  requests     routingStrategies  send  tenants
translations  users     workspacePreferences
```

Sub-namespaces: `automations.invoke`, `automations.runs`, `digests.schedules`, `journeys.runs`, `journeys.templates`, `lists.subscriptions`, `notifications.checks`, `notifications.previews`, `notifications.previews.runs`, `profiles.lists`, `providers.catalog`, `tenants.preferences`, `tenants.preferences.items`, `tenants.templates`, `tenants.templates.versions`, `users.preferences`, `users.tenants`, `users.tokens`, `workspacePreferences.topics`.

`auditEvents` and `inbound` (`inbound.trackEvent`) have no dedicated guide; use MCP or the CLI. `requests.archive` is in [inbox.md](./channels/inbox.md).

## Method lookup

Python uses the same method in snake_case (`listVersions` → `list_versions`, `routingStrategies` → `routing_strategies`). The positional argument stays positional, and every key of the Node params object becomes a snake_case keyword argument, headers included (`"Idempotency-Key"` → `idempotency_key=`, `{ templateId }` → `template_id=`). Response fields are snake_case attributes (`.request_id`, `.job_id`, `.run_id`).

| Operation | Node |
|-----------|------|
| Send a message | `client.send.message({ message })` |
| Create a template | `client.notifications.create({ notification, state })` → returns `{ id, name, content, … }` at top level |
| Publish a template (or roll back to a version) | `client.notifications.publish(templateId)` · rollback: `client.notifications.publish(templateId, { version: "v001" })` |
| List a template's versions | `client.notifications.listVersions(templateId)`, paginated, `{ cursor, limit }` (max 10/page) |
| Retrieve a message | `client.messages.retrieve(id)` |
| List messages | `client.messages.list({ ... })` |
| Subscribe a user to a list (additive) | `client.lists.subscriptions.subscribeUser(userId, { list_id })` |
| Replace a list's subscribers | `client.lists.subscriptions.subscribe(listId, { recipients })` |
| Create/replace a tenant | `client.tenants.update(tenantId, body)` |
| Add a user to a tenant | `client.users.tenants.addSingle(tenantId, { user_id })` |
| Create a bulk job | `client.bulk.createJob({ message: { event } })` → `{ jobId }` (`event` required) |
| Ingest users into a bulk job | `client.bulk.addUsers(jobId, { users })` |
| Run a bulk job | `client.bulk.runJob(jobId)` |
| Bulk job status and counts | `client.bulk.retrieveJob(jobId)` → `{ job }` |
| Per-recipient bulk outcomes | `client.bulk.listUsers(jobId)` → `{ items, paging }` |
| Archive a sent message | `client.requests.archive(requestId)` |
| Resend a message (creates a **new** message with a new message ID; limited to 1 request per 2 seconds per message) | `client.messages.resend(messageId)` |
| Rendered content of a sent message | `client.messages.content(messageId)` |
| Delivery event history | `client.messages.history(messageId)` |
| List preference changes | `client.workspacePreferences.listLogs({ user_id, since, limit, cursor })` → `{ items, paging }` |
| Configure a topic's digest | `client.workspacePreferences.topics.create(sectionId, { name, default_status, digest })` · also `replace(topicId, { section_id, ... })` |
| Turn off a topic's digest | `client.workspacePreferences.topics.deleteDigest(topicId, { section_id })` |
| Release one recipient's digest | `client.workspacePreferences.topics.releaseDigest(topicId, { section_id, user_id })` |
| Release a schedule's digests early | `client.digests.schedules.release(scheduleId)` |
| Inspect digest accumulation | `client.digests.schedules.listInstances(scheduleId)` |
| Write a profile (POST, deep-merge, the everyday write) | `client.profiles.create(userId, { profile })` |
| Change profile fields (PATCH, JSON Patch RFC 6902) | `client.profiles.update(userId, { patch: [...] })` |
| Overwrite a whole profile (PUT; omitted fields are removed) | `client.profiles.replace(userId, { profile })` |
| Get a user's preferences | `client.users.preferences.retrieve(userId)` |
| Update a user's preference for a topic (status, channels, digest schedule) | `client.users.preferences.updateOrCreateTopic(topicId, { user_id, topic: { status, digest_schedule_id?, ... } })` |
| Register a user's device token | `client.users.tokens.addSingle(token, { user_id, provider_key, device })` |
| Create a journey | `client.journeys.create({ name, nodes, enabled, cancelation_token? })` |
| Replace a journey (draft) | `client.journeys.replace(id, { name, nodes, enabled })` |
| Publish a journey | `client.journeys.publish(id)` |
| Invoke a journey (start a run) | `client.journeys.invoke(id, { user_id, data, profile })` → `{ runId }` |
| Cancel a journey run | `client.journeys.cancel({ cancelation_token })`, or `{ run_id }`, exactly one |
| List journey runs | `client.journeys.runs.list({ template_id?, status? })` |
| One journey run, and its steps | `client.journeys.runs.retrieve(runId)` · `client.journeys.runs.listSteps(runId)` |
| Create a journey-scoped template | `client.journeys.templates.create(journeyId, { ... })` |
| Publish a journey-scoped template | `client.journeys.templates.publish(notificationId, { templateId: journeyId })` |
| Create and send a broadcast | `client.broadcasts.create({ name, channel })`, `putContent(id, { content })`, then `send(id, { recipient_type, recipient_id })` or `schedule(id, { recipient_type, recipient_id, scheduled_to })` |
| Create a routing strategy | `client.routingStrategies.create({ name, routing, channels?, providers? })` → returns `{ id: "rs_...", ... }` |
| Replace a routing strategy (full PUT) | `client.routingStrategies.replace(id, { name, routing, ... })` |
| Configure a provider | `client.providers.create({ provider, settings, title?, alias? })` |
| Change part of a provider config (PATCH, JSON Patch operations) | `client.providers.patch(id, { patch: [{ op, path, value? }] })` |
| Replace a provider config (full PUT) | `client.providers.update(id, { provider, settings, ... })` |
| List provider catalog (required `settings` schema) | `client.providers.catalog.list({ keys?, name?, channel? })` |
| Cancel a message (only while it's still in flight; an unknown ID returns `404`) | `client.messages.cancel(messageId)` |
| Retrieve a template | `client.notifications.retrieve(templateId)` |
| List templates | `client.notifications.list()` |
| Replace a template (full PUT) | `client.notifications.replace(templateId, { notification, state })` |
| Archive a template | `client.notifications.archive(templateId)` |
| Get template content (published, draft, or a version) | `client.notifications.retrieveContent(templateId, { version: "draft" \| "published" \| "v001" })`; omit for published |
| Write one locale's translations (merges) | `client.notifications.putLocale(localeId, { id: templateId, elements: [{ id, ...fields }] })` |
| Workspace `.po` strings for `{{t}}` (read) | `client.translations.retrieve(locale, { domain: "default" })`. Upload with raw HTTP `text/plain`, see [localization.md](./guides/localization.md#workspace-translation-strings) |
| List preview device sets / devices | `client.previews.listDeviceSets()` · `client.previews.listDevices()` |
| Save a preview device set | `client.previews.createDeviceSet({ name, device_ids })` |
| Start a Device Preview run | `client.notifications.previews.runs.create(templateId, { device_set_id, data, "Idempotency-Key": key })` |
| Read a preview run (poll) | `client.notifications.previews.runs.retrieve(runId, { id: templateId })` |
| Template delivery metrics (time series) | `client.notifications.getMetrics(templateId, { lookback: "P7D", granularity: "DAY" })` |

> The table covers the most common operations. [journeys.md](./guides/journeys.md), [templates.md](./guides/templates.md), [routing-strategies.md](./guides/routing-strategies.md), [providers.md](./guides/providers.md), [audiences.md](./guides/audiences.md), [brands.md](./guides/brands.md), [tenants.md](./guides/tenants.md), [preferences.md](./guides/preferences.md), [push.md](./channels/push.md) (device tokens), and [inbox/auth.md](./inbox/auth.md) each have the full SDK table for their resource.
