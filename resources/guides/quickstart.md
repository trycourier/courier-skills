# Quickstart

Send your first notification with Courier using the SDK, CLI, or curl.

## Quick Reference

### Rules
- You need a Courier API key from [Settings > API Keys](https://app.courier.com/settings/api-keys)
- Use a test environment key for development (prefixed with `pk_test_`)
- Always use idempotency keys for transactional sends in production
- Check delivery status via the Messages API or Courier dashboard

### Steps
1. Get an API key
2. Install SDK or CLI
3. Send a message
4. Check delivery status

---

## 1. Get an API Key

Create an API key in your [Courier Settings](https://app.courier.com/settings/api-keys). Use a test key for development.

## 2. Install

**TypeScript/Node.js:**

```bash
npm install @trycourier/courier
```

**Python:**

```bash
pip install trycourier
```

**CLI:**

```bash
npm install -g @trycourier/cli
export COURIER_API_KEY="your-api-key"
```

## 3. Send a Message

### TypeScript

```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

const response = await courier.send({
  message: {
    to: { email: "jane@example.com" },
    content: {
      title: "Hello from Courier",
      body: "This is your first notification!"
    }
  }
});

console.log(response.requestId);
```

### Python

```python
from courier.client import Courier

client = Courier()

response = client.send(
    message={
        "to": {"email": "jane@example.com"},
        "content": {
            "title": "Hello from Courier",
            "body": "This is your first notification!",
        },
    }
)

print(response.request_id)
```

### CLI

```bash
courier send message \
  --message.to.email "jane@example.com" \
  --message.content.title "Hello from Courier" \
  --message.content.body "This is your first notification!"
```

### curl

```bash
curl -X POST https://api.courier.com/send \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "to": { "email": "jane@example.com" },
      "content": {
        "title": "Hello from Courier",
        "body": "This is your first notification!"
      }
    }
  }'
```

## 4. Check Delivery Status

Use the `requestId` from the send response to check delivery status.

### TypeScript

```typescript
const message = await courier.messages.retrieve(requestId);
console.log(message.status); // DELIVERED, UNDELIVERABLE, etc.
```

### Python

```python
message = client.messages.get(request_id)
print(message.status)
```

### CLI

```bash
courier messages retrieve --message-id "REQUEST_ID" --format json
```

### curl

```bash
curl https://api.courier.com/messages/REQUEST_ID \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

## 5. Send with a Template

Templates are designed in the [Courier Designer](https://app.courier.com/designer). Reference them by ID or slug:

### TypeScript

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_CONFIRMATION",
    data: { orderId: "12345", total: "$99.00" }
  }
});
```

### Python

```python
client.send(
    message={
        "to": {"user_id": "user-123"},
        "template": "ORDER_CONFIRMATION",
        "data": {"orderId": "12345", "total": "$99.00"},
    }
)
```

### CLI

```bash
courier send message \
  --message.to.user_id "user-123" \
  --message.template "ORDER_CONFIRMATION" \
  --message.data '{"orderId": "12345", "total": "$99.00"}'
```

## What's Next

| Goal | Guide |
|------|-------|
| Send via multiple channels (email, SMS, push) | [Multi-Channel](./multi-channel.md) |
| Add idempotency keys and retry logic | [Reliability](./reliability.md) |
| Manage user notification preferences | [Preferences](./preferences.md) |
| Use the CLI for debugging and agent workflows | [CLI](./cli.md) |
| Build a specific notification type | [Catalog](./catalog.md) |

## Related

- [Email](../channels/email.md) - Email deliverability and SPF/DKIM/DMARC
- [SMS](../channels/sms.md) - SMS compliance and 10DLC
- [Push](../channels/push.md) - Push notification setup
- [Patterns](./patterns.md) - Reusable code patterns
