# Lifecycle Marketing

Notifications Courier sends proactively rather than in response to a user action — onboarding sequences, feature adoption, activity and engagement, win-back, referral, and promotional campaigns.

**Courier does all of these.** This file maps each use case to the Courier primitive that implements it, and carries the consent and compliance rules that carry real legal exposure. It deliberately does **not** prescribe cadence, send times, or copy — "nudge at day 7" and "max 2 emails per week" are product decisions that depend on your users, not integration facts.

## Quick Reference

### Rules

- **Promotional sends require recorded opt-in.** Store *when* and *how* the user consented — you may have to produce it.
- **SMS marketing is opt-in only, always.** Never opt-out, never inferred, no exceptions.
- **Push marketing requires a promotional-push opt-in** distinct from the OS permission grant. Permission to notify is not permission to advertise.
- **Marketing email must carry a physical mailing address and a working unsubscribe link**, functional for at least 30 days after send.
- **Honor opt-out immediately, in-loop.** Suppress on the very next send — never wait for a nightly job.
- **Stop the sequence when its goal is met.** A user who activated should not receive the day-3 activation nudge. Cancel, don't let it run out.
- **Transactional and marketing cannot share a message.** One promotional line in a receipt reclassifies the whole message and drags it under opt-in and unsubscribe rules.
- **Check preferences before sending**, not after. Courier enforces subscription topics at send time — use them rather than reimplementing suppression.

### Does this need opt-in?

| Category | Opt-in required? |
|---|---|
| Onboarding / activation | Usually no — part of delivering the service the user signed up for |
| Activity notifications (mentions, comments, shares) | Usually no — expected consequence of using the product |
| Feature announcements | Grey area. Treat as marketing if the goal is upsell; as product if the goal is competent use. |
| Re-engagement / win-back | Usually **yes** — not tied to a user action |
| Promotional, sales, upgrade offers | **Always yes**, explicitly |

When you're unsure, the safe path is a subscription topic the user controls.

### Use case → Courier primitive

| Use case | Build it with |
|---|---|
| Onboarding / activation sequence | [Journey](./guides/journeys.md): `send` → `delay` → `branch` on activated? → `exit`. Cancel on activation. |
| Feature announcement | Send to an [audience](./guides/patterns.md) (`to: { audience_id }`) so targeting is a filter, not a query you maintain |
| Activity notification | Single send, or an [`add-to-digest`](./guides/batching.md) node if the user prefers a summary |
| Activity digest (daily / weekly) | [`add-to-digest`](./guides/batching.md) node + a subscription topic schedule — the user's own frequency preference drives delivery |
| Aggregated activity ("Jane and 5 others") | [`batch`](./guides/batching.md) node with `category_key` to group by target |
| Re-engagement / win-back | [Journey](./guides/journeys.md) with `delay` + `branch` on returned?, cancelled the moment they come back |
| Referral invite and reward | Single sends triggered by your referral service; reward send on qualification |
| Promotional campaign | Send to a [list or audience](./guides/patterns.md), gated on a subscription topic |
| Frequency capping across campaigns | [`throttle`](./guides/journeys.md) node (`scope: "user"`) — enforce it in Courier, not in application code |
| Letting users choose frequency | [Subscription topics + preferences](./guides/preferences.md), including a hosted or embedded preference center |
| One-off broadcast to a list or audience | Broadcasts, configured in the dashboard |

**The two things people rebuild unnecessarily** are frequency capping and digest scheduling. Both are Courier nodes. See [Batching](./guides/batching.md) and [Throttling](./guides/throttling.md).

### Cancel the sequence when its goal is met

This is the most common lifecycle bug: a user activates on day 1 and still gets the day-3 "still need help getting started?" email. Set a cancelation token when you invoke, then cancel on the success event:

```typescript
// On signup — token lets you stop the whole sequence later
await client.journeys.invoke(onboardingJourneyId, {
  user_id: userId,
  data: { first_name: user.firstName },
});

// On activation — kill every pending step
await client.journeys.cancel({ cancelation_token: `onboarding-${userId}` });
```

The token is configured in the journey's settings and templated from run data (e.g. `onboarding-{{data.user_id}}`). If the referenced field is missing at invoke time the run gets **no token and can never be cancelled by token** — see [Cancelling Runs](./guides/journeys.md#cancelling-runs).

### Common mistakes

- Sending promotional content without recorded opt-in
- Treating OS push permission as consent to advertise
- Letting a sequence run after the user did the thing it was nudging toward
- Rebuilding digest scheduling or frequency capping in application code
- Mixing an upsell into a receipt or password reset
- Deferring opt-out suppression to a batch job
- Targeting by a hand-maintained user query instead of an audience

---

## Targeting: use audiences, not queries

An audience is a filter Courier evaluates and keeps current. Send to it directly instead of resolving a user list yourself.

```typescript
await client.send.message({
  message: {
    to: { audience_id: "trial-users-no-integration" },
    template: "nt_feature_announcement_template_id",
    data: { feature_name: "Journeys" },
  },
});
```

For per-user data that Courier doesn't hold, invoke a journey per user and pass it in `data` — a `fetch` node can also pull it at send time. See [Patterns](./guides/patterns.md).

## Respecting frequency without writing a scheduler

Put a `throttle` node at the top of any lifecycle journey. `scope: "user"` caps per recipient regardless of how many campaigns are running:

```json
{ "type": "throttle", "scope": "user", "max_allowed": 2, "period": "P7D" }
```

That is the whole frequency-cap implementation. Details in [Throttling](./guides/throttling.md).

## Letting users pick their own cadence

Create a subscription topic per notification category, expose a preference center, and let Courier enforce the result at send time — you stop maintaining suppression logic entirely.

Courier offers a hosted preference page and embeddable React / Web Components. See [Preferences](./guides/preferences.md).

## Related

- [Journeys](./guides/journeys.md) — the engine behind every multi-step sequence, plus cancellation and A/B experiments
- [Batching](./guides/batching.md) — `batch` and `add-to-digest` nodes for aggregation and digests
- [Throttling](./guides/throttling.md) — frequency caps and fatigue control
- [Preferences](./guides/preferences.md) — subscription topics, preference centers, opt-out handling
- [Patterns](./guides/patterns.md) — lists, audiences, tenants, bulk targeting
- [Transactional](./transactional.md) — the non-opt-in side, and why mixing the two is a problem
