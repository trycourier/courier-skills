# Lifecycle Marketing

Notifications Courier sends proactively rather than in response to a user action, onboarding sequences, feature adoption, activity and engagement, win-back, referral, and promotional campaigns.

## Quick Reference

### Rules

- **Let Courier handle suppression.** Subscription topics are enforced at send time, so an unsubscribe takes effect on the next send with no suppression job of your own.
- **Stop the sequence when its goal is met.** A user who activated should not receive the day-3 activation nudge. Cancel, don't let it run out.

### Use case → Courier primitive

| Use case | Build it with |
|---|---|
| Onboarding / activation sequence | [Journey](./guides/journeys.md): `send` → `delay` → `branch` on activated? → `exit`. Cancel on activation. |
| Feature announcement | Send to an [audience](./guides/patterns.md) (`to: { audience_id }`) so targeting is a filter, not a query you maintain |
| Activity notification | Single send, mapped to a topic with a [digest](./guides/digests.md) so users who prefer a summary get one |
| Activity digest (daily / weekly) | A [topic digest](./guides/digests.md): send once per event, the recipient's chosen schedule drives delivery |
| Aggregated activity ("Jane and 5 others") | [`batch`](./guides/batching.md) node. Count by type ("3 likes and 2 comments") with `category_key`. To cover several posts in one message, key the categories by post title. One notification per post needs [app-side aggregation](./guides/batching.md#app-side-aggregation-only-when-the-nodes-dont-fit) |
| Re-engagement / win-back | [Journey](./guides/journeys.md) with `delay` + `branch` on returned?, cancelled the moment they come back |
| Referral invite and reward | Single sends triggered by your referral service; reward send on qualification |
| Promotional campaign | Send to a [list or audience](./guides/patterns.md), gated on a subscription topic |
| Frequency capping across campaigns | [Send limits](https://www.courier.com/docs/send/statuses#send-limits) per user, topic, or tenant. A [`throttle`](./guides/journeys.md) node caps only one point in one journey |
| Letting users choose frequency | [Subscription topics + preferences](./guides/preferences.md), including a hosted or embedded preference center |
| One-off broadcast to a list or audience | A [broadcast](https://www.courier.com/docs/broadcasts/overview), built in the dashboard or with the API: `client.broadcasts.create`, `putContent`, then `send` or `schedule` |

### Cancel the sequence when its goal is met

This is the most common lifecycle bug: a user activates on day 1 and still gets the day-3 "still need help getting started?" email. Set `cancelation_token` on the journey, then cancel on the success event:

```typescript
// On signup. The journey's token, onboarding-{{data.user_id}}, reads user_id from data
await client.journeys.invoke(onboardingJourneyId, {
  user_id: userId,
  data: { user_id: userId, first_name: user.firstName },
});

// On activation, cancel every pending step
await client.journeys.cancel({ cancelation_token: `onboarding-${userId}` });
```

If the field the token references is missing at invoke, the run gets **no token** and can't be cancelled by it. See [Cancelling Runs](./guides/journeys.md#cancelling-runs).

### Common mistakes

- Rebuilding digest scheduling or frequency capping in application code
- Targeting by a hand-maintained user query instead of an audience

## Related

- [Journeys](./guides/journeys.md), the engine behind every multi-step sequence, plus cancellation and A/B experiments
- [Digests](./guides/digests.md), recipient-scheduled summaries
- [Batching](./guides/batching.md), the `batch` node for aggregation
- [Throttling](./guides/throttling.md), frequency caps and fatigue control
- [Preferences](./guides/preferences.md), subscription topics, preference centers, opt-out handling
- [Patterns](./guides/patterns.md), lists and many-recipient sends · [Audiences](./guides/audiences.md), dynamic segments
- [Transactional](./transactional.md), action-triggered sends: OTP, receipts, order updates, security alerts
