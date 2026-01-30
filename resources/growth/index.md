# Growth Notifications

## Quick Reference

### Rules
- Growth = help users succeed with product (not promotions)
- Onboarding: Usually no opt-in required (part of service)
- Activity notifications: Usually no opt-in required (expected)
- Re-engagement: Usually requires opt-in (not directly tied to action)
- Promotional: ALWAYS requires explicit opt-in
- When in doubt, check user preferences before sending

### Consent Requirements
| Type | Opt-in Required? |
|------|------------------|
| Onboarding (product guidance) | Usually no |
| Activity (mentions, comments) | Usually no |
| Feature announcements | Depends (if affects usage, no) |
| Re-engagement | Usually yes |
| Promotional/Marketing | Always yes |

### Frequency Limits
| Category | Max Frequency |
|----------|---------------|
| Onboarding | 1/day |
| Feature adoption | 2-3/week |
| Activity | As occurs (batch if many) |
| Re-engagement | 1/week |
| Promotional | 1-2/week |

### Common Mistakes
- Treating growth as marketing (different consent rules)
- Same onboarding for all users (personalize by type/goal)
- Feature dump ("here are 50 features!") vs. one CTA
- Continuing onboarding after user activated
- Over-notifying (causes users to disable)
- No exit conditions (user activated, stop onboarding)

### Template

**Check Preferences Before Growth Send:**
```typescript
const prefs = await courier.users.preferences.get(userId);
const topic = prefs.items.find(p => p.topic_id === "growth-notifications");

if (topic?.status === "OPTED_IN") {
  await courier.send({
    message: {
      to: { user_id: userId },
      template: "FEATURE_ANNOUNCEMENT"
    }
  });
}
```

---

Lifecycle notifications that drive user activation, engagement, retention, and expansion.

## Growth vs Marketing

Growth notifications focus on **product value** rather than promotions:

| Growth Notifications | Marketing Notifications |
|---------------------|------------------------|
| Help users succeed with product | Promote offers and sales |
| Triggered by behavior | Campaign-based broadcasts |
| Personalized to user journey | Segmented by audience |
| Educational and helpful | Promotional and persuasive |
| Often no opt-in required | Always requires opt-in |

## Categories

| Category | Purpose | See |
|----------|---------|-----|
| Onboarding | Get users to first value | [Onboarding](./onboarding.md) |
| Adoption | Drive feature discovery | [Adoption](./adoption.md) |
| Engagement | Build habits and retention | [Engagement](./engagement.md) |
| Re-engagement | Recover inactive users | [Re-engagement](./reengagement.md) |
| Referral | Drive viral growth | [Referral](./referral.md) |
| Campaigns | Promotional messages | [Campaigns](./campaigns.md) |

## User Lifecycle

| Stage | Focus | Notifications |
|-------|-------|--------------|
| Sign Up | Welcome | Transactional welcome |
| Onboard | Setup guidance | Onboarding sequence |
| Activate | Aha moment | Feature guidance, first success |
| Engage | Activity notifications | Social updates, content alerts |
| Retain | Habit building | Digests, streaks |
| Expand | Upsell opportunities | Upgrade prompts |
| Advocate | Referral | Share prompts, rewards |

## Consent Requirements

### When Opt-In Is Required

| Notification Type | Opt-In Required? | Notes |
|-------------------|-----------------|-------|
| Transactional | No | Required for service |
| Onboarding (product) | Usually no | Part of service delivery |
| Activity notifications | Usually no | Expected behavior |
| Feature announcements | Depends | If affects current usage, no |
| Re-engagement | Usually yes | Not directly tied to action |
| Promotional | Yes | Always |
| Referral invites | Yes (recipient) | Sender consented by action |

### Best Practice

When in doubt, ask. Better to have explicit consent than risk complaints. Check user preferences before sending growth notifications.

```typescript
// Check if user has opted into growth notifications
const prefs = await courier.users.preferences.get(userId);
const growthPref = prefs.items.find(p => p.topic_id === "growth-notifications");

if (growthPref?.status === "OPTED_IN") {
  await courier.send({
    message: {
      to: { user_id: userId },
      template: "FEATURE_ANNOUNCEMENT",
      data: { featureName: "Dark Mode" }
    }
  });
}
```

## Channel Selection by Lifecycle Stage

| Stage | Primary Channel | Secondary | Rationale |
|-------|----------------|-----------|-----------|
| Onboarding | Email + In-app | Push (if enabled) | Need detail, user is engaged |
| Activation | In-app | Email | Catch them in context |
| Engagement | Push + In-app | Email digest | Real-time relevance |
| Re-engagement | Email | Push, SMS | User may not be in app |
| Referral | Email + In-app | Push | Need detail for sharing |
| Campaigns | Email | Push (opt-in) | Best for promotional content |

## Measuring Growth Notifications

### Key Metrics

**Activation Rate**
- % of new users who complete key action
- Target: 40-60% in first week

**Feature Adoption**
- % of users who use announced feature
- Track before/after notification

**Engagement Retention**
- Daily/Weekly/Monthly active users
- Notification-driven sessions

**Re-engagement Rate**
- % of dormant users who return
- Compare with control group

### A/B Testing

Split test notification variants using deterministic assignment (e.g., based on user ID). Track which variant was sent for analytics.

## Anti-Patterns

### Over-Notification

**Don't:** Send notification for every small event
**Do:** Batch, digest, and prioritize

### Ignoring Context

**Don't:** Send feature announcement to users already using feature
**Do:** Target based on actual behavior

### One-Size-Fits-All

**Don't:** Same onboarding for all users
**Do:** Personalize based on user type, goals, behavior

### Notification Fatigue

**Don't:** Multiple notifications per day
**Do:** Respect frequency limits, consolidate related updates

## Frequency Guidelines

| Category | Max Frequency | Notes |
|----------|---------------|-------|
| Onboarding | 1/day | More is okay if user-triggered |
| Feature adoption | 2-3/week | Space out announcements |
| Activity notifications | As they occur | But batch if many |
| Re-engagement | 1/week | Less is more |
| Promotional | 1-2/week | Heavy opt-out risk if more |

## Related

- [Preferences](../guides/preferences.md) - Managing user notification preferences
- [Multi-Channel](../guides/multi-channel.md) - Channel routing strategies
- [Compliance](../guides/compliance.md) - Consent requirements
