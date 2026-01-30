# User Preferences

## Quick Reference

### Rules
- Transactional notifications: user usually CANNOT opt out (security, orders, receipts)
- Marketing notifications: MUST have explicit opt-in, MUST allow opt-out
- Product notifications: default on, allow opt-out
- Honor preference changes immediately
- Link to preferences in every email footer
- Provide one-click unsubscribe for marketing
- GDPR/CAN-SPAM require easy opt-out mechanism

### Category Defaults
| Category | Default | Can Opt Out? |
|----------|---------|--------------|
| Security alerts | ON | No |
| Order updates | ON | No |
| Password reset | ON | No |
| Product updates | ON | Yes |
| Activity (mentions) | ON | Yes |
| Weekly digest | ON | Yes |
| Marketing/Promotions | OFF | Yes (opt-in required) |
| Newsletter | OFF | Yes (opt-in required) |

### Common Mistakes
- Allowing opt-out from security/transaction notifications
- Pre-checking marketing opt-in boxes (invalid consent)
- Making opt-out difficult (violates regulations)
- Not honoring preference changes immediately
- No unsubscribe link in marketing emails
- Too many preference categories (confuses users)
- Too few categories (users unsubscribe entirely)

### Templates

**Get User Preferences:**
```typescript
const prefs = await courier.users.preferences.get("user-123");
```

**Update Preferences:**
```typescript
await courier.users.preferences.update("user-123", "weekly-digest", {
  status: "OPTED_OUT"
});
```

**Check Before Sending:**
```typescript
// Courier auto-checks when topics are configured
// Link templates to topics in Courier dashboard
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "WEEKLY_DIGEST" // Template linked to "weekly-digest" topic
  }
});
```

---

Let users control what notifications they receive and how.

## Why Preferences Matter

- **Reduce unsubscribes:** Users who can control frequency don't opt out entirely
- **Legal compliance:** GDPR, CAN-SPAM require easy opt-out
- **Better engagement:** Users receive what they want, when they want
- **Trust:** Respecting preferences builds trust

## Preference Types

### Channel Preferences

Which channels can we use to reach this user?

- Email: enabled/disabled
- Push: enabled/disabled
- SMS: enabled/disabled
- Slack: enabled/disabled

### Category Preferences

What types of notifications does the user want?

- **Transactional (usually can't opt out):** Order updates, security alerts
- **Product:** Product updates, activity mentions, weekly digest
- **Marketing (requires opt-in):** Promotions, newsletter

### Frequency Preferences

How often?

- Realtime
- Daily digest
- Weekly digest
- Monthly
- Off

## Courier Preferences API

Courier provides APIs to get and update user preferences:

### Get User Preferences

```typescript
const preferences = await courier.users.preferences.get("user-123");
// Returns: { items: [{ topic_id, status, ... }] }
```

### Update Preferences for a Topic

```typescript
await courier.users.preferences.update("user-123", "order-updates", {
  status: "OPTED_IN", // or "OPTED_OUT"
  channel_preferences: [
    { channel: "email", enabled: true },
    { channel: "sms", enabled: false }
  ]
});
```

### Define Topics in Dashboard

Create preference topics (categories) in the Courier dashboard under **Preferences**. Link templates to topics so Courier automatically respects preferences when sending.

## Preference Center UI

### Courier Preferences Component

Courier provides a pre-built, customizable preference center component for React applications.

### Custom Preference Center

Build your own UI with these sections:

**Essential Notifications (can't turn off)**
- Security alerts
- Order and payment updates

**Product Updates**
- Activity (mentions, comments, replies)
- Weekly digest
- New feature announcements

**Channels**
- Email
- Push notifications
- SMS

**Marketing**
- Promotions and offers
- Newsletter

Include a "Save Preferences" button and an option to unsubscribe from all marketing emails.

## Implementing Preferences

### Check Before Sending

Before sending a notification, check if the user has opted into that category. If opted out, skip sending.

### Courier Handles It

When you set up categories in Courier and link templates to categories, Courier automatically checks preferences before sending.

## Category Structure

### Example Hierarchy

```
notifications/
├── essential/           # Can't opt out
│   ├── security
│   ├── account
│   └── orders
├── product/             # Default on, can opt out
│   ├── activity
│   ├── digest
│   └── features
└── marketing/           # Default off, must opt in
    ├── promotions
    └── newsletter
```

### Category Configuration

For each category, define:
- Name (display name)
- Description
- Default status (opted in or opted out)
- Whether user can opt out

## Channel + Category Matrix

Users can control both what and how:

|                     | Email | Push | SMS |
|---------------------|-------|------|-----|
| Security alerts     | Required | Required | Required |
| Order updates       | Yes | Yes | Optional |
| Activity            | Yes | Yes | Optional |
| Weekly digest       | Yes | No | No |
| Promotions          | Optional | Optional | Optional |

## Frequency Preferences

### Options

- **Realtime:** As events happen
- **Daily digest:** Once per day
- **Weekly digest:** Once per week
- **Off:** Don't send

### Implementation

If user prefers digest for a category, queue notifications for batched sending instead of immediate delivery.

## Best Practices

### Default to On (Carefully)

- **Transactional:** Always on, can't opt out
- **Product:** Default on, easy to opt out
- **Marketing:** Default off, require opt in

### Make It Easy

- Link to preferences in every email footer
- Provide preference center in app settings
- Allow quick opt-out without login

### Granularity Balance

- Too few options: Users unsubscribe entirely
- Too many options: Users confused, don't set
- **Sweet spot:** 5-10 meaningful categories

### Respect Immediately

When user changes preference:
1. Update preference immediately
2. If opted out, cancel any pending notifications in that category

## Unsubscribe Handling

### One-Click Unsubscribe

Required by some regulations. Generate unique unsubscribe links for each email.

### Unsubscribe vs Preference Center

Offer both options:
- Quick unsubscribe from specific category
- Link to preference center for more control
- Option to resubscribe

## Related

- [Compliance](./compliance.md) - Legal requirements for preferences
- [Multi-Channel](./multi-channel.md) - Channel routing
- [Campaigns](../growth/campaigns.md) - Marketing opt-in requirements
