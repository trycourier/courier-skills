# Migrate from Knock

## Quick Reference

### Rules
- Use Courier's Test environment API key during migration; switch to Production only after validation
- Knock Workflows = Courier Templates (content) + Automations (orchestration) — split them
- Knock Objects don't have a 1:1 equivalent; pass that context via the `data` field on each send
- Knock Feeds map to Courier Inbox — swap `@knocklabs/react` for `@trycourier/courier-react`
- Keep the same `user_id` values when creating Courier profiles to simplify cutover
- Idempotency keys work the same way — keep using them

### Concept Mapping

| Knock | Courier | Notes |
|-------|---------|-------|
| Channels | Integrations | Provider config lives in the Courier dashboard; supports 50+ providers |
| Workflows | Templates + Automations | Content and orchestration are independent resources |
| Recipients / Users | Users / Profiles | Same shape; profiles accept nested JSON |
| Objects | `data` on send | Pass context inline instead of managing a separate entity |
| Preferences (PreferenceSet) | Preferences (topics) | Courier enforces at send time automatically |
| Tenants | Tenants | Branding lives directly on the Tenant resource |
| Feeds (in-app) | Inbox | Drop-in React, iOS, Android, and vanilla JS components |
| Commits | Publish (draft/live) | Edit in draft, publish when ready; published versions are immutable |
| Batch function | Automations (batch/digest step) | Configure window and aggregation in the automation |

### API Mapping

| Operation | Knock | Courier |
|-----------|-------|---------|
| Send a notification | `POST /v1/workflows/:key/trigger` | `POST /send` |
| Create/update a user | `PUT /v1/users/:id` | `POST /profiles/:id` (merge) |
| Get a user | `GET /v1/users/:id` | `GET /profiles/:id` |
| Set user preferences | `PUT /v1/users/:id/preferences/:set_id` | `PUT /users/:id/preferences/:topic` |
| Get message status | `GET /v1/messages/:id` | `GET /messages/:id` |
| List messages | `GET /v1/messages` | `GET /messages` |
| Bulk send | `POST /v1/workflows/:key/trigger` (recipients array) | `POST /bulk` |
| Create/update tenant | `PUT /v1/objects/tenants/:id` (Knock models tenants as Objects) | `PUT /tenants/:id` |

> Note: `PUT /profiles/:id` is a **full replacement** — any fields not included are deleted. Use `POST` for partial updates; reach for `PUT` only when you deliberately want to wipe unlisted fields.

### Common Mistakes
- Trying to recreate Knock Objects as a first-class Courier resource (use `data` instead)
- Copying a Knock Workflow into a single Courier resource (split content into a Template, orchestration into an Automation)
- Forgetting to configure provider integrations in the dashboard before sending
- Migrating to Production keys before validating delivery in the Test environment
- Not migrating user preferences (users lose their opt-out choices)

---

Migrate your notification infrastructure from Knock to Courier. This guide provides side-by-side code examples so you can translate Knock SDK calls to Courier equivalents. For the full official walkthrough, see [Courier's migration docs](https://www.courier.com/docs/tutorials/migrate/from-knock).

## 1. Swap the SDK

### TypeScript / Node.js

**Before (Knock):**
```bash
npm install @knocklabs/node
```

**After (Courier):**
```bash
npm install @trycourier/courier
```

### Python

**Before (Knock):**
```bash
pip install knockapi
```

**After (Courier):**
```bash
pip install trycourier
```

## 2. Initialize the Client

### TypeScript

**Before (Knock):**
```typescript
import Knock from "@knocklabs/node";

const knock = new Knock(process.env.KNOCK_API_KEY);
```

**After (Courier):**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();
```

> Both `import Courier from "@trycourier/courier"` (default export) and `import { Courier } from "@trycourier/courier"` (named export) work — the named export is `Courier`, not `CourierClient`. The examples in this guide use the default export.

### Python

**Before (Knock):**
```python
from knockapi import Knock

knock = Knock(api_key="sk_...")
```

**After (Courier):**
```python
from courier import Courier

client = Courier()
```

## 3. Configure Integrations

In the Courier dashboard, connect the same providers you use in Knock (SendGrid, Twilio, FCM, etc.). Each provider maps to a channel type.

You can add multiple providers per channel type for automatic failover — if your primary email provider goes down, the backup takes over without code changes.

If you use Knock's in-app feed, enable [Courier Inbox](https://www.courier.com/docs/platform/inbox/inbox-overview). No external provider is needed.

## 4. Recreate Templates

Knock bundles content and delivery logic into Workflows. In Courier, split them:

1. Create a **Template** in the [Designer](https://www.courier.com/docs/platform/content/template-designer/template-designer-overview) for the content (email body, SMS text, push title/body)
2. Use `{{variable}}` syntax for dynamic data — same Handlebars-style as Knock
3. Add content blocks for each channel the notification should support
4. If your Knock Workflow has delays, conditions, or batching, create a separate **Automation** for the orchestration logic

## 5. Migrate Users

Create Courier profiles with the same identifiers you use in Knock.

### TypeScript

**Before (Knock):**
```typescript
// Current Knock Node SDK uses users.update (the older users.identify helper
// was removed; update is an upsert-by-ID).
await knock.users.update("user-123", {
  email: "jane@example.com",
  phone_number: "+15551234567",
  name: "Jane Doe",
});
```

**After (Courier):**
```typescript
await client.profiles.create("user-123", {
  profile: {
    email: "jane@example.com",
    phone_number: "+15551234567",
    name: "Jane Doe",
    plan: "enterprise",
  },
});
```

### Python

**Before (Knock):**
```python
# Current Knock Python SDK uses users.update (upsert by ID).
knock.users.update("user-123", data={
    "email": "jane@example.com",
    "phone_number": "+15551234567",
    "name": "Jane Doe",
})
```

**After (Courier):**
```python
client.profiles.create(
    user_id="user-123",
    profile={
        "email": "jane@example.com",
        "phone_number": "+15551234567",
        "name": "Jane Doe",
        "plan": "enterprise",
    },
)
```

### Bulk Migration

For large user sets, use the [Bulk API](https://www.courier.com/docs/api-reference/bulk/create-a-bulk-job) to upsert users in batches instead of one-by-one calls.

## 6. Update Send Calls

### TypeScript

**Before (Knock):**
```typescript
await knock.workflows.trigger("welcome-email", {
  recipients: ["user-123"],
  data: {
    name: "Jane Doe",
    action_url: "https://app.example.com",
  },
});
```

**After (Courier):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbw4q7x1v5d8c2n6w9hj",
    data: {
      name: "Jane Doe",
      action_url: "https://app.example.com",
    },
  },
});
```

### Python

**Before (Knock):**
```python
knock.workflows.trigger("welcome-email",
    recipients=["user-123"],
    data={
        "name": "Jane Doe",
        "action_url": "https://app.example.com",
    },
)
```

**After (Courier):**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbw4q7x1v5d8c2n6w9hj",
        "data": {
            "name": "Jane Doe",
            "action_url": "https://app.example.com",
        },
    }
)
```

### Multi-Channel Routing

Knock embeds channel steps inside workflows. In Courier, specify routing on the send call or in the template:

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: { orderNumber: "12345", trackingUrl: "https://acme.co/track/12345" },
    routing: {
      method: "single",
      channels: ["email", "push", "sms"],
    },
  },
});
```

See [Multi-Channel](./multi-channel.md) for routing strategies, escalation patterns, and provider failover.

## 7. Migrate Preferences

Knock's `PreferenceSet` maps to Courier preference topics. Courier enforces preferences automatically at send time.

### TypeScript

**Before (Knock):**
```typescript
await knock.users.setPreferences("user-123", {
  channel_types: { email: true, sms: false },
  workflows: { "weekly-digest": false },
});
```

**After (Courier):**
```typescript
await client.users.preferences.updateOrCreateTopic("weekly-digest", {
  user_id: "user-123",
  topic: {
    status: "OPTED_OUT",
    has_custom_routing: true,
    custom_routing: ["email"],
  },
});
```

### Hosted Preference Page

Courier provides a [hosted preference page](https://www.courier.com/docs/platform/preferences/hosted-page) you can deploy in minutes, plus embeddable [React components](https://www.courier.com/docs/platform/preferences/embedding-preferences) for building a preference center directly into your app.

See [Preferences](./preferences.md) for topic structure, category defaults, and implementation patterns.

## 8. Migrate In-App Feeds to Inbox

Knock Feeds become Courier Inbox. Swap the React package and component:

### Installation

**Before (Knock):**
```bash
npm install @knocklabs/react
```

**After (Courier):**
```bash
npm install @trycourier/courier-react
```

### React Component

**Before (Knock):**
```tsx
import { KnockProvider, NotificationFeedPopover } from "@knocklabs/react";

function App() {
  return (
    <KnockProvider apiKey="pk_..." userId="user-123">
      <NotificationFeedPopover />
    </KnockProvider>
  );
}
```

**After (Courier v8):**
```tsx
import { useEffect } from "react";
import { CourierInbox, useCourier } from "@trycourier/courier-react";

function App() {
  const courier = useCourier();

  useEffect(() => {
    fetch("/api/courier-token")
      .then((res) => res.json())
      .then((data) => {
        courier.shared.signIn({ userId: "user-123", jwt: data.token });
      });
  }, []);

  return <CourierInbox />;
}
```

v8 uses JWT authentication (not client keys), `CourierInbox` (not `Inbox`), and `useCourier()` for auth. See [Inbox](../channels/inbox.md) for full setup, theming, feeds/tabs, and mobile SDK options.

## 9. Migrate Orchestration Logic

Knock workflow steps (batch, delay, conditions) map to Courier Automations:

| Knock Step | Courier Equivalent |
|------------|-------------------|
| Batch function | Automation batch/digest step |
| Delay step | Automation delay step |
| Branch/condition step | Automation condition step |
| Channel step | Automation send step (references a Template) |

### Batch Example

**Before (Knock):** Batch function configured inside the workflow with a window and batch key.

**After (Courier):**
```typescript
await client.automations.invoke.invokeByTemplate("social-activity-batch", {
  recipient: "user-123",
  data: {
    event_type: "like",
    actor_name: "Jane",
    target_id: "post-789",
  },
});
```

Configure the automation in the Courier dashboard:
1. **Batch step:** Collect events for 5 minutes, keyed by `target_id`
2. **Send step:** Reference a template that uses aggregated batch data

See [Batching](./batching.md) for window strategies, aggregation patterns, and digest implementation.

## 10. Migrate Tenants

Tenants work similarly across both platforms. In Courier, branding attributes live directly on the Tenant resource instead of a separate Brands object.

```typescript
// `update` is create-or-replace (PUT /tenants/{id}). Brands live in the Brands API;
// tenants reference a brand via `brand_id`.
await client.tenants.update("acme-corp", {
  name: "Acme Corp",
  brand_id: "BRAND_ACME", // optional
});

await client.send.message({
  message: {
    to: { user_id: "user-123", tenant_id: "acme-corp" },
    template: "nt_01kmrbw4q7x1v5d8c2n6w9hj",
    data: { name: "Jane Doe" },
  },
});
```

## 11. Test and Cut Over

1. Send test messages using your Test environment API key
2. Verify delivery in [Message Logs](https://app.courier.com/logs) — check rendered content, delivery timeline, and provider response
3. Validate that preferences, routing, and template rendering match your Knock setup
4. Switch to the Production API key
5. Monitor [Analytics](https://www.courier.com/docs/platform/analytics/analytics) for delivery rates and engagement

## What's Next

| Goal | Guide |
|------|-------|
| Set up multi-channel routing and fallbacks | [Multi-Channel](./multi-channel.md) |
| Configure user notification preferences | [Preferences](./preferences.md) |
| Build an in-app notification center | [Inbox](../channels/inbox.md) |
| Add idempotency keys and retry logic | [Reliability](./reliability.md) |
| Set up digests and batch notifications | [Batching](./batching.md) |
| Plan notifications for your app type | [Catalog](./catalog.md) |

## Related

- [Quickstart](./quickstart.md) - Send your first Courier notification
- [Multi-Channel](./multi-channel.md) - Routing, failover, and escalation
- [Preferences](./preferences.md) - Preference topics and opt-out handling
- [Inbox](../channels/inbox.md) - In-app notification center
- [Batching](./batching.md) - Digest and batch strategies
- [Reliability](./reliability.md) - Idempotency, retries, and error recovery
- [Patterns](./patterns.md) - Reusable code patterns
