# Re-engagement Notifications

## Quick Reference

### Rules
- Define "inactive" based on your product's natural usage pattern
- Light nudge at 7 days, stronger at 14, win-back at 30+
- Stop after 2-3 attempts with no response
- Cancel re-engagement sequence when user returns
- Cart abandonment: Transactional at 1h/24h, Marketing (needs opt-in) at 48h+
- Don't use SMS for re-engagement (too intrusive)

### Inactivity Triggers
| User Type | Inactive Period | Action |
|-----------|----------------|--------|
| New (< 7 days) | 3+ days | Redirect to onboarding sequence (not re-engagement) |
| Active | 7 days | Light nudge |
| Active | 14 days | Stronger outreach |
| Active | 30+ days | Win-back campaign |

### Win-Back Sequence
| Day | Message | Focus |
|-----|---------|-------|
| 0 | "We miss you" | Emotional appeal |
| 3 | "Here's what's new" | Value reminder |
| 7 | "Special offer" (optional) | Incentive |
| 14 | "Last chance" | Urgency |
| 30+ | Stop or reduce | Don't burn relationship |

### Common Mistakes
- Too aggressive re-engagement (causes unsubscribes)
- No stop condition (keeps emailing forever)
- Not canceling when user returns
- SMS for re-engagement (high opt-out risk)
- Cart abandonment discount without opt-in (at 48h+)
- Same cadence for all user segments

### Templates

**Light Nudge (7 days, TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbun4x7q1v5d8c2n6w9hj",
    data: {
      lastActivity: "your dashboard",
      whatsNew: ["Dark mode", "API improvements"]
    }
  }
});
```

**Light Nudge (Python):**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbun4x7q1v5d8c2n6w9hj",
        "data": {
            "lastActivity": "your dashboard",
            "whatsNew": ["Dark mode", "API improvements"],
        },
    }
)
```

**Cart Abandonment (Transactional - 1hr):**
```typescript
// Use an idempotency key on retry-sensitive transactional paths like this one
// so a retried webhook from your cart-abandonment job cannot double-send.
// Python SDK: pass the header via `extra_headers={"Idempotency-Key": ...}`.
await client.send.message(
  {
    message: {
      to: { user_id: "user-123" },
      template: "nt_01kmrbuw8q2x6v1d4c7n5j9ht",
      data: {
        items: [{ name: "Widget", price: 29.99 }],
        cartUrl: "https://acme.com/cart",
      },
    },
  },
  { headers: { "Idempotency-Key": `cart-abandon-${cartId}` } },
);
```

**Welcome Back (when user returns):**
```typescript
// With Journeys, exit logic is built into the DAG — no external cancel needed.
// See the journey example in the "Journey with Exit Logic" section below.

// Send welcome back
await client.send.message({
  message: {
    to: { user_id: userId },
    content: { title: "Welcome back!", body: "Here's what's new since you left." },
    routing: { method: "single", channels: ["inbox"] }
  }
});
```

---

Win back inactive users and prevent churn.

## When to Re-engage

### Inactivity Detection

Define "inactive" based on your product's natural usage pattern:

| Product Type | Consider Inactive After |
|--------------|------------------------|
| Daily-use app | 3-5 days |
| Weekly tool | 2 weeks |
| Monthly service | 6 weeks |
| Seasonal product | Varies |

```typescript
interface UserActivity {
  userId: string;
  lastActiveAt: Date;
  accountCreatedAt: Date;
  reengagementAttempts: number;
}

type InactivityTier = "nudge" | "outreach" | "winback" | "dormant" | "none";

function getInactivityTier(user: UserActivity): InactivityTier {
  const daysSinceActive = Math.floor(
    (Date.now() - user.lastActiveAt.getTime()) / (1000 * 60 * 60 * 24)
  );
  const isNewUser =
    Date.now() - user.accountCreatedAt.getTime() < 7 * 24 * 60 * 60 * 1000;

  // New users get onboarding help, not re-engagement
  if (isNewUser) return "none";

  // Stop after 2-3 attempts
  if (user.reengagementAttempts >= 3) return "dormant";

  if (daysSinceActive >= 30) return "winback";
  if (daysSinceActive >= 14) return "outreach";
  if (daysSinceActive >= 7) return "nudge";
  return "none";
}
```

### Inactivity Triggers

| User Type | Inactive Period | Action |
|-----------|----------------|--------|
| New user (< 7 days) | 3 days | Onboarding help (not re-engagement) |
| Active user | 7 days | Light nudge |
| Active user | 14 days | Stronger outreach |
| Active user | 30+ days | Win-back campaign |

## Inactivity Nudges

### Light Touch (7 days)

Subject: Picking up where you left off

Include:
- What they were working on
- CTA to continue
- What's new (team updates, new content)

### Stronger Outreach (14 days)

Subject: We miss you, Jane

Include:
- Check-in message
- What happened while they were away (team activity, new features)
- Multiple help options

## Win-Back Campaigns

### When Incentives Make Sense

- User was previously engaged
- User is on free tier or canceled
- High customer lifetime value
- Product improvements address why they left

### Win-Back Sequence

| Day | Message | Focus |
|-----|---------|-------|
| Day 0 | "We miss you" | Emotional appeal |
| Day 3 | "Here's what's new" | Value reminder |
| Day 7 | "Special offer" (optional) | Incentive |
| Day 14 | "Last chance" (optional) | Urgency |
| Day 30 | Stop or reduce frequency | Don't burn relationship |

### Win-Back Email Examples

**Day 0: Emotional appeal**

Subject: We miss you, Jane

Include:
- Check-in message
- Request for feedback
- CTA to return

**Day 3: Value reminder**

Subject: 3 things you might have missed

Include:
- List of improvements/new features
- Most requested features that were added
- CTA to see what's new

**Day 7: Incentive (if appropriate)**

Subject: A little something to welcome you back

Include:
- Discount offer with code
- Expiration date
- CTA to claim discount

### Journey with Exit Logic

Build the win-back sequence as a [Journey](../guides/journeys.md) with branch nodes that check whether the user has returned before each step:

```json
{
  "name": "Win-Back Sequence",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger",
      "trigger_type": "api-invoke",
      "schema": {
        "type": "object",
        "properties": {
          "user_name": { "type": "string" },
          "last_activity": { "type": "string" }
        }
      }
    },
    {
      "id": "throttle-user",
      "type": "throttle",
      "scope": "user",
      "max_allowed": 1,
      "period": "P30D"
    },
    { "id": "send-miss-you", "type": "send", "message": { "template": "<miss-you-template-id>" } },
    { "id": "wait-3d", "type": "delay", "mode": "duration", "duration": "P3D" },
    {
      "id": "check-return",
      "type": "fetch",
      "method": "get",
      "url": "https://api.yourapp.com/users/{{user_id}}/activity",
      "merge_strategy": "overwrite"
    },
    {
      "id": "branch-returned",
      "type": "branch",
      "paths": [
        {
          "label": "User returned",
          "conditions": ["data.returned", "is equal", "true"],
          "nodes": [{ "id": "exit-returned", "type": "exit" }]
        }
      ],
      "default": {
        "nodes": [
          { "id": "send-whats-new", "type": "send", "message": { "template": "<whats-new-template-id>" } },
          { "id": "wait-7d", "type": "delay", "mode": "duration", "duration": "P7D" },
          { "id": "send-last-chance", "type": "send", "message": { "template": "<last-chance-template-id>" } },
          { "id": "exit-end", "type": "exit" }
        ]
      }
    }
  ],
  "enabled": true
}
```

**Invoke when a user becomes inactive:**

```bash
curl -sS -X POST "https://api.courier.com/journeys/$JOURNEY_ID/invoke" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "data": { "user_name": "Jane", "last_activity": "2026-05-10T12:00:00Z" }
  }'
```

The journey checks whether the user returned before sending additional messages — no external cancel call needed.

### Legacy: Automations with Cancellation

If you have existing Automations:

```typescript
await client.automations.invoke.invokeByTemplate("winback-sequence", {
  recipient: userId,
  data: {
    cancelation_token: `reengagement-${userId}`,
    userName: user.name,
    lastActivity: user.lastActiveAt.toISOString(),
  },
});

// When user returns
await client.automations.invoke.invokeAdHoc({
  recipient: userId,
  automation: {
    steps: [{ action: "cancel", cancelation_token: `reengagement-${userId}` }]
  }
});
```

## Cart Abandonment

### Legal Classification

**Important:** Cart abandonment emails can be transactional OR marketing:

| Content | Classification | Opt-in Required |
|---------|----------------|-----------------|
| "Your cart expires soon" | Transactional | No |
| "Complete your purchase for 10% off" | Marketing | Yes |

### Sequence

| Timing | Type | Content |
|--------|------|---------|
| 1 hour | Transactional | Reminder |
| 24 hours | Transactional | Still there? |
| 48 hours | Marketing (opt-in required) | Incentive |

### Transactional Cart Email

Subject: You left something in your cart

Include:
- Items in cart with images
- CTA to complete order
- Cart expiration time (if applicable)

## Feature Update for Dormant Users

Re-engage by highlighting improvements relevant to their past usage.

Subject: The feature you asked for is here

Include:
- Feature name and description
- How it benefits them specifically
- CTA to try it
- Link to see all updates

## Channel Strategy

| Notification Type | Email | Push | SMS |
|-------------------|-------|------|-----|
| Light nudge (7d) | Yes | Yes | - |
| Stronger outreach (14d) | Yes | - | - |
| Win-back (30d+) | Yes | - | - |
| Cart reminder (1h) | Yes | Yes | - |
| Cart incentive (48h) | Yes | - | - |
| Feature update | Yes | - | - |

**Why not SMS for re-engagement?**
- Higher opt-out risk
- Feels intrusive for non-urgent
- Save for high-value, time-sensitive

## Segmentation

### By Engagement Level

- **Light touch (7-14 days):** Recently engaged, need gentle reminder
- **Moderate (14-30 days):** Need stronger value proposition
- **Win-back (30-90 days):** Consider incentives
- **Dormant (90+ days):** Low-frequency, wait for major updates

### By User Value

Prioritize high-value users:
- High LTV: Personal outreach from team
- Medium LTV: Full win-back sequence
- Low LTV: Light nudge only

## Welcome Back

When a user returns after 14+ days, acknowledge it.

Channel: In-app

Include:
- What's new since they left
- Pending items they should know about

## Metrics

### Track

- **Open rate** by inactivity segment
- **Click-through rate** on CTAs
- **Return rate** - % who come back after notification
- **Retention** - % who stay active after returning
- **Unsubscribe rate** - Monitor carefully

### Benchmarks

| Metric | Target |
|--------|--------|
| Win-back email open rate | 20-30% |
| Return rate | 5-10% |
| Post-return 30-day retention | 30%+ |
| Unsubscribe rate | < 2% |

## Best Practices

### Don't Be Pushy

- Space messages appropriately
- Give genuine value, not just "come back"
- Respect unsubscribes

### Know When to Stop

After 2-3 attempts with no response:
- Reduce frequency significantly
- Wait for product improvements to share
- Don't burn the relationship

### Exit Gracefully

Subject: Is this goodbye?

Include:
- Acknowledgment this is last message for a while
- Option to stay connected
- Promise to only send important updates otherwise

## Related

- [Journeys](../guides/journeys.md) - Build multi-step win-back and cart abandonment flows as code
- [Onboarding](./onboarding.md) - Prevent churn early
- [Engagement](./engagement.md) - Keep users active
- [Campaigns](./campaigns.md) - Promotional win-back offers
- [Preferences](../guides/preferences.md) - Respect opt-outs
