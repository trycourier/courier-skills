# WhatsApp Channel

## Quick Reference

### Rules
- Business-initiated messages REQUIRE pre-approved templates
- Templates must be approved by Meta (24-72 hour review)
- 24-hour session window: after user messages, can send free-form for 24hrs
- After 24hrs with no user message: MUST use template
- Phone numbers MUST be E.164 format: +15551234567
- Explicit opt-in required before messaging users
- Template categories: UTILITY (fastest approval), AUTHENTICATION, MARKETING (strictest)
- Variables use positional format: `{{1}}`, `{{2}}`, `{{3}}`
- Quick reply buttons: maximum 3
- Template variable count must match exactly

### Common Mistakes
- Sending without approved template (outside 24hr window)
- Variable count mismatch (template has 3, you send 2)
- Phone number not in E.164 format
- Not recording opt-in consent
- Using MARKETING category for transactional messages (slower approval)
- Too many template variables (looks spammy, may be rejected)
- Promotional content in UTILITY templates (will be rejected)
- Not handling template rejection gracefully

### Templates

**Send Template Message:**
```typescript
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    template: "ORDER_SHIPPED",
    data: {
      customerName: "Jane",      // {{1}}
      orderNumber: "12345",      // {{2}}
      deliveryDate: "Jan 30"     // {{3}}
    },
    routing: { method: "single", channels: ["whatsapp"] }
  }
});
```

**With Media Header:**
```typescript
channels: {
  whatsapp: {
    override: {
      body: {
        header: {
          type: "image",
          image: { link: "https://acme.com/proof.jpg" }
        }
      }
    }
  }
}
```

**WhatsApp with SMS Fallback:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "OTP_CODE",
    routing: {
      method: "single",
      channels: ["whatsapp", "sms"]
    }
  }
});
```

---

Best practices for sending WhatsApp Business messages with templates and session messaging.

## WhatsApp Business API Overview

WhatsApp has strict rules to prevent spam and maintain user trust:

| Message Type | When to Use | Approval Required |
|--------------|-------------|-------------------|
| Template messages | Business-initiated contact | Yes (by Meta) |
| Session messages | Response within 24hr window | No |

## Message Types

### Template Messages (Business-Initiated)

Required when:
- Starting a new conversation
- User hasn't messaged in 24+ hours
- Sending proactive notifications

**Must be pre-approved by Meta** (24-72 hour review)

### Session Messages (User-Initiated)

Available when:
- User messaged within last 24 hours
- Responding to user inquiry
- Continuing active conversation

**No template required** - send free-form text, images, documents, etc.

### 24-Hour Window

```
User sends message
        │
        ▼
┌───────────────────────────────────────┐
│       24-Hour Session Window          │
│                                       │
│  ✓ Free-form messages allowed         │
│  ✓ Any media type                     │
│  ✓ No template required               │
│                                       │
└───────────────────────────────────────┘
        │
        ▼ (24 hours pass)
        
Must use approved template to re-initiate
```

## Template Setup

### Template Categories

| Category | Use Case | Approval Time | Cost |
|----------|----------|---------------|------|
| **UTILITY** | Order updates, account alerts | ~24 hours | Lower |
| **AUTHENTICATION** | OTP, verification codes | ~24 hours | Lower |
| **MARKETING** | Promotions, offers | 24-72 hours | Higher |

**Start with UTILITY templates** - highest approval rates.

### Template Structure

```
┌─────────────────────────────────────┐
│ HEADER (optional)                   │
│ Text, Image, Video, or Document     │
├─────────────────────────────────────┤
│ BODY (required)                     │
│ Main message with {{variables}}     │
├─────────────────────────────────────┤
│ FOOTER (optional)                   │
│ Small disclaimer text               │
├─────────────────────────────────────┤
│ BUTTONS (optional)                  │
│ Quick Reply or URL buttons          │
└─────────────────────────────────────┘
```

### Template Examples

**Order Shipped (UTILITY):**
```
Name: order_shipped
Category: UTILITY
Language: en

Header: 📦 Your order is on the way!
Body: Hi {{1}}, your order #{{2}} has shipped and will arrive by {{3}}.
Footer: Track at acme.com/track
Buttons: [Track Order] → https://acme.com/track/{{2}}
```

**OTP Code (AUTHENTICATION):**
```
Name: otp_verification
Category: AUTHENTICATION
Language: en

Body: Your Acme verification code is {{1}}. Valid for 10 minutes. Do not share this code.
```

**Appointment Reminder (UTILITY):**
```
Name: appointment_reminder
Category: UTILITY
Language: en

Header: 📅 Appointment Reminder
Body: Hi {{1}}, this is a reminder for your appointment:

📍 {{2}}
📆 {{3}}
⏰ {{4}}

Reply YES to confirm or RESCHEDULE to change.
Buttons: [Confirm] [Reschedule]
```

## Courier Integration

### Setup

1. Create Meta Business account at [business.facebook.com](https://business.facebook.com)
2. Set up WhatsApp Business API (via Meta or BSP)
3. Get Phone Number ID and Access Token
4. Configure in Courier dashboard: **Integrations → WhatsApp**

### Send Template Message

```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

// Basic template send
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    template: "ORDER_SHIPPED", // Your Courier template
    data: {
      customerName: "Jane",
      orderNumber: "12345",
      deliveryDate: "January 30, 2026"
    },
    routing: {
      method: "single",
      channels: ["whatsapp"]
    }
  }
});
```

### Template Variable Mapping

Configure in your Courier template to map data to WhatsApp variable positions:

```typescript
// Your send call
data: {
  customerName: "Jane",    // Maps to {{1}}
  orderNumber: "12345",    // Maps to {{2}}
  deliveryDate: "Jan 30"   // Maps to {{3}}
}

// WhatsApp template body
"Hi {{1}}, your order #{{2}} has shipped and will arrive by {{3}}."

// Rendered message
"Hi Jane, your order #12345 has shipped and will arrive by Jan 30."
```

### With Media Header

```typescript
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    template: "ORDER_DELIVERED",
    data: {
      customerName: "Jane",
      orderNumber: "12345"
    },
    channels: {
      whatsapp: {
        override: {
          body: {
            header: {
              type: "image",
              image: {
                link: "https://acme.com/delivery-proof/12345.jpg"
              }
            }
          }
        }
      }
    }
  }
});
```

### OTP Template

```typescript
async function sendWhatsAppOTP(phoneNumber: string, code: string) {
  await courier.send({
    message: {
      to: { phone_number: phoneNumber },
      template: "OTP_CODE",
      data: { code },
      routing: {
        method: "single",
        channels: ["whatsapp", "sms"] // Fallback to SMS
      }
    }
  }, {
    idempotencyKey: `otp-wa-${phoneNumber}-${Date.now()}`
  });
}
```

### With User Profile

```typescript
// Store WhatsApp number in user profile
await courier.users.update("user-123", {
  profile: {
    phone_number: "+15551234567" // E.164 format
  }
});

// Send using user_id
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "APPOINTMENT_REMINDER",
    data: {
      patientName: "Jane",
      location: "123 Medical Center",
      date: "January 30, 2026",
      time: "2:00 PM"
    },
    routing: {
      method: "single",
      channels: ["whatsapp"]
    }
  }
});
```

## Interactive Messages

### Quick Reply Buttons

Up to 3 buttons for quick responses:

```typescript
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    channels: {
      whatsapp: {
        override: {
          body: {
            type: "interactive",
            interactive: {
              type: "button",
              body: {
                text: "Your appointment is tomorrow at 2pm. Can you make it?"
              },
              action: {
                buttons: [
                  { type: "reply", reply: { id: "confirm", title: "Yes, I'll be there" } },
                  { type: "reply", reply: { id: "reschedule", title: "Need to reschedule" } },
                  { type: "reply", reply: { id: "cancel", title: "Cancel" } }
                ]
              }
            }
          }
        }
      }
    }
  }
});
```

### List Messages

For menus with multiple options:

```typescript
await courier.send({
  message: {
    to: { phone_number: "+15551234567" },
    channels: {
      whatsapp: {
        override: {
          body: {
            type: "interactive",
            interactive: {
              type: "list",
              body: {
                text: "What would you like help with?"
              },
              action: {
                button: "View Options",
                sections: [
                  {
                    title: "Orders",
                    rows: [
                      { id: "track", title: "Track my order", description: "Check delivery status" },
                      { id: "return", title: "Return an item", description: "Start a return" }
                    ]
                  },
                  {
                    title: "Account",
                    rows: [
                      { id: "billing", title: "Billing question", description: "Invoices and payments" },
                      { id: "password", title: "Reset password", description: "Change your password" }
                    ]
                  }
                ]
              }
            }
          }
        }
      }
    }
  }
});
```

## Opt-In Requirements

### User Consent Required

WhatsApp requires explicit opt-in before messaging users:

| Requirement | Details |
|-------------|---------|
| Clear disclosure | What messages they'll receive |
| Active opt-in | User must take action (not pre-checked) |
| Easy opt-out | Reply STOP or similar |

### Valid Opt-In Methods

```html
<!-- Web form -->
<label>
  <input type="checkbox" name="whatsapp_consent">
  Receive order updates via WhatsApp to {{phone_number}}
</label>
```

- SMS keyword: "Text START to receive WhatsApp updates"
- Click-to-chat: `https://wa.me/15551234567?text=Subscribe`
- In-app toggle with clear description

### Record Consent

```typescript
interface WhatsAppConsent {
  phoneNumber: string;
  consentedAt: Date;
  method: 'web_form' | 'sms_keyword' | 'click_to_chat';
  categories: string[]; // ['orders', 'appointments']
}

await storeConsent({
  phoneNumber: "+15551234567",
  consentedAt: new Date(),
  method: 'web_form',
  categories: ['orders']
});
```

## Template Best Practices

### Approval Tips

1. **Start with UTILITY** - Highest approval rates
2. **Be clear and specific** - Avoid vague language
3. **Include sample values** - Show Meta what it will look like
4. **No promotional content in UTILITY** - Or it will be rejected
5. **Follow Meta's policies** - No prohibited content

### Variable Guidelines

**Good:**
```
Hi {{1}}, your order #{{2}} shipped!
```

**Bad:**
```
Hi {{1}}, {{2}} {{3}} {{4}} {{5}} {{6}}...
```
(Too many variables, looks like spam)

### Content Guidelines

| Do | Don't |
|----|-------|
| Be clear and specific | Use vague, clickbait language |
| Personalize with name | Send identical mass messages |
| Provide value | Be overly promotional (in UTILITY) |
| Include business name | Forget to identify yourself |

## Pricing

WhatsApp charges per conversation (24-hour window from first message):

| Category | Cost Range (varies by country) |
|----------|-------------------------------|
| Utility | $0.005 - $0.015 |
| Authentication | $0.005 - $0.015 |
| Marketing | $0.01 - $0.05 |
| Service (user-initiated) | Free (first 1,000/month) |

**Tip:** Use UTILITY for order updates to minimize costs.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Template rejected | Policy violation | Review Meta guidelines, revise |
| Message not delivered | Outside 24hr window | Use approved template |
| "Invalid parameter" | Variable count mismatch | Check template has matching params |
| Phone not found | Invalid format | Use E.164 format (+1...) |
| Rate limited | Too many messages | Implement queuing |

### Debug Checklist

1. WhatsApp configured correctly in Courier?
2. Phone number in E.164 format?
3. Template approved in Meta Business Suite?
4. Variable count matches template?
5. User has opted in?
6. Within 24-hour window (for session messages)?

## Multi-Channel with WhatsApp

### WhatsApp with SMS Fallback

```typescript
// Try WhatsApp, fall back to SMS
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "OTP_CODE",
    data: { code: "847293" },
    routing: {
      method: "single",
      channels: ["whatsapp", "sms"]
    }
  }
});
```

### When to Use Each

| Use WhatsApp | Use SMS |
|--------------|---------|
| Rich media needed | Simple text only |
| International messaging (cheaper) | US/Canada domestic |
| User prefers WhatsApp | No WhatsApp account |
| Conversation-style support | One-way notifications |

## Related

- [SMS](./sms.md) - Alternative mobile channel
- [Compliance](../guides/compliance.md) - Consent requirements
- [Multi-Channel](../guides/multi-channel.md) - WhatsApp in routing strategies
- [Orders](../transactional/orders.md) - Order notification patterns
- [Appointments](../transactional/appointments.md) - Appointment reminders
