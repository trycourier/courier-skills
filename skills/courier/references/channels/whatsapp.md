# WhatsApp Channel

## Quick Reference

### Rules
- Courier sends WhatsApp through Twilio. The provider key is `twilio-whatsapp`
- Connect it under Integrations with a Twilio Account SID, Auth Token and a WhatsApp-enabled From number
- Every send needs a Twilio Content SID (`HX...`). Set it in the template's WhatsApp channel settings, or per send at `providers["twilio-whatsapp"].override.body.ContentSid`. Without one, the send fails with `No Content SID specified.`
- Outside the 24-hour window, the Content SID must belong to a template WhatsApp approved. Submit it in the Twilio Console
- Inside the window, unapproved text, media, quick-reply and list-picker content can go out, but it still needs a Content SID
- Phone numbers go in `phone_number`, in E.164: `+15551234567`
- Template categories: Marketing, Authentication, Utility. WhatsApp is likely to reject any other category
- Content template variables are numbered: `{{1}}`, `{{2}}`, `{{3}}`
- WhatsApp requires an explicit opt-in from each user before you message them

### Common Mistakes
- No Content SID on the send, either on the template's WhatsApp channel or in the override
- Unapproved content outside the 24-hour window
- Meta Cloud API shapes (`interactive`, `header.image.link`) in an override. Courier calls Twilio, not Meta
- Phone number not in E.164 format
- Picking a category other than Marketing, Authentication or Utility
- Promotional content in a Utility template (rejected)

### Templates

**Send Template Message (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { phone_number: "+15551234567" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: { customerName: "Jane", orderNumber: "12345", deliveryDate: "Jan 30" },
    routing: { method: "single", channels: ["twilio-whatsapp"] },
    providers: {
      "twilio-whatsapp": {
        override: { body: { ContentSid: "HXXXXXXXXXXXXXXXXXXXXXXXXXXX" } }, // or set it on the template's WhatsApp channel
      },
    },
  },
});
```

**Send Template Message (Python):**
```python
client.send.message(
    message={
        "to": {"phone_number": "+15551234567"},
        "template": "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
        "data": {
            "customerName": "Jane",
            "orderNumber": "12345",
            "deliveryDate": "Jan 30",
        },
        "routing": {"method": "single", "channels": ["twilio-whatsapp"]},
        "providers": {
            "twilio-whatsapp": {
                "override": {"body": {"ContentSid": "HXXXXXXXXXXXXXXXXXXXXXXXXXXX"}},
            },
        },
    }
)
```

**WhatsApp with SMS Fallback:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbr0s4y7qv2n8c5d1xj9k",
    routing: {
      method: "single",
      channels: ["twilio-whatsapp", "sms"]
    }
  }
});
```

---

Best practices for sending WhatsApp messages through Twilio with content templates and the 24-hour window.

## WhatsApp Overview

Courier uses the Twilio API for WhatsApp. Every send names a Twilio content template by its Content SID, and WhatsApp decides whether that content may go out:

| Message Type | When to Use | Approval Required |
|--------------|-------------|-------------------|
| Approved content template | Business-initiated contact, or any time outside the 24-hour window | Yes (by WhatsApp) |
| Session content | Within 24 hours of the user's last message | No for text, media, quick-reply and list-picker. Still needs a Content SID |

## Message Types

### Approved Templates (Business-Initiated)

Required when:
- Starting a new conversation
- User hasn't messaged in 24+ hours
- Sending proactive notifications

**WhatsApp must approve the template.** Review takes a few minutes to 24 hours.

### Session Messages (User-Initiated)

Available when:
- User messaged within last 24 hours
- Responding to user inquiry
- Continuing active conversation

**Unapproved text, media, quick-reply or list-picker content.** It still needs a Content SID.

### 24-Hour Window

```
User sends message
        │
        ▼
┌───────────────────────────────────────┐
│       24-Hour Session Window          │
│                                       │
│  ✓ Unapproved text and media          │
│  ✓ Quick-reply and list-picker        │
│  ✓ Still needs a Content SID          │
│                                       │
└───────────────────────────────────────┘
        │
        ▼ (24 hours pass)
        
Only approved content templates can go out
```

The window runs for 24 hours after the user's most recent message.

## Template Setup

Templates are built and submitted in Twilio's Content Template Builder (**Messaging → Templates** in the Twilio Console). **Save and submit for WhatsApp approval** creates the template, assigns its `HX...` Content SID, and sends it for review.

### Template Categories

| Category | Use Case |
|----------|----------|
| **UTILITY** | Order updates, account alerts |
| **AUTHENTICATION** | OTP, verification codes |
| **MARKETING** | Promotions, offers |

### Content Types

| Content type | Use | Inside the window | Outside the window |
|--------------|-----|-------------------|--------------------|
| `twilio/text` | Plain text | No approval needed | Needs approval |
| `twilio/media` | Image or document with text | No approval needed | Needs approval |
| `twilio/quick-reply` | Text with reply buttons | No approval needed | Needs approval |
| `twilio/list-picker` | Menu of options | No approval needed | Can't be sent |
| `twilio/card` | Card with buttons | Depends on the button types | Needs approval |
| `whatsapp/authentication` | One-time password with a copy-code button | Needs approval | Needs approval |

### Template Examples

**Order Shipped (UTILITY):**
```
Name: order_shipped
Category: UTILITY
Language: en
Content type: twilio/text

Body: Hi {{1}}, your order #{{2}} has shipped and will arrive by {{3}}.
```

**OTP Code (AUTHENTICATION):**
```
Name: otp_verification
Category: AUTHENTICATION
Language: en
Content type: whatsapp/authentication
```
OTP uses the `whatsapp/authentication` content type, which delivers a WhatsApp-approved one-time password with a copy-code button. It needs approval even inside the 24-hour window.

**Appointment Reminder (UTILITY):**
```
Name: appointment_reminder
Category: UTILITY
Language: en
Content type: twilio/quick-reply

Body: Hi {{1}}, this is a reminder for your appointment at {{2}} on {{3}} at {{4}}. Tap a button to reply.
Buttons: [Confirm] [Reschedule]
```

## Courier Integration

### Setup

1. In the Twilio Console, copy your Account SID and Auth Token. Your WhatsApp sender is the From number
2. In Courier, open **Integrations → WhatsApp** and enter the Account SID, Auth Token and From number
3. Create the content template in Twilio and get it approved, then paste its Content SID into your Courier template's WhatsApp channel settings

### Send Template Message

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

// The Content SID comes from the template's WhatsApp channel settings
await client.send.message({
  message: {
    to: { phone_number: "+15551234567" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht", // Your Courier template
    data: {
      customerName: "Jane",
      orderNumber: "12345",
      deliveryDate: "January 30, 2026"
    },
    routing: {
      method: "single",
      channels: ["twilio-whatsapp"]
    }
  }
});
```

### Template Variable Mapping

The content template uses `{{1}}`, `{{2}}`. Courier sends the Content SID with its variables, and Twilio fills in the approved template. Check the provider request in the message log on the first send to confirm what Courier passed.

```text
WhatsApp template body:
  Hi {{1}}, your order #{{2}} has shipped and will arrive by {{3}}.

Rendered message:
  Hi Jane, your order #12345 has shipped and will arrive by Jan 30.
```

### OTP Template

```typescript
async function sendWhatsAppOTP(
  phoneNumber: string,
  code: string,
  requestId: string,
) {
  await client.send.message({
    message: {
      to: { phone_number: phoneNumber },
      template: "nt_01kmrbr0s4y7qv2n8c5d1xj9k",
      data: { code },
      routing: {
        method: "single",
        channels: ["twilio-whatsapp", "sms"], // Fallback to SMS
      },
    },
  }, {
    // requestId identifies this OTP attempt (typically a row ID in your
    // OTP table); a "resend code" produces a new requestId and thus a
    // new send, while retries of the same attempt collapse.
    headers: { "Idempotency-Key": `otp-wa-${phoneNumber}-${requestId}` },
  });
}

await sendWhatsAppOTP("+15551234567", "847293", crypto.randomUUID());
```

### With User Profile

```typescript
// Store WhatsApp number in user profile
await client.profiles.create("user-123", {
  profile: {
    phone_number: "+15551234567" // E.164 format
  }
});

// Send using user_id
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbx5q8x2v6d1c4n7w9hj",
    data: {
      patientName: "Jane",
      location: "123 Medical Center",
      date: "January 30, 2026",
      time: "2:00 PM"
    },
    routing: {
      method: "single",
      channels: ["twilio-whatsapp"]
    }
  }
});
```

## Interactive Messages and Media

Create `twilio/quick-reply` or `twilio/list-picker` content in Twilio and send its Content SID. List-picker works only inside the 24-hour window. Images and documents go in a `twilio/media` or `twilio/card` content template the same way.

## Template Best Practices

### Approval Tips

1. **Keep it clear and non-promotional** - WhatsApp disallows promotional material in templates
2. **Include sample values** - Give every variable a sample value so reviewers have context
3. **Approve each language** - Every language version needs its own approval
4. **Watch quality** - Frequent spam reports can cost you the ability to send

### Variable Guidelines

**Good:**
```
Hi {{1}}, your order #{{2}} shipped!
```

**Bad:**
```
Hi {{1}}, {{2}} {{3}} {{4}} {{5}} {{6}}...
```

WhatsApp rejects templates whose variables are out of order, sit next to each other, or start or end the message. Keep at least 2x+1 plain words for every x variables.

## Pricing

Meta charges per message, by category and the recipient's country. Twilio adds its own per-message fee.

> **Never quote a price from memory or from this file.** Fetch
> https://developers.facebook.com/docs/whatsapp/pricing and read the current rates for the
> countries the customer sends to.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `No Content SID specified.` | No SID on template or send | Set ContentSid |
| Template rejected | Policy violation | Review WhatsApp's guidelines, revise and resubmit |
| Message not delivered | Unapproved content outside 24hr window | Use an approved template |
| Phone not found | Invalid format | Use E.164 format (+1...) |
| Rate limited | Too many messages | Set a [send rate limit](../guides/providers.md#send-rate-limits) on the provider |

### Debug Checklist

1. WhatsApp (`twilio-whatsapp`) connected in Courier with the Account SID, Auth Token and From number?
2. Content SID set on the template or the send?
3. Template approved in Twilio, if the user hasn't messaged in 24 hours?
4. Phone number in E.164 format?
5. User has opted in?

## Multi-Channel with WhatsApp

### WhatsApp with SMS Fallback

```typescript
// Try WhatsApp, fall back to SMS
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbr0s4y7qv2n8c5d1xj9k",
    data: { code: "847293" },
    routing: {
      method: "single",
      channels: ["twilio-whatsapp", "sms"]
    }
  }
});
```

### When to Use Each

| Use WhatsApp | Use SMS |
|--------------|---------|
| Rich media needed | Simple text only |
| International messaging | US/Canada domestic |
| User prefers WhatsApp | No WhatsApp account |
| Conversation-style support | One-way notifications |

## Related

- [SMS](./sms.md) - Alternative mobile channel
- [Multi-Channel](../guides/multi-channel.md) - WhatsApp in routing strategies
- [Providers](../guides/providers.md) - Provider config and send rate limits
- [Orders](../transactional.md) - Order notification patterns
- [Appointments](../transactional.md) - Appointment reminders
