# Engagement Notifications

## Quick Reference

### Rules
- Activity notifications: Send to affected user, not actor
- Batch likes/follows: "Jane and 5 others" not 6 separate
- Direct mentions: Higher priority than likes
- Streaks: Celebrate at 3, 7, 14, 30, 60, 90, 365 days
- Daily digest: Only send if there's content (never empty)
- Respect user preference for realtime vs digest

### Activity Priority
| Type | Priority | Channels |
|------|----------|----------|
| Direct mention | High | Push + In-app + Email |
| Comment/reply | High | Push + In-app |
| Like (single) | Low | In-app only |
| Likes (batch) | Low | In-app only |
| New follower | Low | In-app only |
| Streak at risk | High | Push |

### Frequency Limits
| Type | Max |
|------|-----|
| Activity | 10/hour |
| Milestone | 1/hour |
| Streak | 1/day |
| Digest | 1/period |

### Common Mistakes
- 10 separate "liked your post" notifications (batch them!)
- Sending activity to wrong user (actor vs affected)
- No batching window (send after 5-10 min delay)
- Empty digests ("Nothing happened this week")
- Streak notifications for low-value streaks (< 3 days)
- Same urgency for likes vs direct mentions

### Templates

**Batched Activity:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Your post is getting attention!",
      body: "Jane, Bob, and 8 others liked your post"
    },
    routing: { method: "all", channels: ["push", "inbox"] }
  }
});
```

**Streak Celebration:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "7-day streak! 🔥",
      body: "You're building a habit. Keep it going!"
    },
    routing: { method: "single", channels: ["push", "inbox"] }
  }
});
```

**Streak at Risk:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Your streak is at risk!",
      body: "Log in within 4 hours to keep your 14-day streak alive."
    },
    routing: { method: "single", channels: ["push"] }
  }
});
```

---

Build habits, drive retention, and keep users active with activity notifications.

## Types of Engagement Notifications

| Type | Trigger | Example |
|------|---------|---------|
| Activity | User action affects another user | "Jane commented on your post" |
| Content | New relevant content available | "5 new posts in your feed" |
| Milestone | User achieves something | "You've completed 100 tasks!" |
| Streak | Maintaining consecutive activity | "7-day streak! Keep it going" |
| Digest | Aggregated updates | "Your weekly summary" |

## Activity Notifications

### Social Notifications

The core engagement loop for social/collaborative products:

1. User A takes action
2. Send notification to User B (affected user)
3. User B returns to respond
4. User A gets notified
5. Loop continues

### Common Activity Types

- **Comment:** "Jane commented on your post"
- **Mention:** "Mike mentioned you in a comment"
- **Like:** "Sarah liked your post"
- **Follow:** "Bob started following you"
- **Share:** "Lisa shared your article"

Channels: In-app + Push for real-time, Email for important mentions

## Batching & Aggregation

### Why Batch

- Reduce notification fatigue
- "5 people liked your post" > 5 separate notifications
- Higher engagement with aggregated content

### Batch Summary Formats

- 1 actor: "Jane liked your post"
- 2 actors: "Jane and Bob liked your post"
- 3+ actors: "Jane, Bob, and 3 others liked your post"

### Implementation

Queue events and batch after a delay window. Group by type and target, then summarize:

```typescript
interface ActivityEvent {
  type: "like" | "comment" | "follow" | "share";
  actorId: string;
  actorName: string;
  targetId: string;
  targetOwnerId: string;
  createdAt: Date;
}

function formatActors(names: string[]): string {
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  return `${names[0]}, ${names[1]}, and ${names.length - 2} others`;
}

async function processBatchedEvents(events: ActivityEvent[]): Promise<void> {
  // Group by target owner + type + target
  const grouped = new Map<string, ActivityEvent[]>();
  for (const event of events) {
    const key = `${event.targetOwnerId}:${event.type}:${event.targetId}`;
    const group = grouped.get(key) ?? [];
    group.push(event);
    grouped.set(key, group);
  }

  for (const [, group] of grouped) {
    const actorNames = [...new Set(group.map((e) => e.actorName))];
    const summary = formatActors(actorNames);

    await courier.send({
      message: {
        to: { user_id: group[0].targetOwnerId },
        content: {
          title: `${summary} ${group[0].type}d your post`,
          body: `You have ${group.length} new ${group[0].type}s`,
        },
        routing: { method: "all", channels: ["push", "inbox"] },
      },
    });
  }
}
```

### Batch Window Strategy

Use a 5-10 minute delay queue. When the first event arrives, start a timer. Send the batch when either the timer expires or the event count hits a threshold:

```typescript
const BATCH_WINDOW_MS = 5 * 60 * 1000; // 5 minutes
const BATCH_MAX_EVENTS = 50;

async function onActivityEvent(event: ActivityEvent): Promise<void> {
  const batchKey = `batch:${event.targetOwnerId}:${event.type}`;

  await queue.add(batchKey, event);
  const count = await queue.length(batchKey);

  if (count === 1) {
    // First event — schedule batch processing
    setTimeout(() => flushBatch(batchKey), BATCH_WINDOW_MS);
  } else if (count >= BATCH_MAX_EVENTS) {
    // Threshold hit — flush immediately
    await flushBatch(batchKey);
  }
}
```

## Digests

### Daily Digest

Send if there's content worth sharing. Don't send empty digests.

Subject: Your daily digest - [Date]

Include:
- Stats summary (new followers, likes, comments)
- Top performing content
- Action items (comments to respond to)
- CTA to view all activity

### Weekly Digest

Subject: Your week in review - [Date Range]

Include:
- Week summary (posts created, views, engagement trend)
- Top post
- Insights and suggestions
- Suggested actions

## Milestone Notifications

### Achievement Celebrations

Define meaningful milestones: 1, 10, 100, 1000.

When user hits milestone, send celebration:
- Channel: In-app + Push
- Include: Achievement, encouragement, what's next

Example: "100 tasks completed! Your productivity is on fire. Keep up the great work."

### Progress Notifications

For goals, show progress updates.

Include:
- Current progress vs target
- Percentage complete
- Encouragement message

## Streak Notifications

### Streak Calculation

```typescript
interface StreakData {
  userId: string;
  currentStreak: number;
  lastActiveDate: Date;
  longestStreak: number;
}

const STREAK_MILESTONES = [3, 7, 14, 30, 60, 90, 365];

function checkStreakStatus(streak: StreakData): "active" | "at_risk" | "broken" {
  const hoursSinceActive =
    (Date.now() - streak.lastActiveDate.getTime()) / (1000 * 60 * 60);

  if (hoursSinceActive < 20) return "active";
  if (hoursSinceActive < 28) return "at_risk"; // 4-hour warning window
  return "broken";
}

async function handleStreakCheck(streak: StreakData): Promise<void> {
  const status = checkStreakStatus(streak);

  if (status === "at_risk" && streak.currentStreak >= 3) {
    const hoursLeft = Math.floor(
      28 - (Date.now() - streak.lastActiveDate.getTime()) / (1000 * 60 * 60)
    );
    await courier.send({
      message: {
        to: { user_id: streak.userId },
        content: {
          title: "Your streak is at risk!",
          body: `Log in within ${hoursLeft} hours to keep your ${streak.currentStreak}-day streak alive.`,
        },
        routing: { method: "single", channels: ["push"] },
      },
    });
  }
}
```

### Milestone Celebrations

Celebrate streak milestones with increasing intensity:
- 7 days: "One week! You're building a habit."
- 30 days: "One month! You're unstoppable."
- 365 days: "ONE YEAR! You're a legend."

Channel: In-app + Push

## Channel Strategy

| Notification Type | Push | In-App | Email |
|-------------------|------|--------|-------|
| Direct mention | Yes | Yes | Yes |
| Comment/reply | Yes | Yes | - |
| Like (single) | - | Yes | - |
| Likes (batch) | - | Yes | - |
| New follower | - | Yes | - |
| Daily digest | - | - | Yes |
| Weekly digest | - | - | Yes |
| Milestone | Yes | Yes | - |
| Streak at risk | Yes | - | - |

## Frequency Management

### Don't Over-Notify

Track notification frequency per user and enforce limits:
- Activity: Max 10/hour
- Milestone: Max 1/hour
- Streak: Max 1/day
- Digest: Max 1/period

### User Preference Integration

Respect user preferences for notification channels and frequency. Courier can automatically check preferences before sending.

## Related

- [Inbox](../channels/inbox.md) - In-app notification center
- [Push](../channels/push.md) - Push notification best practices
- [Preferences](../guides/preferences.md) - User notification preferences
- [Batching](../guides/batching.md) - Combining notifications into digests
- [Throttling](../guides/throttling.md) - Controlling notification frequency
- [Re-engagement](./reengagement.md) - When engagement drops
