# Migrate from Any Notification System

## Quick Reference

### Rules
- Use Courier's Test environment API key during migration; switch to Production only after validation
- Run old and new systems in parallel during migration — don't cut over in one step
- Keep the same user identifiers when creating Courier profiles to simplify cutover
- Content lives in Templates; orchestration lives in Automations — keep them separate
- Configure provider integrations (SendGrid, Twilio, etc.) in the Courier dashboard before sending
- Idempotency keys prevent duplicates during the parallel-run phase

### Common Mistakes
- Cutting over all traffic at once instead of running in parallel
- Forgetting to configure providers in the dashboard before sending
- Not migrating user preferences (users lose their opt-out choices)
- Recreating complex orchestration logic in code instead of using Automations
- Sending to production before validating in the Test environment
- Not mapping existing user IDs to Courier profile IDs (causes duplicate users)

---

This guide covers migrating from any custom-built or third-party notification system to Courier. If you're migrating from a specific platform, see the dedicated guides: [Migrate from Knock](./migrate-from-knock.md), [Migrate from Novu](./migrate-from-novu.md).

## 1. Audit Your Existing System

Before writing any code, inventory what you have. This prevents missed notifications during cutover.

### Notification Inventory

For each notification your system sends, record:

| Field | Example |
|-------|---------|
| Name / ID | `order-confirmation` |
| Trigger | Order placed event |
| Channels | Email, SMS |
| Template / content source | HTML template in S3, hardcoded string, etc. |
| Provider | SendGrid, Twilio |
| Data / variables | `orderNumber`, `items`, `total` |
| Recipient source | User table, event payload |
| Preferences | User can opt out of marketing; transactional always sent |
| Orchestration | Immediate, delayed, batched, sequenced |

### Questions to Answer

- How many distinct notification types do you send?
- Which providers do you use per channel?
- Where do templates live (code, database, third-party)?
- Do you have orchestration logic (delays, batching, sequences)?
- How are user preferences stored and enforced?
- Do you have multi-tenant / white-label requirements?

## 2. Map to Courier Concepts

| Your System | Courier | Notes |
|-------------|---------|-------|
| Email/SMS/push send function | `client.send.message()` | Single API for all channels |
| User / recipient table | Profiles | `POST /profiles/:id` (merge) — accepts nested JSON |
| Template (HTML, text, etc.) | Templates | Built in Courier Designer or via API (Elemental format) |
| Send queue / orchestration | Automations | Delays, batching, conditions, sequences |
| User preferences / opt-outs | Preference Topics | Enforced automatically at send time |
| Provider config (API keys, etc.) | Integrations | Configured in the Courier dashboard |
| Webhook handlers for status | Courier Webhooks | Delivery, bounce, complaint events |
| Multi-tenant branding | Tenants | Brand attributes live on the Tenant resource |

> Note: `PUT /profiles/:id` is a **full replacement** — any fields not included are deleted. Use `POST` for partial updates; reach for `PUT` only when you deliberately want to wipe unlisted fields.

## 3. Set Up Courier

### Install the SDK

**TypeScript:**
```bash
npm install @trycourier/courier
```

**Python:**
```bash
pip install trycourier
```

### Initialize

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();
```

**Python:**
```python
from courier import Courier

client = Courier()
```

Set `COURIER_API_KEY` in your environment. Use the **Test** environment key during migration.

### Configure Providers

In the [Courier dashboard](https://app.courier.com), connect the same providers you currently use:

| Channel | Common Providers |
|---------|-----------------|
| Email | SendGrid, Amazon SES, Postmark, Mailgun, Resend |
| SMS | Twilio, Vonage, MessageBird, Plivo, Telnyx |
| Push | Firebase Cloud Messaging (FCM), APNs, Expo |
| Chat | Slack, Microsoft Teams, Discord |

You can add multiple providers per channel for automatic failover.

## 4. Migrate Users

Create Courier profiles with the same identifiers your current system uses.

**TypeScript:**
```typescript
await client.profiles.create("user-123", {
  profile: {
    email: "jane@example.com",
    phone_number: "+15551234567",
    name: "Jane Doe",
  },
});
```

**Python:**
```python
client.profiles.create(
    user_id="user-123",
    profile={
        "email": "jane@example.com",
        "phone_number": "+15551234567",
        "name": "Jane Doe",
    },
)
```

For large user sets, use the [Bulk API](https://www.courier.com/docs/api-reference/bulk/create-a-bulk-job) to upsert in batches.

### Device Tokens

If you send push notifications, store device tokens on the profile:

```typescript
await client.users.tokens.addSingle("fcm-token-abc", {
  user_id: "user-123",
  provider_key: "firebase-fcm",
  device: {
    app_id: "com.acme.app",
    platform: "android",
  },
});
```

## 5. Recreate Templates

You have two options for content:

### Option A: Use the Template Designer

Build templates visually in the [Courier Designer](https://www.courier.com/docs/platform/content/template-designer/template-designer-overview). Use `{{variable}}` for dynamic data. Add content blocks for each channel.

### Option B: Send Inline Content

Skip templates entirely and send content inline — useful for simple notifications or when content is generated in code:

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Order Confirmed",
      body: "Your order #{{orderNumber}} has been confirmed.",
    },
    data: { orderNumber: "12345" },
  },
});
```

### Option C: Manage Templates via API

Create and publish templates programmatically using the Notifications API. See [Templates](./templates.md) for the full CRUD lifecycle and Elemental format.

## 6. Migrate Send Calls

Replace your existing send functions with `client.send.message()`.

### Before (Custom System)

```typescript
// Your existing code might look like this
await sendEmail({
  to: user.email,
  template: "order-confirmation",
  data: { orderNumber, items, total },
});

await sendSMS({
  to: user.phone,
  body: `Order #${orderNumber} confirmed!`,
});
```

### After (Courier)

```typescript
await client.send.message({
  message: {
    to: { user_id: user.id },
    template: "nt_01kmrbq6ypf25tsge12qek41r0",
    data: { orderNumber, items, total },
    routing: {
      method: "all",
      channels: ["email", "sms"],
    },
  },
}, {
  headers: { "Idempotency-Key": `order-confirmation-${orderNumber}` },
});
```

Use your own workspace template ID (`nt_...`) for `message.template`; the value above is an example.

One API call replaces separate email and SMS sends. Courier handles provider selection, template rendering, and delivery.

### Multi-Channel Routing

If your old system had custom routing logic (try push, fall back to email), replace it with Courier's routing:

```jsonc
// message.routing fragment on client.send.message
{
  "method": "single",
  "channels": ["push", "email"]
}
```

See [Multi-Channel](./multi-channel.md) for routing strategies, escalation, and provider failover.

## 7. Migrate Orchestration

If your system has delays, sequences, or batching, move that logic to Courier Automations.

| Your System | Courier Automation |
|-------------|-------------------|
| Cron job / delayed queue | Delay step |
| Batch / digest aggregation | Digest step |
| Conditional sends (if user did X) | Condition step |
| Multi-step sequences (onboarding drip) | Automation template with send + delay steps |

```typescript
await client.automations.invoke.invokeByTemplate("onboarding-sequence", {
  recipient: "user-123",
  data: { name: "Jane", plan: "pro" },
});
```

See [Batching](./batching.md) for digest strategies.

## 8. Migrate Preferences

If your system tracks user notification preferences, migrate them to Courier topics.

**TypeScript:**
```typescript
await client.users.preferences.updateOrCreateTopic("marketing-emails", {
  user_id: "user-123",
  topic: {
    status: "OPTED_OUT",
  },
});
```

**Python:**
```python
client.users.preferences.update_or_create_topic(
    "marketing-emails",
    user_id="user-123",
    topic={"status": "OPTED_OUT"},
)
```

Courier enforces preferences automatically at send time — you don't need to check preferences in your application code.

See [Preferences](./preferences.md) for topic structure, categories, and building a preference center.

## 9. Run in Parallel

The safest migration strategy is to run both systems simultaneously:

```
Phase 1: Shadow mode (1-2 weeks)
├── Old system sends to users (production)
└── Courier sends to test addresses only (validation)

Phase 2: Dual send (1 week)
├── Old system sends to users (production)
└── Courier sends to users (production) — monitor for parity

Phase 3: Courier primary (1 week)
├── Courier sends to users (production)
└── Old system as fallback (monitor)

Phase 4: Cutover
└── Courier only
```

### Shadow Mode Pattern

Send to Courier with a test recipient to validate rendering and delivery without affecting users:

```typescript
if (process.env.MIGRATION_PHASE === "shadow") {
  await client.send.message({
    message: {
      to: { email: "notifications-test@yourcompany.com" },
      template: "nt_01kmrbq6ypf25tsge12qek41r0",
      data: { orderNumber, items, total },
    },
  });
}
```

### Dual Send Pattern

Once validated, send through both systems. Use idempotency keys to prevent issues if you accidentally double-send:

```typescript
await client.send.message({
  message: {
    to: { user_id: user.id },
    template: "nt_01kmrbq6ypf25tsge12qek41r0",
    data: { orderNumber, items, total },
  },
}, {
  headers: { "Idempotency-Key": `order-confirmation-${orderNumber}` },
});
```

## 10. Validate and Cut Over

1. Send test messages using your Test environment API key
2. Verify delivery in [Message Logs](https://app.courier.com/logs) — check rendered content, delivery timeline, and provider response
3. Compare delivery rates between old and new systems during dual-send
4. Validate preference enforcement (opted-out users should not receive)
5. Switch to the Production API key
6. Remove old system code
7. Monitor [Analytics](https://www.courier.com/docs/platform/analytics/analytics) for delivery rates and engagement

## Migration Checklist

- [ ] Inventory all notification types
- [ ] Configure providers in Courier dashboard
- [ ] Migrate user profiles (with same IDs)
- [ ] Migrate device tokens for push
- [ ] Create or migrate templates
- [ ] Migrate user preferences
- [ ] Replace send calls with `client.send.message()`
- [ ] Migrate orchestration to Automations
- [ ] Set up webhook handlers for delivery events
- [ ] Run shadow mode and validate
- [ ] Run dual-send and compare
- [ ] Cut over to Courier only
- [ ] Remove old system code

## What's Next

| Goal | Guide |
|------|-------|
| Set up multi-channel routing and fallbacks | [Multi-Channel](./multi-channel.md) |
| Configure user notification preferences | [Preferences](./preferences.md) |
| Build an in-app notification center | [Inbox](../channels/inbox.md) |
| Add idempotency keys and retry logic | [Reliability](./reliability.md) |
| Set up digests and batch notifications | [Batching](./batching.md) |
| Plan notifications for your app type | [Catalog](./catalog.md) |
| Create templates programmatically | [Templates](./templates.md) |

## Related

- [Quickstart](./quickstart.md) - Send your first Courier notification
- [Migrate from Knock](./migrate-from-knock.md) - Platform-specific migration from Knock
- [Migrate from Novu](./migrate-from-novu.md) - Platform-specific migration from Novu
- [Multi-Channel](./multi-channel.md) - Routing, failover, and escalation
- [Reliability](./reliability.md) - Idempotency, retries, and error recovery
- [Patterns](./patterns.md) - Reusable code patterns
