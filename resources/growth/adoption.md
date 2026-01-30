# Feature Adoption Notifications

## Quick Reference

### Rules
- In-app first (user already engaged), email second
- Don't announce to users already using the feature
- Target by relevance (API feature → developers only)
- Three phases: Awareness → Education → Reinforcement
- Major features: 1-2 emails max
- Minor features: In-app only
- Consider monthly "What's New" digest instead of per-feature

### Three-Phase Approach
| Phase | Goal | Channels |
|-------|------|----------|
| Awareness | "New feature!" | In-app, Email, Push |
| Education | "Here's how" | In-app guide, Email w/video |
| Reinforcement | "You're using it!" | In-app, Push |

### Targeting Rules
| Feature Type | Target Users |
|--------------|--------------|
| API/Webhooks | Developers |
| Templates | Designers |
| Permissions | Admins/Managers |
| Reports | Managers |
| General | Everyone |

### Common Mistakes
- Announcing to users already using feature
- Announcing to wrong user segment (API to designers)
- Too many feature emails (use "What's New" digest)
- No in-app announcement (highest conversion)
- No education phase (just "it's here!")
- Missing first-use celebration

### Templates

**Feature Announcement Email:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "FEATURE_ANNOUNCEMENT",
    data: {
      featureName: "Dark Mode",
      headline: "Easy on the eyes",
      benefits: ["Reduce eye strain", "Save battery", "Look cool"],
      ctaUrl: "https://app.acme.com/settings/appearance"
    }
  }
});
```

**First-Use Celebration:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "You discovered Dark Mode! 🌙",
      body: "You just saved your eyes. Enable keyboard shortcuts next?"
    },
    routing: { method: "single", channels: ["inbox", "push"] }
  }
});
```

---

Drive discovery and usage of product features.

## When to Use

- New feature launches
- Underutilized features
- Features relevant to user's workflow
- Milestone celebrations

## Feature Announcement Framework

### Three-Phase Approach

| Phase | Goal | Channels |
|-------|------|----------|
| Awareness | "New feature!" | In-app banner, Email, Push |
| Education | "Here's how" | In-app guide, Email w/video, Tooltip series |
| Reinforcement | "You're using it!" | In-app message, Push |

## Phase 1: Awareness

### In-App Announcement

Most effective - catch users in context. Show a banner or modal when user is in the app.

### Email Announcement

For major features, follow up with email.

Subject: New: [Feature Name] is here

Include:
- Feature name and headline
- Brief description of value
- 2-3 key benefits
- CTA button
- GIF or image showing feature
- Note that they can ignore if not interested

### Target the Right Users

Don't announce to everyone - target based on relevance:
- Skip users already using the feature
- Only announce to users who would benefit
- Example: Announce API feature only to developers

## Phase 2: Education

### Tutorial Sequence

Send 2 days after awareness.

Subject: How to use [Feature] (3 simple steps)

Include:
- Video walkthrough link
- Step-by-step instructions
- Template or quick-start option
- CTA to try the feature

### In-App Tooltips

Use progressive disclosure. Show tooltips when user visits relevant page. Make them dismissable.

## Phase 3: Reinforcement

### First-Use Celebration

When user first uses the feature, celebrate.

Channel: In-app + Push

Include:
- Encouragement (e.g., "You just saved yourself hours!")
- Tip for getting more out of the feature

### Usage Milestone

Track feature usage and celebrate milestones.

Include:
- What milestone was reached
- Impact (e.g., "You've saved approximately 5 hours")
- What's next (e.g., "Power user: 50 automations")

## Targeting Strategies

### By Behavior

Target users who:
- View but don't use a feature
- Use a related feature frequently
- Would benefit based on their workflow

### By User Segment

Map features to user roles:
- Developers: API, webhooks, CLI
- Designers: Templates, branding, export
- Managers: Reports, permissions, audit log

### By Usage Pattern

If user does X a lot, suggest related feature Y:
- Frequent manual task creation → Templates
- Frequent exports → Scheduled reports
- Many team mentions → Channel notifications

## Power User Guidance

### Advanced Feature Unlock

When user reaches high usage threshold, unlock advanced features and notify them.

Include:
- Acknowledgment of their power user status
- List of advanced features they can now access
- Brief description of each

## Channel Strategy

| Phase | Primary Channel | Secondary |
|-------|----------------|-----------|
| Awareness | In-app banner | Email, Push |
| Education | In-app guide | Email (video) |
| Reinforcement | In-app message | Push |

### Why In-App First

- User is already engaged
- Feels like product guidance, not marketing
- Can be contextual (show when relevant)
- Higher conversion than email

## Frequency Guidelines

- **Major features:** 1-2 emails max
- **Minor features:** In-app only
- **Don't:** Announce every small update
- **Do:** Batch related updates

Consider a monthly "What's New" digest instead of per-feature announcements.

## Metrics

### Track Per Feature

- **Awareness:** % of target users who saw announcement
- **Click-through:** % who clicked to learn more
- **Adoption:** % who used feature after notification
- **Retention:** % still using after 30 days

### A/B Test Elements

- Subject lines
- CTA button text
- With/without video
- In-app vs email first

## Related

- [Onboarding](./onboarding.md) - First-time user flows
- [Engagement](./engagement.md) - Ongoing usage patterns
- [Inbox](../channels/inbox.md) - In-app notifications
