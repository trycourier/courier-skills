# SDK Method Reference

Method-name lookup for the Node (`@trycourier/courier`) and Python (`trycourier`) SDKs.
Both follow the same structure, Node is camelCase, Python is snake_case.

**This is a snapshot of Node v7.25.2 / Python v7.26.2.** The authoritative source is the installed package's
own type definitions, `node_modules/@trycourier/courier/resources/*.d.ts` or the Python
package stubs. When they disagree with this file, they win. See
[Verifying Against Live Sources](../SKILL.md#verifying-against-live-sources).

**Staying current.** The installed version is the ground truth. Check it
(`npm ls @trycourier/courier`, `pip show trycourier`) and verify shapes against its types.
If it trails the latest release, recommend upgrading (`npm install @trycourier/courier@latest`);
a major-version jump (6 → 7) is a breaking migration that reshaped `send`, `messages`,
`journeys`, and `digests`, so flag it as one rather than assuming a silent bump.

Minor versions have also moved whole namespaces. `client.bulk` was absent from Node 7.21.0–7.25.0
and Python ≤7.26.0, and returned in Node **7.25.1** / Python **7.26.1**. If a namespace in this
table is `undefined` on the installed client, check the version before concluding the method
doesn't exist.

## Method lookup

| Operation | Node | Python |
|-----------|------|--------|
| Send a message | `client.send.message({ message })` | `client.send.message(message=...)` |
| Create a template | `client.notifications.create({ notification, state })` → returns `{ id, name, content, … }` at top level | `client.notifications.create(notification=..., state=...)` → `response.id` |
| Publish a template | `client.notifications.publish(templateId)` | `client.notifications.publish(template_id)` |
| Retrieve a message | `client.messages.retrieve(id)` | `client.messages.retrieve(id)` |
| List messages | `client.messages.list({ ... })` | `client.messages.list(...)` |
| Subscribe a user to a list (additive) | `client.lists.subscriptions.subscribeUser(userId, { list_id })` | `client.lists.subscriptions.subscribe_user(user_id, list_id=...)` |
| Replace a list's subscribers | `client.lists.subscriptions.subscribe(listId, { recipients })` | `client.lists.subscriptions.subscribe(list_id, recipients=...)` |
| Create/replace a tenant | `client.tenants.update(tenantId, body)` | `client.tenants.update(tenant_id, ...)` |
| Add a user to a tenant | `client.users.tenants.addSingle(tenantId, { user_id })` | `client.users.tenants.add_single(tenant_id, user_id=...)` |
| Send to many recipients | `client.send.message({ message: { to: { list_id } } })`, or `{ audience_id }` | `client.send.message(message={"to": {"list_id": ...}})` |
| Create a bulk job | `client.bulk.createJob({ message: { event } })` → `{ jobId }` (`event` required) | `client.bulk.create_job(message={"event": ...})` → `.job_id` |
| Ingest users into a bulk job | `client.bulk.addUsers(jobId, { users })` | `client.bulk.add_users(job_id, users=[...])` |
| Run a bulk job | `client.bulk.runJob(jobId)` | `client.bulk.run_job(job_id)` |
| Bulk job status and counts | `client.bulk.retrieveJob(jobId)` → `{ job }` | `client.bulk.retrieve_job(job_id)` |
| Per-recipient bulk outcomes | `client.bulk.listUsers(jobId)` → `{ items, paging }` | `client.bulk.list_users(job_id)` |
| Archive a sent message | `client.requests.archive(requestId)` | `client.requests.archive(request_id)` |
| Resend a message | `client.messages.resend(messageId)` | `client.messages.resend(message_id)` |
| Rendered content of a sent message | `client.messages.content(messageId)` | `client.messages.content(message_id)` |
| Delivery event history | `client.messages.history(messageId)` | `client.messages.history(message_id)` |
| Duplicate a template | `client.notifications.duplicate(templateId)` | `client.notifications.duplicate(template_id)` |
| Release a digest early | `client.digests.schedules.release(scheduleId)` | `client.digests.schedules.release(schedule_id)` |
| Inspect digest accumulation | `client.digests.schedules.listInstances(scheduleId)` | `client.digests.schedules.list_instances(schedule_id)` |
| Create/update a profile (merge) | `client.profiles.create(userId, { profile })` | `client.profiles.create(user_id, profile=...)` |
| Get a user's preferences | `client.users.preferences.retrieve(userId)` | `client.users.preferences.retrieve(user_id)` |
| Update a user's preference for a topic | `client.users.preferences.updateOrCreateTopic(topicId, { user_id, topic: { status, ... } })` | `client.users.preferences.update_or_create_topic(topic_id, user_id=..., topic=...)` |
| Register a user's device token | `client.users.tokens.addSingle(token, { user_id, provider_key, device })` | `client.users.tokens.add_single(token, user_id=..., provider_key=..., device=...)` |
| Create a journey | `client.journeys.create({ name, nodes, enabled })` | `client.journeys.create(name=..., nodes=..., enabled=...)` |
| Replace a journey (draft) | `client.journeys.replace(id, { name, nodes, enabled })` | `client.journeys.replace(id, name=..., nodes=..., enabled=...)` |
| Publish a journey | `client.journeys.publish(id)` | `client.journeys.publish(id)` |
| Invoke a journey (start a run) | `client.journeys.invoke(id, { user_id, data, profile })` → `{ runId }` | `client.journeys.invoke(template_id=id, user_id=..., data=..., profile=...)` → `.run_id` |
| Cancel a journey run | `client.journeys.cancel({ cancelation_token })`, or `{ run_id }`, exactly one | `client.journeys.cancel(cancelation_token=...)` |
| Create a journey-scoped template | `client.journeys.templates.create(journeyId, { ... })` | `client.journeys.templates.create(journey_id, ...)` |
| Publish a journey-scoped template | `client.journeys.templates.publish(notificationId, { templateId: journeyId })` | `client.journeys.templates.publish(journey_id, template_id)` |
| Create a routing strategy | `client.routingStrategies.create({ name, routing, channels?, providers? })` → returns `{ id: "rs_...", ... }` | `client.routing_strategies.create(name=..., routing=..., ...)` |
| Replace a routing strategy (full PUT) | `client.routingStrategies.replace(id, { name, routing, ... })` | `client.routing_strategies.replace(id, name=..., routing=..., ...)` |
| Configure a provider | `client.providers.create({ provider, settings, title?, alias? })` | `client.providers.create(provider=..., settings=..., ...)` |
| List provider catalog (required `settings` schema) | `client.providers.catalog.list({ keys?, name?, channel? })` | `client.providers.catalog.list(keys=..., channel=...)` |
| Cancel a message | `client.messages.cancel(messageId)` | `client.messages.cancel(message_id)` |
| Retrieve a template | `client.notifications.retrieve(templateId)` | `client.notifications.retrieve(template_id)` |
| List templates | `client.notifications.list()` | `client.notifications.list()` |
| Replace a template (full PUT) | `client.notifications.replace(templateId, { notification, state })` | `client.notifications.replace(template_id, notification=..., state=...)` |
| Archive a template | `client.notifications.archive(templateId)` | `client.notifications.archive(template_id)` |
| Get published template content | `client.notifications.retrieveContent(templateId)` | `client.notifications.retrieve_content(template_id)` |

> The table above covers the most common operations. [journeys.md](./guides/journeys.md), [templates.md](./guides/templates.md), [routing-strategies.md](./guides/routing-strategies.md), and [providers.md](./guides/providers.md) each contain their own complete SDK shape tables for CRUD on their respective resources (including `list`, `retrieve`, `replace`, `archive`). **Journeys are Courier's orchestration primitive. Use them for every multi-step flow** (delays, branches, batching, digests, throttling, A/B experiments). See [Journeys](./guides/journeys.md).
