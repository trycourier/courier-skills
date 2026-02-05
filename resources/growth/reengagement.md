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
| New (< 7 days) | 3 days | Onboarding help |
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

**Light Nudge (7 days):**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "LIGHT_NUDGE",
    data: {
      lastActivity: "your dashboard",
      whatsNew: ["Dark mode", "API improvements"]
    }
  }
});
```

**Cart Abandonment (Transactional - 1hr):**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "CART_REMINDER",
    data: {
      items: [{ name: "Widget", price: 29.99 }],
      cartUrl: "https://acme.com/cart"
    }
  }
});
```

**Welcome Back (when user returns):**
```typescript
// Cancel re-engagement sequence
await courier.automations.cancel({
  cancelation_token: `reengagement-${userId}`
});

// Send welcome back
await courier.send({
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

### Automation with Cancellation

Start a win-back sequence that auto-cancels when the user returns:

```typescript
// Start win-back sequence
await courier.automations.invoke("winback-sequence", {
  user_id: userId,
  cancelation_token: `reengagement-${userId}`,
  data: {
    userName: user.name,
    lastActivity: user.lastActiveAt.toISOString(),
    whatsNew: await getRecentFeatures(),
  },
});

// When user returns — cancel the sequence and welcome back
async function onUserReturn(userId: string): Promise<void> {
  // Cancel any active re-engagement sequence
  await courier.automations.cancel({
    cancelation_token: `reengagement-${userId}`,
  });

  // Increment return count for analytics
  await incrementReengagementSuccess(userId);

  // Send welcome back via in-app
  await courier.send({
    message: {
      to: { user_id: userId },
      content: {
        title: "Welcome back!",
        body: "Here's what's new since you left.",
      },
      routing: { method: "single", channels: ["inbox"] },
    },
  });
}
```

### Exit Condition

When user returns, cancel the win-back sequence and send a welcome back message instead.

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

- [Onboarding](./onboarding.md) - Prevent churn early
- [Engagement](./engagement.md) - Keep users active
- [Campaigns](./campaigns.md) - Promotional win-back offers
- [Preferences](../guides/preferences.md) - Respect opt-outs
