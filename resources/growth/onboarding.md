# Onboarding Notifications

## Quick Reference

### Rules
- Goal: Get user to "aha moment" as fast as possible
- Day 0: Welcome email + getting started guide (1 hour after signup)
- Day 1: Reminder if setup incomplete
- Day 2-3: Nudge toward core action
- Day 4-7: Offer help if not activated
- STOP onboarding when user activates (send success message instead)
- Max 3-4 emails in first week (not 7)

### Timing Schedule
| Day | Channel | Content |
|-----|---------|---------|
| 0 (immediate) | Email | Transactional welcome |
| 0 (+1 hour) | Email/In-app | Getting started guide |
| 1 | Email + Push | Setup reminder (if incomplete) |
| 2-3 | Email | Core action nudge |
| 4-7 | Email | Help offer |

### Exit Conditions
| Condition | Action |
|-----------|--------|
| User activated | Stop onboarding, send success |
| User completed setup | Move to activation phase |
| User unsubscribed | Stop immediately |

### Common Mistakes
- Too many emails (7 in first week = unsubscribe)
- Feature dumping ("here are 50 features!")
- No personalization (same flow for everyone)
- No exit condition (onboarding continues after activation)
- Asking for permission on first launch (wait for value)
- Immediate system prompt for push (use pre-permission)

### Templates

**Getting Started (Day 0 +1hr):**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "GETTING_STARTED",
    data: {
      userName: "Jane",
      steps: [
        { title: "Connect your data", time: "2 min" },
        { title: "Create first dashboard", time: "5 min" }
      ]
    }
  }
});
```

**Activation Success:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ACTIVATION_SUCCESS",
    data: {
      achievement: "First dashboard created!",
      nextStep: "Invite your team"
    },
    routing: { method: "all", channels: ["email", "push", "inbox"] }
  }
});
```

---

Get new users to their first value moment as quickly as possible.

## The Goal

Onboarding notifications exist to:
1. **Reduce time-to-value** - Help users succeed faster
2. **Drive activation** - Get users to the "aha moment"
3. **Reduce churn** - Users who don't activate, leave

## The "Aha Moment"

Every product has a moment when users "get it":

| Product Type | Aha Moment |
|--------------|------------|
| Project management | Create first task, see it complete |
| Analytics | See first dashboard with their data |
| Communication | Send first message, get response |
| E-commerce | Complete first purchase |
| SaaS tool | Complete core workflow |

**Your job:** Get users there as fast as possible.

## Onboarding Flow

| Day | Stage | Action |
|-----|-------|--------|
| Day 0 | Welcome | Welcome email + getting started guide |
| Day 1 | Setup | Reminder if setup incomplete |
| Day 2-3 | First Action | Nudge toward core action |
| Day 4-7 | Activation Help | Offer help if not activated |
| Day 7+ | Success or Re-engage | Celebrate or try re-engagement |

## Day 0: Welcome

### Transactional Welcome

Immediate confirmation (see [Account](../transactional/account.md)). Keep it simple: confirm account, provide login link.

### Getting Started Guide

Follow-up 1 hour after welcome with actionable guidance.

Subject: Get started with Acme in 3 steps

Include:
- User's name
- Checklist of 2-3 setup steps with time estimates
- Single CTA button: "Start Now"
- Offer to reply for help

## Day 1: Setup Reminder

If user hasn't completed setup, send a reminder.

Subject: Quick question: Ready to finish setup?

Include:
- What step they need to complete
- Time estimate
- Why it matters (e.g., "unlocks collaboration features")

Channels: Email + Push

## Day 2-3: First Action Nudge

Push toward the core action that leads to the aha moment.

Subject: Create your first project (5 min walkthrough)

Include:
- Template or quick-start option
- Video walkthrough link
- Encouragement: "Most users find their aha moment right here"

## Day 4-7: Activation Help

If user still hasn't activated, offer help.

Subject: Need a hand getting started?

Include:
- Acknowledgment that everyone's different
- Multiple help options (video, chat, call)
- Low-pressure tone

## Checklist Pattern

### In-App + Email Sync

Track onboarding progress and nudge via appropriate channel. For incomplete steps, prefer in-app first, then email.

### Completion Celebration

When onboarding is complete, celebrate the achievement. Channels: In-app + Push.

Include:
- Achievement badge or emoji
- What they can do next
- Link to explore more

## Personalized Onboarding

### By User Type

Customize onboarding based on user role (developer, designer, manager) and surface relevant features.

### By Goal

If user selected a goal during signup (increase productivity, team collaboration), customize the onboarding flow to match.

## Channel Strategy

| Day | Channel | Rationale |
|-----|---------|-----------|
| 0 (immediate) | Email | Confirmation, reference |
| 0 (+1hr) | In-app | They're likely still there |
| 1 | Email + Push | Bring them back |
| 2-3 | Email | Core guidance |
| 4-7 | Email | Help offer |
| 7+ | Email (less frequent) | Re-engagement territory |

## Automation

### Courier Automations

Use Courier Automations to build onboarding sequences with delays, conditions, and cancellation:

```typescript
// Start onboarding when user signs up
await courier.automations.invoke("onboarding-sequence", {
  user_id: "user-123",
  cancelation_token: `onboarding-${userId}`,
  data: {
    userName: "Jane",
    signupDate: new Date().toISOString(),
    timezone: user.timezone || "America/New_York"
  }
});
```

### Exit Conditions

When the user activates, cancel the onboarding sequence and send a success message:

```typescript
// User completed their aha moment — stop onboarding
await courier.automations.cancel({
  cancelation_token: `onboarding-${userId}`
});

// Send activation success
await courier.send({
  message: {
    to: { user_id: userId },
    template: "ACTIVATION_SUCCESS",
    data: {
      achievement: "First dashboard created!",
      nextStep: "Invite your team"
    },
    routing: { method: "all", channels: ["email", "push", "inbox"] }
  }
});
```

### Timezone-Aware Scheduling

Onboarding emails should arrive during business hours in the user's local timezone:

```typescript
function getNextDeliveryTime(
  timezone: string,
  targetHour: number = 9
): Date {
  const now = new Date();
  const userTime = new Date(
    now.toLocaleString("en-US", { timeZone: timezone })
  );
  const userHour = userTime.getHours();

  // If past target hour today, schedule for tomorrow
  if (userHour >= targetHour) {
    userTime.setDate(userTime.getDate() + 1);
  }
  userTime.setHours(targetHour, 0, 0, 0);
  return userTime;
}

// Schedule Day 1 reminder for 9am user local time
const deliverAt = getNextDeliveryTime(user.timezone, 9);
```

### Incomplete Step Detection

Track which onboarding steps are incomplete to send targeted reminders:

```typescript
interface OnboardingProgress {
  userId: string;
  steps: {
    id: string;
    title: string;
    completed: boolean;
    completedAt?: Date;
  }[];
}

async function sendStepReminder(progress: OnboardingProgress): Promise<void> {
  const nextStep = progress.steps.find((s) => !s.completed);
  if (!nextStep) return; // All steps complete

  await courier.send({
    message: {
      to: { user_id: progress.userId },
      template: "ONBOARDING_STEP_REMINDER",
      data: {
        stepTitle: nextStep.title,
        completedCount: progress.steps.filter((s) => s.completed).length,
        totalSteps: progress.steps.length,
      },
    },
  });
}
```

## Metrics

### Track

- **Activation rate** - % who complete key action
- **Time to activation** - Days from signup to key action
- **Onboarding completion** - % who complete all steps
- **Email engagement** - Opens, clicks on onboarding emails
- **Drop-off points** - Where users abandon

### Benchmarks

| Metric | Good | Great |
|--------|------|-------|
| Day 1 return | 30% | 50%+ |
| Week 1 activation | 20% | 40%+ |
| Onboarding completion | 40% | 60%+ |
| Email open rate | 50% | 70%+ |

## Common Mistakes

### Too Many Emails

**Bad:** 7 emails in first week
**Good:** 3-4 emails, behavioral triggers

### Feature Dumping

**Bad:** "Here are 50 features!"
**Good:** "Do this one thing"

### No Personalization

**Bad:** Same flow for everyone
**Good:** Adapt to user type and behavior

### Missing Exit Conditions

**Bad:** Keep sending even after activation
**Good:** Stop and celebrate success

## Related

- [Account](../transactional/account.md) - Welcome message (transactional)
- [Adoption](./adoption.md) - Feature discovery after onboarding
- [Re-engagement](./reengagement.md) - If onboarding fails
- [Multi-Channel](../guides/multi-channel.md) - Channel routing
