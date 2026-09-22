# Digests

A digest collects the messages sent for one subscription topic and delivers them together on a
schedule the recipient picks. Instead of five emails about five comments, a recipient on Daily gets
one email at 9:00 listing all five. The topic owns everything: the digest template, the schedules,
and the categories.

## Quick Reference

### Rules

- **Collect with the Send API by default.** Link a template to the topic, then `POST /send` it once per event. Use the Send to Digest journey node only when the events already flow through a journey. **Never feed one topic both ways** (Send API and Send to Digest node): mixing them produces `INCOMPLETE_PROFILE_DATA` or `UNROUTABLE` errors.
- **A send is only held if it carries the topic**, through the template's `subscription.topic_id` or the send's `message.preferences.subscription_topic_id`.
- **The send's `data` needs a top-level key named exactly like a category**, including case. A send with no matching key is delivered immediately as a normal message, with no error.
- **One `/send` call is one item.** Never send `count` or `items` yourself. Courier builds them at release.
- **The digest template is set on the topic's digest configuration**, separately from the templates you send. Removing it turns digesting off for the topic. If it is a separate template, **don't link it to the topic**, or it gets collected like any other send and the digest contains a copy of itself.
- **Include an Instant schedule** so recipients can opt out, but don't make it the default: a recipient who never chose a schedule falls back to the default (or the first schedule), and Instant never holds anything.
- **`schedules` needs at least one entry.** `schedules: []` returns 400. Turn a digest off with `digest: null` or `deleteDigest`.
- **Events past a category's `limit` are discarded** at release, not carried into the next digest.
- **Never link a transactional template** (OTP, password reset, receipts) to a digest topic. A recipient on Daily would get their code tomorrow.
- Held sends show status `DIGESTED` in message logs. The release is a new message.

### Common Mistakes

- Sending `{ "author_name": "..." }` when the category is `comments`. It delivers individually. Send `{ "comments": { "author_name": "..." } }`
- Reading a field without the category key. Each item is one send's whole `data`, so the author is `comments.author_name` on the item
- Writing the total without the root that matches the template's scope (see [What the template receives](#what-the-template-receives)). The wrong form renders an empty string
- Looping with `{{#each}}` in a text block. It renders, but the designer then shows broken variable chips. Use a `list` element with `loop`
- Testing with Instant as the topic's default. Every new test user delivers immediately, and nothing is ever `DIGESTED`
- Linking a digest template with no content for the channel. The release still sends, with subject `(no subject)` and an empty body
- Putting the digest body in a channel override (`channels.email.override.html`). Overrides on held sends are dropped at release
- Storing a "digest frequency" field on the profile and branching in app code. Recipients choose a schedule on the topic
- Using a digest for a burst-of-events rollup inside a journey. That is the journey `batch` node, a different mechanism, see [batching.md](./batching.md)

## How it works

1. Link the templates you send to the topic (`subscription: { topic_id }`, see [preferences.md](./preferences.md#setting-it-up)).
2. Configure the topic's digest: the digest template, at least one schedule, and optional categories.
3. Send once per event. What happens depends on the recipient's schedule for the topic:
   - **Instant:** delivered now as an ordinary message.
   - **Any other schedule:** held as `DIGESTED`. At the scheduled time Courier renders the digest template once with everything held for that recipient.

A recipient who never picked a schedule is on the topic's default schedule, or its first schedule
when none is marked default. Digests are kept per recipient and per tenant.

## Configure a topic's digest

In the app: Preferences Editor, open the topic, **Digest settings** (up to four schedules and five
categories). Then **Publish** the preferences so recipients see the schedule choices.

Through the API, the whole configuration is the `digest` object on topic create and replace:

```typescript
const topic = await client.workspacePreferences.topics.create(sectionId, {
  name: "Activity",
  default_status: "OPTED_IN",
  routing_options: ["email"],
  digest: {
    template_id: "nt_01kmrbtm6q9x3c7v1d5w2n8hj",
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

```python
topic = client.workspace_preferences.topics.create(
    section_id,
    name="Activity",
    default_status="OPTED_IN",
    routing_options=["email"],
    digest={
        "template_id": "nt_01kmrbtm6q9x3c7v1d5w2n8hj",
        "schedules": [
            {"frequency": "daily", "time": "09:00", "timezone": "America/New_York", "is_default": True},
            {"frequency": "instant"},
        ],
        "categories": [{"category_key": "comments", "retain": "FIRST", "limit": 10}],
    },
)

topic_id = topic.id
schedule_ids = [s.schedule_id for s in topic.digest.schedules]
```

| Field | Notes |
|---|---|
| `template_id` | Required. The template that renders the digest. |
| `schedules[].frequency` | `instant`, `daily`, `weekdays`, `weekly`, `custom_days`, `monthly`. |
| `schedules[].time` | `HH:MM`, 24-hour. Required for everything except `instant`. |
| `schedules[].timezone` | IANA name, DST aware. Absent means UTC. The schedule's own zone, not each recipient's. |
| `day_of_week` / `days_of_week` / `day_of_month` | Required for `weekly` / `custom_days` / `monthly`. A missing one returns 400. |
| `schedules[].is_default` | The schedule for recipients who have not chosen. Set it explicitly. |
| `schedules[].schedule_id` | Send it to update an existing schedule in place. The array is a full replacement, so a schedule you leave out is deleted. |
| `categories[]` | `category_key`, `retain` (`FIRST`, `LAST`, `HIGHEST`, `LOWEST`, `NONE`), `limit` (1 to 100, default 10), and `sort_key` for `HIGHEST`/`LOWEST`. Omit categories to collect everything under one key, `digest`. |
| `trigger_empty` | Send on schedule even with nothing collected. Off by default. |

`replace` is a full replacement of the topic, but omitting `digest` leaves the digest untouched. To
turn it off, send `digest: null` or call `client.workspacePreferences.topics.deleteDigest(topicId, { section_id })`.
A stored schedule the `frequency` values can't express comes back without `frequency` and never fires.

CLI: `courier workspace-preferences:topics create`, `replace`, and `delete-digest`.

### Schedule ids

Schedule ids are returned on the topic, under `digest.schedules[].schedule_id`, from create,
replace, and `client.workspacePreferences.topics.retrieve(topicId, { section_id })`. Newer ids look
like `sch_01m26nhsf7fzxr5kngwf8p0b2c`. Older ones look like `sch/{uuid}` and need the slash written
as `%2F` in a raw URL. The SDKs escape both.

## Send events

Send a linked template once per event, keyed by the category name:

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbtm6q9x3c7v1d5w2n8hj",
    data: { comments: { author_name: "Priya Shah", comment_text: "Can we ship Friday?" } },
  },
});
```

An event with two matching keys (`comments` and `mentions`) is filed in both categories. Include
only the keys the event belongs in.

### From a journey

The Send to Digest node adds the journey's event to the topic's digest. The topic still controls
schedule, categories, and template.

```json
{ "type": "add-to-digest", "subscription_topic_id": "<topic-id>" }
```

If the topic has no digest template when the first event arrives, the run is marked `ERROR` and stops.

## What the template receives

At release, the digest template receives one object per category with the total `count` and the
retained `items`. Each item is the full `data` object from one send, so it repeats the category key.
`count` is every event in the window and can exceed the number of items. Items are not in send order.

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
| `scope: "strict"` | `{{data.comments.count}}` |

With no categories, the key is `digest` and each item is the send's `data` unwrapped.

If you offer Instant, use a separate digest template that is not linked to the topic. Instant
recipients then get the per-event template you sent, and the digest template only ever renders the
list. A single template serving both receives one event with no `items` for Instant recipients, and
the list above renders nothing for them. A value that is the same on every event (a build number) still
arrives per item. Read it inside the loop, not positionally from `items.[0]`, which vanishes silently
when the first item lacks it.

## Per-recipient schedule

Recipients choose a schedule in the hosted or embedded preference page. To set it from your backend,
pass `digest_schedule_id` on the user's topic preference:

```typescript
await client.users.preferences.updateOrCreateTopic(topicId, {
  user_id: "user-123",
  topic: { status: "OPTED_IN", digest_schedule_id: scheduleId },
});
```

```python
client.users.preferences.update_or_create_topic(
    topic_id,
    user_id="user-123",
    topic={"status": "OPTED_IN", "digest_schedule_id": schedule_id},
)
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
- A wrong schedule id returns an empty list, not an error.
- Both releases return 204, including when nothing was held. A released instance leaves the list.
- Pass `tenant_id` to `releaseDigest` for a recipient who was sent to in a tenant context.

In the app, the topic's **Test** button releases one recipient without any ids.

## Troubleshooting

**Each event arrives as its own message.** In order: the payload key doesn't match a category; the
recipient is on Instant (check the topic's default); the send doesn't carry the topic; no digest
template is set.

**The digest arrives with blank values.** The total uses the wrong root for the template's scope,
the item field skips the category key, or the sender wrapped events in their own `count` and
`items`. Sends and releases use the **published** template, so publish template edits first.

**The same item appears twice.** The event carried two category keys, or a separate digest template is linked to the topic.

**An event just after the scheduled time waits a full cycle.** Expected. Release manually while
developing instead of using a short schedule.

**The digest arrives as `(no subject)`.** The digest template has no content for the channel.

## Related

- [Preferences](./preferences.md) - topics, linking templates, and the preference page where recipients pick a schedule
- [Batching](./batching.md) - the journey `batch` node, for count or quiet-time rollups
- [Journeys](./journeys.md) - the Send to Digest node
- [Send a daily digest](https://www.courier.com/docs/guides/send-a-daily-digest) · [Send to Digest node](https://www.courier.com/docs/journeys/nodes/digest)
