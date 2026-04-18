# Migrate from Novu

## Quick Reference

### Rules
- Use Courier's Test environment API key during migration; switch to Production only after validation
- Novu Workflows = Courier Templates (content) + Automations (orchestration) — split them
- Novu's code-first `@novu/framework` workflows don't have a 1:1 equivalent; extract content into Templates and orchestration into Automations
- Novu Inbox (`@novu/react`) maps to Courier Inbox — swap for `@trycourier/courier-react`
- Keep the same `subscriberId` values as Courier `user_id` to simplify cutover
- Idempotency keys work the same way — keep using them

### Concept Mapping

| Novu | Courier | Notes |
|------|---------|-------|
| Workflows (code-first via `@novu/framework`) | Templates + Automations | Content and orchestration are independent resources |
| Events API / `novu.trigger()` | `POST /send` | Different payload shape; `subscriberId` becomes `user_id` |
| Subscribers | Users / Profiles | Courier profiles accept nested JSON for custom data |
| Subscriber credentials (deviceTokens, webhookUrl) | Profile channel tokens | Stored directly on the Courier profile |
| Topics | Subscription Topics / Lists | Topics for broadcast fan-out; lists for static subscriber groups |
| Tenants | Tenants | Branding lives directly on the Courier Tenant resource |
| Digest step | Automations batch/digest step | Configure window and aggregation in the automation |
| Delay step | Automation delay step | Same concept |
| Custom step | Fetch Data node or condition logic | No direct equivalent; use automation nodes |
| Inbox (`@novu/react`, `NovuProvider`) | Inbox (`@trycourier/courier-react`, `CourierInbox`) | v8 uses JWT auth and `useCourier()` hook; both offer headless mode |
| Subscriber preferences | Preferences (topics) | Courier enforces at send time automatically |
| Environments (dev/production) | Test/Production keys | Courier uses separate API keys per environment; copy from [Settings > API Keys](https://app.courier.com/settings/api-keys) |

### API Mapping

| Operation | Novu | Courier |
|-----------|------|---------|
| Send a notification | `POST /v1/events/trigger` | `POST /send` |
| Create/update a subscriber | `POST /v2/subscribers` | `POST /profiles/:id` (merge) |
| Get a subscriber | `GET /v2/subscribers/:id` | `GET /profiles/:id` |
| Set subscriber preferences | `PATCH /v2/subscribers/:id/preferences` | `PUT /users/:id/preferences/:topic` |
| Get message status | `GET /messages/:id` | `GET /messages/:id` |
| List messages | `GET /messages` | `GET /messages` |
| Broadcast to topic | `POST /v1/events/trigger` (with `topics`) | `POST /send` (with list/audience) |
| Create/update tenant | `POST /v1/tenants` | `PUT /tenants/:id` |
| Bulk send | Topic trigger (fan-out) | `POST /bulk` |

> Note: `PUT /profiles/:id` is a **full replacement** — any fields not included are deleted. Use `POST` for partial updates; reach for `PUT` only when you deliberately want to wipe unlisted fields.

### Common Mistakes
- Trying to replicate Novu's code-first workflow definitions (`@novu/framework`) as a single Courier resource (split content into a Template, orchestration into an Automation)
- Using `subscriberId` in Courier send calls instead of mapping it to `user_id`
- Forgetting to configure provider integrations in the Courier dashboard before sending
- Not migrating subscriber preferences (users lose their opt-out choices)
- Migrating to Production keys before validating delivery in the Test environment
- Expecting Novu's topic fan-out to work identically (use Courier Lists or subscription topics instead)

---

Migrate your notification infrastructure from Novu to Courier. This guide provides side-by-side code examples so you can translate Novu SDK calls to Courier equivalents. For the full official walkthrough, see [Courier's migration docs](https://www.courier.com/docs/tutorials/migrate/from-novu).

## 1. Swap the SDK

### TypeScript / Node.js

**Before (Novu):**
```bash
# If using the legacy SDK:
npm install @novu/node
# Or the newer SDK:
npm install @novu/api
```

**After (Courier):**
```bash
npm install @trycourier/courier
```

### Python

**Before (Novu):**
```bash
# If using the legacy SDK:
pip install novu
# Or the newer SDK:
pip install novu-py
```

**After (Courier):**
```bash
pip install trycourier
```

## 2. Initialize the Client

### TypeScript

**Before (Novu — `@novu/api`):**
```typescript
import { Novu } from "@novu/api";

const novu = new Novu({ secretKey: process.env.NOVU_SECRET_KEY });
```

**Before (Novu — `@novu/node`):**
```typescript
import { Novu } from "@novu/node";

const novu = new Novu(process.env.NOVU_SECRET_KEY);
```

**After (Courier):**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();
```

### Python

**Before (Novu — `novu-py`):**
```python
from novu_py import Novu

novu = Novu(secret_key="sk_...")
```

**Before (Novu — legacy `novu` SDK, pseudocode):**
```python
# The legacy `novu` Python SDK used an EventApi class. Real usage requires
# passing the secret key; this snippet is pseudocode for shape only.
from novu.api import EventApi

event_api = EventApi(url="https://api.novu.co", api_key="sk_...")
event_api.trigger(
    name="welcome-email",
    recipients="user-123",
    payload={"name": "Jane Doe"},
)
```

**After (Courier):**
```python
from courier import Courier

client = Courier()
```

## 3. Configure Integrations

In the Courier dashboard, connect the same providers you use in Novu (SendGrid, Twilio, FCM, etc.). Each provider maps to a channel type.

You can add multiple providers per channel type for automatic failover — if your primary email provider goes down, the backup takes over without code changes.

If you use Novu's Inbox component, enable [Courier Inbox](https://www.courier.com/docs/platform/inbox/inbox-overview). No external provider is needed.

## 4. Recreate Templates

Novu bundles content, routing, and orchestration into code-first Workflows (via `@novu/framework`) or the dashboard workflow editor. In Courier, split them:

1. Create a **Template** in the [Designer](https://www.courier.com/docs/platform/content/template-designer/template-designer-overview) for the content (email body, SMS text, push title/body)
2. Use `{{variable}}` syntax for dynamic data — same Handlebars-style as Novu
3. Add content blocks for each channel the notification should support
4. If your Novu Workflow has digest, delay, or condition steps, create a separate **Automation** for the orchestration logic

### Novu Step → Courier Equivalent

| Novu Workflow Step | Courier Equivalent |
|--------------------|-------------------|
| Channel step (email, sms, push, chat, in-app) | Automation send step (references a Template) |
| Digest step | Automation digest node |
| Delay step | Automation delay node |
| Custom step | Fetch Data node or condition logic |

## 5. Migrate Subscribers

Create Courier profiles with the same identifiers you use as `subscriberId` in Novu.

### TypeScript

**Before (Novu):**
```typescript
await novu.subscribers.create({
  subscriberId: "user-123",
  email: "jane@example.com",
  phone: "+15551234567",
  firstName: "Jane",
  lastName: "Doe",
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

**Before (Novu):**
```python
novu.subscribers.create(
    subscriber_id="user-123",
    email="jane@example.com",
    phone="+15551234567",
    first_name="Jane",
    last_name="Doe",
)
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

### Device Tokens and Webhooks

Novu stores push device tokens and chat webhook URLs as subscriber credentials. In Courier:

- **Push device tokens** are a first-class resource. Register them with `client.users.tokens.addSingle(token, { user_id, provider_key, device })` — not as a profile field. This way Courier can manage per-device routing, token refresh, and invalidation. See [push.md](../channels/push.md) and [SKILL.md](../../SKILL.md) for the canonical shape.
- **Chat webhooks / Slack / Teams credentials** live on the profile (`slack`, `ms_teams`, `discord`, etc.) so template routing can pick them up automatically.

```typescript
await client.users.tokens.addSingle("fcm-device-token-here", {
  user_id: "user-123",
  provider_key: "firebase-fcm",
  device: { app_id: "com.acme.app", platform: "android" },
});

await client.profiles.create("user-123", {
  profile: {
    email: "jane@example.com",
    slack: { access_token: "xoxb-...", channel: "C01234" },
  },
});
```

```python
client.users.tokens.add_single(
    token="fcm-device-token-here",
    user_id="user-123",
    provider_key="firebase-fcm",
    device={"app_id": "com.acme.app", "platform": "android"},
)

client.profiles.create(
    user_id="user-123",
    profile={
        "email": "jane@example.com",
        "slack": {"access_token": "xoxb-...", "channel": "C01234"},
    },
)
```

> For iOS (APNs), set `provider_key: "apn"`. See [push.md](../channels/push.md) for the full provider-key table.

### Bulk Migration

For large subscriber sets, use the [Bulk API](https://www.courier.com/docs/api-reference/bulk/create-a-bulk-job) to upsert users in batches instead of one-by-one calls.

## 6. Update Send Calls

### TypeScript

**Before (Novu — `@novu/api`, current SDK):**
```typescript
import { Novu } from "@novu/api";

const novu = new Novu({ secretKey: process.env.NOVU_SECRET_KEY! });

await novu.trigger({
  workflowId: "welcome-email",
  to: [{ subscriberId: "user-123" }],
  payload: {
    name: "Jane Doe",
    action_url: "https://app.example.com",
  },
});
```

**Before (Novu — `@novu/node`, legacy SDK):**
```typescript
import { Novu } from "@novu/node";

const novu = new Novu(process.env.NOVU_API_KEY!);

await novu.trigger("welcome-email", {
  to: { subscriberId: "user-123" },
  payload: {
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

**Before (Novu — `novu-py`, current SDK):**
```python
from novu_py import Novu
from novu_py.models import TriggerEventRequestDto

novu = Novu(secret_key="sk_...")

novu.trigger(trigger_event_request_dto=TriggerEventRequestDto(
    workflow_id="welcome-email",
    to={"subscriber_id": "user-123"},
    payload={
        "name": "Jane Doe",
        "action_url": "https://app.example.com",
    },
))
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

Novu embeds channel steps inside workflows. In Courier, specify routing on the send call or in the template:

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

Novu's subscriber preferences (per-workflow and per-channel) map to Courier preference topics. Courier enforces preferences automatically at send time.

### Read preferences

**Before (Novu):**
```typescript
const prefs = await novu.subscribers.getPreferences("user-123");
```

**After (Courier) — TypeScript:**
```typescript
const prefs = await client.users.preferences.retrieve("user-123");
```

**After (Courier) — Python:**
```python
prefs = client.users.preferences.retrieve("user-123")
```

### Update a topic preference

Novu's per-workflow/per-channel preference writes map to Courier's `updateOrCreateTopic`. This is a separate call from reading — there is no single "set all preferences" API.

**TypeScript:**
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

**Python:**
```python
client.users.preferences.update_or_create_topic(
    "weekly-digest",
    user_id="user-123",
    topic={
        "status": "OPTED_OUT",
        "has_custom_routing": True,
        "custom_routing": ["email"],
    },
)
```

### Hosted Preference Page

Courier provides a [hosted preference page](https://www.courier.com/docs/platform/preferences/hosted-page) you can deploy in minutes, plus embeddable [React components](https://www.courier.com/docs/platform/preferences/embedding-preferences) for building a preference center directly into your app.

See [Preferences](./preferences.md) for topic structure, category defaults, and implementation patterns.

## 8. Migrate In-App Inbox

Novu Inbox becomes Courier Inbox. Swap the React package and component:

### Installation

**Before (Novu):**
```bash
npm install @novu/react
```

**After (Courier):**
```bash
npm install @trycourier/courier-react
```

### React Component

**Before (Novu):**
```tsx
import { NovuProvider, Inbox } from "@novu/react";

function App() {
  return (
    <NovuProvider applicationIdentifier="APP_ID" subscriberId="user-123">
      <Inbox />
    </NovuProvider>
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

### Headless Mode

Both platforms offer headless mode for custom UI. In Courier, use the headless hooks from `@trycourier/courier-react` or the vanilla JS client for non-React frameworks.

## 9. Migrate Topics to Lists

Novu Topics let you broadcast to subscriber groups with a single trigger. In Courier, use Lists or Audiences:

### TypeScript

**Before (Novu):**
```typescript
await novu.trigger({
  workflowId: "product-update",
  to: [{ type: "Topic", topicKey: "beta-users" }],
  payload: { feature: "Dark mode is here" },
});
```

**After (Courier):**
```typescript
await client.send.message({
  message: {
    to: { list_id: "beta-users" },
    template: "nt_01kmrbzc8x2q6v1d4c7n5j9ht",
    data: { feature: "Dark mode is here" },
  },
});
```

Manage list membership via the API:

```typescript
// Additive single-user subscribe. The list is auto-created if it doesn't exist.
await client.lists.subscriptions.subscribeUser("user-123", { list_id: "beta-users" });
```

For attribute-based targeting (e.g., all users on the enterprise plan), use [Audiences](https://www.courier.com/docs/platform/users/audiences) instead of lists.

## 10. Migrate Orchestration Logic

Novu workflow steps (digest, delay, conditions) map to Courier Automations:

| Novu Step | Courier Equivalent |
|-----------|--------------------|
| Digest step | Automation digest node |
| Delay step | Automation delay node |
| Condition / filter | Automation condition node |
| Channel step | Automation send node (references a Template) |

### Digest Example

**Before (Novu):** Digest step configured inside the workflow with `amount`, `unit`, and optional `digestKey`.

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
1. **Digest step:** Collect events for 5 minutes, keyed by `target_id`
2. **Send step:** Reference a template that uses aggregated batch data

See [Batching](./batching.md) for window strategies, aggregation patterns, and digest implementation.

## 11. Migrate Tenants

Tenants work similarly across both platforms. In Novu, tenant data is passed during trigger and available in templates as `{{ tenant.data.* }}`. In Courier, branding attributes live directly on the Tenant resource.

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

## 12. Test and Cut Over

1. Send test messages using your Test environment API key
2. Verify delivery in [Message Logs](https://app.courier.com/logs) — check rendered content, delivery timeline, and provider response
3. Validate that preferences, routing, and template rendering match your Novu setup
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
