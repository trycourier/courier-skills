# User Preferences

## Quick Reference

### Rules
- Transactional notifications: user usually CANNOT opt out (security, orders, receipts)
- Marketing notifications: MUST have explicit opt-in, MUST allow opt-out
- Product notifications: default on, allow opt-out
- Honor preference changes immediately
- Link to preferences in every email footer
- Provide one-click unsubscribe for marketing
- Opt-out must be easy — one click or one reply

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
- Making opt-out difficult
- Not honoring preference changes immediately
- No unsubscribe link in marketing emails
- Too many preference categories (confuses users)
- Too few categories (users unsubscribe entirely)

### Templates

**Get User Preferences:**

TypeScript:
```typescript
const prefs = await client.users.preferences.retrieve("user-123");
```

Python:
```python
prefs = client.users.preferences.retrieve("user-123")
```

**Update Preferences:**

The topic (`weekly-digest`) must already exist in Settings > Preferences; these calls set the *user's* preference for that topic, they do not create the topic definition itself. Calling for an unknown topic returns 404.

TypeScript:
```typescript
await client.users.preferences.updateOrCreateTopic("weekly-digest", {
  user_id: "user-123",
  topic: {
    status: "OPTED_OUT"
  }
});
```

Python:
```python
client.users.preferences.update_or_create_topic(
    "weekly-digest",
    user_id="user-123",
    topic={"status": "OPTED_OUT"},
)
```

**Check Before Sending:**

Courier auto-checks when topics are configured — link templates to topics in the Courier dashboard.

TypeScript:
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbu5x8q2v6d1c4n7w9hj" // Template linked to "weekly-digest" topic
  }
});
```

Python:
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbu5x8q2v6d1c4n7w9hj",  # Template linked to "weekly-digest" topic
    },
)
```

---

Let users control what notifications they receive and how.

## Why Preferences Matter

- **Reduce unsubscribes:** Users who can control frequency don't opt out entirely
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

### Create Topics (Dashboard)

Topics are the categories users can opt into/out of. Set them up in the Courier dashboard:

1. Go to **Settings > Preferences** in the [Courier dashboard](https://app.courier.com/settings/preferences)
2. Click **Create Topic** — give it an ID (e.g., `weekly-digest`), name, and description
3. Set the **default status**: `OPTED_IN` (product notifications) or `REQUIRED` (transactional — user can't opt out)
4. Set allowed channels for this topic

### Link Templates to Topics

Linking a template to a topic means Courier auto-checks the user's preference before sending. If the user has opted out, the send is silently skipped — no error returned.

1. Open a template in the [Designer](https://app.courier.com/designer)
2. In template settings, select the **Preference Topic** this template belongs to
3. When `client.send.message()` uses this template, Courier checks the user's preference for that topic

### How Preferences Interact with Routing

When both routing and preferences are configured:

1. Courier builds the channel list from `routing.channels`
2. It removes any channels the user has disabled for the linked topic
3. With `method: "single"`, it tries remaining channels in order
4. If no channels remain (user opted out of all), the message is silently skipped

Example: routing specifies `["email", "push", "sms"]` but user opted out of SMS for this topic → Courier only tries email and push.

### Get User Preferences

**TypeScript:**
```typescript
const preferences = await client.users.preferences.retrieve("user-123");
// Returns: { items: [{ topic_id, status, ... }] }
```

**Python:**
```python
preferences = client.users.preferences.retrieve("user-123")
# Returns an object with `.items` — list of { topic_id, status, ... }
```

### Update Preferences for a Topic

**TypeScript:**
```typescript
await client.users.preferences.updateOrCreateTopic("order-updates", {
  user_id: "user-123",
  topic: {
    status: "OPTED_IN", // or "OPTED_OUT"
    has_custom_routing: true,
    custom_routing: ["email"]
  }
});
```

**Python:**
```python
client.users.preferences.update_or_create_topic(
    "order-updates",
    user_id="user-123",
    topic={
        "status": "OPTED_IN",  # or "OPTED_OUT"
        "has_custom_routing": True,
        "custom_routing": ["email"],
    },
)
```

## Preference Center UI

### Courier Preferences Component

Courier provides a pre-built preference center component. For v8 React apps, `@trycourier/courier-react` includes `<CourierPreferences />` which renders a ready-made UI for topic opt-in/opt-out. For setup and customization options, see the [Courier Preferences docs](https://www.courier.com/docs/sdk-libraries/courier-react/preferences).

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
| Security alerts     | Required | Required | Required at highest severity tier only (see below) |
| Order updates       | Yes | Yes | Optional |
| Activity            | Yes | Yes | Optional |
| Weekly digest       | Yes | No | No |
| Promotions          | Optional | Optional | Optional |

"Required" means the user can't opt out — it does **not** mean every alert uses every required channel. Security-alert fan-out is tiered by event severity (see [Security Alert Channels](../transactional/authentication.md#security-alert-channels)); SMS is only sent for the highest-severity events (password changed, 2FA disabled, suspicious activity), not for every new device login.

## Frequency Preferences

### Options

- **Realtime:** As events happen
- **Daily digest:** Once per day
- **Weekly digest:** Once per week
- **Off:** Don't send

### Implementation

If the user prefers digest for a category, queue notifications for batched sending instead of immediate delivery — **but only for categories that are safe to batch**. Transactional categories that [batching.md](./batching.md) excludes (OTP, password reset, security alerts, order confirmations, payment receipts, shipping) must always send in real time regardless of the user's digest preference. Enforce the blocklist in your digest dispatcher; don't rely on UI to prevent users from opting these into a digest.

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

Generate unique unsubscribe links for each email. Gmail and Yahoo require list-unsubscribe headers for bulk senders; Courier sets these automatically when you configure an unsubscribe link.

### Unsubscribe vs Preference Center

Offer both options:
- Quick unsubscribe from specific category
- Link to preference center for more control
- Option to resubscribe

## Related

- [Multi-Channel](./multi-channel.md) - Channel routing
- [Campaigns](../growth/campaigns.md) - Marketing opt-in requirements
- [Hosted Preference Page](https://www.courier.com/docs/platform/preferences/hosted-page) - Deploy a hosted preference page in minutes
- [Embedding Preferences](https://www.courier.com/docs/platform/preferences/embedding-preferences) - Embeddable React components for building a preference center into your app
