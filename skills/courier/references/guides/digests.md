# Digests

A digest collects the notifications sent for one subscription topic and delivers them together on a
schedule the recipient picks. Instead of five emails about five comments, a recipient on Daily gets
one email at 9:00 listing all five. The topic owns the digest: the digest template, the schedules,
and the categories. A journey feeds it.

**Contents:** [Quick Reference](#quick-reference) · [How it works](#how-it-works) · [Configure a topic's digest](#configure-a-topics-digest) · [Feed it from a journey](#feed-it-from-a-journey) · [What the template receives](#what-the-template-receives) · [Per-recipient schedule](#per-recipient-schedule) · [Inspect and release](#inspect-and-release) · [Troubleshooting](#troubleshooting) · [Related](#related)

## Quick Reference

### Rules

- **Feed the digest from a journey.** Link the Send node's template to the topic and invoke the journey once per event. Each recipient's schedule decides whether the notification is held or sent now. Use the Send to Digest node only for a step that shouldn't send a notification of its own.
- **A send is only held if it carries the topic**, through its template's `subscription.topic_id` (journey or workspace template) or, on a direct `/send`, `message.preferences.subscription_topic_id`.
- **When the topic has categories, the data needs a top-level key named exactly like one**, including case, with a value other than `null`, `false`, `0` or `""`. A send that matches no category is delivered immediately as a normal message (a Send to Digest event is dropped instead), with no error. The exception is a category named `digest`, which catches everything unmatched. A topic with no categories collects everything under `digest`.
- **One event is one item.** Never send `count` or `items` yourself. Courier builds them at release.
- **Use two kinds of template.** The Send node's template is linked to the topic, and Instant recipients get it as-is. The digest template renders the collected list: build it as a workspace template (the topic's **Template** picker lists only workspace templates, not journey ones), select it on the topic, and **don't link it to the topic**, or it gets collected like any other send and the digest contains a copy of itself. Removing the digest template turns digesting off.
- **Include an Instant schedule** so recipients can opt out, but don't make it the default: a recipient who never chose a schedule falls back to the default (or the first schedule), and Instant never holds anything.
- **`schedules` needs at least one entry.** `schedules: []` returns 400. Turn a digest off with `digest: null` or `deleteDigest`.
- **Events past a category's `limit` are discarded** at release, not carried into the next digest.
- **Never link a transactional template** (OTP, password reset, receipts) to a digest topic. A recipient on Daily would get their code tomorrow.
- Held sends show status `DIGESTED` in message logs, and the release is a new message. An opted-out recipient's sends also show `DIGESTED`: the opt-out applies at release, which is dropped as `UNSUBSCRIBED`.

### Common Mistakes

- Sending `{ "author_name": "..." }` when the category is `comments`. It delivers individually. Send `{ "comments": { "author_name": "..." } }`
- Reading a field without the category key. Each item is one send's whole `data`, so the author is `comments.author_name` on the item
- Writing the total without the root that matches the template's scope (see [What the template receives](#what-the-template-receives)). The wrong form renders an empty string
- Looping with `{{#each}}` in a text block. It renders, but the designer then shows broken variable chips. Use a `list` element with `loop`
- Testing with Instant as the topic's default. Every new test user delivers immediately, and nothing is ever `DIGESTED`
- Linking a digest template with no content for the channel. The release still sends, with subject `(no subject)` and an empty body
- Putting the digest body in a channel override (`channels.email.override.html`). Overrides on held sends are dropped at release
- Naming the event's actor `user_id` in a journey invoke's `data`. A value other than the recipient fails the invoke with 400, see [journeys.md](./journeys.md#step-5-invoke). Use `author_id` or similar
- Relying on send order. Without a `sort_key`, items follow the order Courier collected them, and events sent close together, or through a journey and a direct send, can swap. Send a numeric timestamp and set it as the category's `sort_key`
- Storing a "digest frequency" field on the profile and branching in app code. Recipients choose a schedule on the topic
- Using a digest for a burst-of-events rollup inside a journey. That is the journey `batch` node, a different mechanism, see [batching.md](./batching.md)

## How it works

Configure the topic's digest (a separate, unlinked digest template, at least one schedule, optional
categories). Link the journey's Send node template to the topic, then invoke the journey once per
event. A recipient on **Instant** gets each notification now with the Send node's template. On any
other schedule it's held as `DIGESTED`, and at release Courier renders the digest template once with
everything held for that recipient. The release uses the digest template the topic had when that
recipient's first held event arrived. Digests are kept per recipient and per tenant.

## Configure a topic's digest

In the app: **Platform → Preferences**, open the topic, turn on **Digest Schedules**, then click
**Add Digest Schedules** (**Edit Digest Schedules** once the topic has a digest). Pick the digest
template under **Template**. The editor allows up to four schedules and five categories and keeps 10
items per category. The editor's **Save** writes the digest, so collection starts then; **Publish**
puts the schedule choices on the hosted preference page.

Through the API, the whole configuration is the `digest` object on topic create and replace, with no
cap on schedules or categories:

```typescript
const topic = await client.workspacePreferences.topics.create(sectionId, {
  name: "Activity",
  default_status: "OPTED_IN",
  routing_options: ["email"],
  digest: {
    template_id: "nt_01kmrbwx4c8p2n6v0d3j7t9qf", // renders the list; not linked to the topic
    schedules: [
      { frequency: "daily", time: "09:00", timezone: "America/New_York", is_default: true },
      { frequency: "instant" },
    ],
    categories: [{ category_key: "comments", retain: "FIRST", limit: 10 }],
    trigger_empty: false,
  },
});

const scheduleIds = topic.digest?.schedules.map((s) => s.schedule_id);
```

Python takes the same fields as keyword arguments: `client.workspace_preferences.topics.create(section_id, name=..., default_status=..., routing_options=[...], digest={...})`, and the ids are at `topic.id` and `topic.digest.schedules[].schedule_id`.

| Field | Notes |
|---|---|
| `template_id` | Required. The template that renders the digest, separate from the templates you send. |
| `schedules[].frequency` | `instant`, `daily`, `weekdays`, `weekly`, `custom_days`, `monthly`. |
| `schedules[].time` | `HH:MM`, 24-hour. Required for everything except `instant`. |
| `schedules[].timezone` | IANA name, DST aware. Absent means UTC. The schedule's own zone, not each recipient's. |
| `day_of_week` / `days_of_week` / `day_of_month` | Required for `weekly` / `custom_days` / `monthly`. A missing one returns 400. |
| `schedules[].is_default` | The schedule for recipients who have not chosen. Set it explicitly. |
| `schedules[].schedule_id` | Send it to keep an existing schedule. The array is a full replacement, so a schedule you leave out is deleted. A kept schedule is stored exactly as sent: leave out `timezone` and it reads as UTC, leave out `is_default` and it stops being the default. |
| `categories[]` | `category_key`, `retain` (`FIRST`, `LAST`, `HIGHEST`, `LOWEST`, `NONE`), `limit` (1 to 100, default 10), and `sort_key`. Omit categories to collect everything under one key, `digest`. |
| `categories[].sort_key` | A top-level field of the send's `data`, read as a number. Required for `HIGHEST`/`LOWEST`, and it orders `FIRST`/`LAST` too when set. A send whose value is missing, `null`, or not a number sorts by its collection time, which ranks above any small number. An empty string counts as 0. |
| `trigger_empty` | Send on schedule even with nothing collected. Off by default. |

`replace` is a full replacement of the topic, but omitting `digest` leaves the digest untouched, and
omitting `schedules` inside `digest` keeps the stored schedules. To turn a digest off, send
`digest: null` or call `client.workspacePreferences.topics.deleteDigest(topicId, { section_id })`.
A stored schedule the `frequency` values can't express comes back without `frequency` and never fires.

CLI: `courier workspace-preferences:topics create`, `replace`, and `delete-digest`.

### Schedule ids

Schedule ids are returned on the topic, under `digest.schedules[].schedule_id`, from create,
replace, and `client.workspacePreferences.topics.retrieve(topicId, { section_id })`. Newer ids look
like `sch_01m26nhsf7fzxr5kngwf8p0b2c`. Older ones look like `sch/{uuid}` and need the slash written
as `%2F` in a raw URL. The SDKs escape both. An unknown or deleted id returns 404 from
`listInstances` and `release`.

## Feed it from a journey

Link the Send node's template to the topic. In the app: select the Send node, click **Edit** under
**Message**, open the template's settings (gear icon), and choose the topic under **Subscription
Topic**. Then publish the template and the journey. Over the API, set `subscription` when you create
the journey's template:

```typescript
const template = await client.journeys.templates.create(journeyId, {
  channel: "email",
  notification: {
    name: "Comment added",
    tags: [],
    brand: null,
    subscription: { topic_id: topicId },
    content: {
      version: "2022-01-01",
      elements: [{ type: "channel", channel: "email", elements: [{ type: "text", content: "New comment" }] }],
    },
  },
});
```

For an existing journey template, send the same `notification` to
`client.journeys.templates.replace(notificationId, { templateId: journeyId, notification })`. Publish
with `client.journeys.templates.publish(notificationId, { templateId: journeyId })`, then
`client.journeys.publish(journeyId)`. A run sends the published version, never an unpublished draft.

Invoke once per event, with the event under the category key:

```typescript
await client.journeys.invoke(journeyId, {
  user_id: "user-123",
  data: { comments: { author_name: "Priya Shah", comment_text: "Can we ship Friday?" } },
});
```

- For a recipient on a digest schedule, every topic-linked Send node that runs adds one item, so two
  linked Send nodes in one run add two. For a recipient on Instant, each is delivered instead.
- An event with two matching keys (`comments` and `mentions`) is filed in both categories. Include
  only the keys the event belongs in.
- Send nodes, Send to Digest nodes, and direct sends can feed the same topic and recipient. They
  land in one digest.

### Without a journey

A backend that sends directly gets the same behavior from `POST /send` with a topic-linked workspace
template (`subscription: { topic_id }`, see [preferences.md](./preferences.md#setting-it-up)):

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbtm6q9x3c7v1d5w2n8hj",
    data: { comments: { author_name: "Priya Shah", comment_text: "Can we ship Friday?" } },
  },
});
```

### Send to Digest node

```json
{ "type": "add-to-digest", "subscription_topic_id": "<topic-id>" }
```

Use it for a step that adds to the digest without sending a notification of its own. It collects the
run's whole `data` as the item. An Instant recipient gets each event right away as a one-item
digest, rendered with the digest template. A run whose data matches no category is dropped, unless
the topic has a `digest` category. If the topic has no digest template when the first event arrives,
the run is marked `ERROR` and stops.

## What the template receives

At release, the digest template receives one object per category with the total `count` and the
retained `items`. Each item is the full `data` object from one send, so it repeats the category key.
`count` is every event in the window and can exceed the number of items. Without a `sort_key`, items
are in the order Courier collected them (`FIRST` oldest first, `LAST` and `NONE` newest first),
which isn't always send order.

Loop with a `list` element whose `loop` is the category's items. The loop path always starts with
`data.`, and each item is `$.item`:

```json
{
  "type": "list",
  "list_type": "unordered",
  "loop": "data.comments.items",
  "elements": [
    { "type": "list-item", "elements": [
      { "type": "string", "content": "{{$.item.comments.author_name}}: {{$.item.comments.comment_text}}" }
    ] }
  ]
}
```

The total, outside the loop, depends on the template's scope:

| Template | Total |
|---|---|
| Default scope, including templates created through the API | `{{comments.count}}` |
| `scope: "strict"` (Design Studio always saves this) | `{{data.comments.count}}` |

With no categories, the key is `digest` and each item is the send's `data` unwrapped.

A release also carries `digest_schedule` beside the categories: `recurrence`, `timezone`,
`period_start` (the recipient's first held event), and `period_end` (the release), read with the same
root as the total. It's left out when the schedule has since been deleted, and a category named
`digest_schedule` takes the key instead.

A value that is the same on every event (a build number) still arrives per item. Read it inside the
loop, not positionally from `items.[0]`, which vanishes silently when the first item lacks it.

## Per-recipient schedule

Recipients choose a schedule in the hosted or embedded preference page. To set it from your backend,
pass `digest_schedule_id` on the user's topic preference:

```typescript
await client.users.preferences.updateOrCreateTopic(topicId, {
  user_id: "user-123",
  topic: { status: "OPTED_IN", digest_schedule_id: scheduleId },
});
```

The next send follows the new schedule. Omit `digest_schedule_id` to keep the current choice, and send
`null` to return the user to the default. An id that is not an active schedule on that topic returns
400. Reads return `digest_schedule_id` when the user has chosen one, and omit it on the default.

## Inspect and release

| Goal | Node | CLI |
|---|---|---|
| See what is held on a schedule, one instance per recipient | `client.digests.schedules.listInstances(scheduleId)` | `courier digests:schedules list-instances` |
| Release one recipient now | `client.workspacePreferences.topics.releaseDigest(topicId, { section_id, user_id })` | `courier workspace-preferences:topics release-digest` |
| Release everyone on a schedule now | `client.digests.schedules.release(scheduleId)` | `courier digests:schedules release` |

Python uses the snake_case names (`list_instances`, `release_digest`, `release`).

- An instance shows `event_count` and `category_key_counts`. `event_count: 0` means the recipient's sends fell through because no key matched a category.
- Both releases return 204, including when nothing was held. A released instance leaves the list.
- Pass `tenant_id` to `releaseDigest` for a recipient who was sent to in a tenant context. Without it, the release returns 204 and sends nothing.

In the app, the topic's **Test** button releases one recipient without any ids.

## Troubleshooting

**Each event arrives as its own message.** In order: the recipient is on Instant (check the topic's
default); the Send node's template isn't linked to the topic (template settings, **Subscription
Topic**); the payload key doesn't match a category; no digest template is set.

**Events are missing from a Send to Digest digest.** The run data matched no category, or the invoke
failed (check its status: a `user_id` in `data` that isn't the recipient returns 400).

**The digest arrives with blank values.** The total uses the wrong root for the template's scope,
the item field skips the category key, or the sender wrapped events in their own `count` and
`items`. Sends and releases use the **published** template, so publish template edits first.

**Items are out of order, or `FIRST` dropped the wrong ones.** Items follow collection order. Send a
numeric timestamp and set it as the category's `sort_key`.

**The same item appears twice.** The event carried two category keys, two topic-linked Send nodes ran, or a separate digest template is linked to the topic.

**The previous digest template renders.** The recipient's digest started before the switch, see
[How it works](#how-it-works).

**An event just after the scheduled time waits a full cycle.** Expected. Release manually while
developing instead of using a short schedule.

**The digest arrives as `(no subject)`.** The digest template has no content for the channel.

## Related

- [Preferences](./preferences.md) - topics, linking templates, and the preference page where recipients pick a schedule
- [Journeys](./journeys.md) - Send nodes, journey templates, and the Send to Digest node
- [Batching](./batching.md) - the journey `batch` node, for count or quiet-time rollups
- [Send a daily digest](https://www.courier.com/docs/guides/send-a-daily-digest) · [Send to Digest node](https://www.courier.com/docs/journeys/nodes/digest)
