# SMS Channel

## Quick Reference

### Rules
- Message length: 160 chars (GSM-7) or 70 chars (Unicode/emoji)
- MUST include sender ID at start: "Acme: Your message..."
- Phone numbers MUST be E.164 format: +15551234567
- US A2P messaging REQUIRES 10DLC registration (allow 2-4 weeks)
- Marketing SMS requires express written consent (TCPA)
- MUST support STOP keyword for opt-out
- Honor opt-outs immediately - no exceptions
- TCPA violations: $500-$1,500 per message
- Transactional SMS (no explicit consent needed): OTP, order updates, appointments
- Marketing SMS (explicit consent required): promotions, sales, re-engagement

### Common Mistakes
- Using emojis without accounting for 70-char Unicode limit
- Forgetting sender identification at start of message
- Not validating phone numbers before storing
- Storing phone numbers without E.164 format
- Sending marketing SMS without consent record
- Missing 10DLC registration (messages filtered/blocked, <10% delivery)
- Including URL shorteners like bit.ly (triggers carrier spam filters)
- Sending during quiet hours (10pm-8am local time)
- Not including opt-out instructions in marketing messages

### Templates

**OTP Code:**
```typescript
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    content: {
      body: "Your Acme code is 847293. Expires in 10 min. Never share this code."
    }
  }
});
```

**Order Shipped:**
```typescript
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    content: {
      body: "Acme: Order #12345 shipped! Arrives Thu. Track: acme.co/t/12345"
    }
  }
});
```

**With Fallback to Email:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "OTP_CODE",
    routing: {
      method: "single",
      channels: ["sms", "email"]
    }
  }
});
```

---

Best practices for sending SMS messages that comply with regulations and engage users.

## Compliance Requirements

### TCPA (United States)

The Telephone Consumer Protection Act requires:

| Requirement | Details |
|-------------|---------|
| Express written consent | Required for marketing SMS |
| Clear disclosure | Message frequency and data rates |
| Easy opt-out | STOP keyword must work |
| Honor opt-outs | Immediately, no exceptions |

**Violations:** $500-$1,500 per message. See [Compliance](../guides/compliance.md) for full penalty details.

### 10DLC Registration (US)

**Required** for A2P (Application-to-Person) SMS in the US since 2023.

| Step | Timeline |
|------|----------|
| 1. Register brand with TCR | 1-2 days |
| 2. Register campaign use case | 1-3 days |
| 3. Carrier vetting | 1-3 weeks |
| 4. Connect to Courier | Same day |

**Without 10DLC:** Messages filtered or blocked by carriers (delivery rates can drop to <10%)

**Use Cases (TCR categories):**
- 2FA/OTP Authentication
- Account Notifications
- Customer Care
- Delivery Notifications
- Marketing (requires additional vetting)

### International Considerations

| Region | Key Requirements |
|--------|-----------------|
| EU (GDPR) | Explicit opt-in, easy withdrawal |
| Canada (CASL) | Express consent, identification |
| UK | PECR + GDPR applies |
| Australia | Spam Act 2003, consent required |
| India | DND registry, templates required |

## Message Design

### Character Limits

| Encoding | Limit | Characters |
|----------|-------|------------|
| GSM-7 | 160 chars | A-Z, 0-9, basic punctuation, common symbols |
| Unicode | 70 chars | Emojis, non-Latin characters, special symbols |

**Concatenation:** Messages over limit split into segments (160/70 chars each), billed as multiple messages.

```
Message: "Your verification code is 847293. Valid for 10 min." 
Length: 51 characters (GSM-7)
Segments: 1
```

### Message Structure

```
[Brand]: [Message]. [CTA]. [Opt-out]

Example:
Acme: Your order #12345 shipped! Track: acme.co/t/12345. Reply STOP to unsubscribe
```

| Component | Purpose |
|-----------|---------|
| Brand identifier | Required for recognition and compliance |
| Core message | What you're telling them |
| CTA/Link | What they should do (use URL shortener) |
| Opt-out | Required for marketing, good practice for all |

### Examples

**Good:**
```
Acme: Your verification code is 847293. Expires in 10 min. Never share this code.
```

```
Acme: Order #12345 shipped! Arrives Thu Jan 30. Track: acme.co/t/12345
```

```
Acme: Your appt with Dr. Smith is tomorrow at 2pm. Reply Y to confirm, N to cancel.
```

**Bad:**
```
Hey! Your awesome order is on the way!!! 🎉🎉🎉 Can't wait for you to get it!!!
```
(Too long, wastes characters on enthusiasm, uses Unicode reducing limit)

## Courier Integration

### Basic SMS Send

```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

// Direct send with phone number
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    content: {
      body: "Your Acme verification code is: 847293. Expires in 10 min."
    }
  }
});
```

### Using Templates

```typescript
// Send via user profile (phone must be in profile)
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_SHIPPED",
    data: {
      orderNumber: "12345",
      trackingUrl: "https://acme.co/t/12345"
    },
    routing: {
      method: "single",
      channels: ["sms"]
    }
  }
});
```

### OTP Pattern

```typescript
async function sendOTP(phoneNumber: string) {
  const code = generateSecureCode(6); // 6-digit numeric
  const expiresAt = Date.now() + 10 * 60 * 1000; // 10 minutes
  
  // Store OTP for verification
  await storeOTP(phoneNumber, code, expiresAt);
  
  // Send via Courier
  await courier.send({
    message: {
      to: { phone_number: phoneNumber },
      content: {
        body: `Your Acme code is ${code}. Expires in 10 min. Never share this code.`
      }
    }
  }, {
    idempotencyKey: `otp-${phoneNumber}-${Date.now()}`
  });
}
```

### SMS with Fallback to Email

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "VERIFICATION_CODE",
    data: { code: "847293" },
    routing: {
      method: "single",
      channels: ["sms", "email"] // Try SMS first, email if fails
    }
  }
});
```

## Phone Number Management

### Validation

```typescript
import { parsePhoneNumber, isValidPhoneNumber } from 'libphonenumber-js';

function validateAndFormat(phone: string, defaultCountry = 'US'): string | null {
  try {
    if (!isValidPhoneNumber(phone, defaultCountry)) {
      return null;
    }
    const parsed = parsePhoneNumber(phone, defaultCountry);
    return parsed.format('E.164'); // +15551234567
  } catch {
    return null;
  }
}

// Always store in E.164 format
const formatted = validateAndFormat('555-123-4567', 'US');
// Result: "+15551234567"
```

### Store in User Profile

```typescript
await courier.users.update("user-123", {
  profile: {
    phone_number: "+15551234567" // E.164 format
  }
});
```

## Opt-In Collection

### Consent Language Example

```html
<label>
  <input type="checkbox" name="sms_consent" required>
  I agree to receive order updates and notifications via SMS to the phone number 
  provided. Message frequency varies. Message and data rates may apply. 
  Reply STOP to unsubscribe, HELP for help. 
  <a href="/privacy">Privacy Policy</a> | <a href="/sms-terms">SMS Terms</a>
</label>
```

See [Compliance](../guides/compliance.md) for full consent requirements, record-keeping, and regional variations.

### Store Consent Record

```typescript
interface SMSConsent {
  phoneNumber: string;
  consentedAt: Date;
  method: 'web_form' | 'sms_keyword' | 'verbal';
  ipAddress?: string;
  consentText: string;
  categories: string[]; // ['transactional', 'marketing']
}

await storeConsent({
  phoneNumber: "+15551234567",
  consentedAt: new Date(),
  method: 'web_form',
  ipAddress: req.ip,
  consentText: "I agree to receive order updates via SMS...",
  categories: ['transactional']
});
```

## Opt-Out Handling

### Standard Keywords

| Keyword | Action | Response |
|---------|--------|----------|
| STOP, UNSUBSCRIBE, CANCEL, END, QUIT | Unsubscribe | "You've been unsubscribed. Reply START to resubscribe." |
| HELP, INFO | Help message | "Acme SMS. Msg freq varies. Msg&data rates apply. Reply STOP to cancel." |
| START, YES, UNSTOP | Resubscribe | "You've been resubscribed. Reply STOP to unsubscribe." |

Most SMS providers handle these automatically. Courier processes opt-outs and updates user preferences.

### Handle in Your App

```typescript
// Webhook from Courier for opt-out events
app.post('/webhooks/sms-optout', async (req, res) => {
  const { phone_number, action } = req.body;
  
  if (action === 'unsubscribe') {
    await updateUserPreference(phone_number, 'sms', false);
  } else if (action === 'resubscribe') {
    await updateUserPreference(phone_number, 'sms', true);
  }
  
  res.sendStatus(200);
});
```

## Number Types

| Type | Throughput | Best For | Notes |
|------|------------|----------|-------|
| **10DLC** | 15-75 msg/sec | Standard A2P messaging | Required for US business SMS |
| **Toll-Free** | 3-10 msg/sec | Customer support | Must be verified |
| **Short Code** | 100+ msg/sec | High-volume campaigns | $500-1500/month, 8-12 week setup |
| **Alphanumeric Sender** | Varies | Branded sender ID | Not supported in US/Canada |

### When to Use Short Codes

- Volume exceeds 100,000 messages/day
- Marketing campaigns with opt-in
- Time-sensitive mass notifications
- Need vanity number (e.g., 12345, ACME)

## Deliverability

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Messages blocked | No 10DLC registration | Complete registration |
| Low delivery rate | Carrier filtering | Review content, avoid spam patterns |
| Delayed delivery | Carrier congestion | Use short code for time-sensitive |
| Number blacklisted | Complaints | Review consent practices |

### Carrier Filtering Triggers

Avoid these patterns:
- URL shorteners (bit.ly, etc.) - use branded short domains
- All caps or excessive punctuation
- Spam keywords ("FREE", "ACT NOW", "LIMITED TIME")
- High-frequency sends to same number
- Messages without brand identification

### Monitor Delivery

```typescript
// Track delivery via webhooks
app.post('/webhooks/courier', async (req, res) => {
  const { event, messageId, channel, error } = req.body;
  
  if (channel === 'sms') {
    if (event === 'delivered') {
      await recordDelivery(messageId, 'delivered');
    } else if (event === 'undelivered') {
      await recordDelivery(messageId, 'failed', error);
      // Investigate if failure rate > 5%
    }
  }
  
  res.sendStatus(200);
});
```

## Timing Considerations

### Quiet Hours

Don't send SMS between 10 PM - 8 AM local time (unless urgent/transactional).

```typescript
function isQuietHours(timezone: string): boolean {
  const now = new Date();
  const localHour = parseInt(
    now.toLocaleString('en-US', { timeZone: timezone, hour: 'numeric', hour12: false })
  );
  return localHour >= 22 || localHour < 8;
}

async function sendSMSRespectingQuietHours(userId: string, message: string, urgent = false) {
  const user = await getUser(userId);
  
  if (!urgent && isQuietHours(user.timezone)) {
    await queueForMorning(userId, message);
  } else {
    await sendImmediately(userId, message);
  }
}
```

## Related

- [Compliance](../guides/compliance.md) - Detailed TCPA and consent requirements
- [Authentication](../transactional/authentication.md) - OTP and 2FA patterns
- [Multi-Channel](../guides/multi-channel.md) - SMS in fallback chains
- [Throttling](../guides/throttling.md) - SMS rate limiting
- [WhatsApp](./whatsapp.md) - Alternative mobile channel
