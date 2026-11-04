# WhatsApp Channel

**Contents:** [Quick Reference](#quick-reference) · [Template Setup](#template-setup) · [Courier Integration](#courier-integration) · [Interactive Messages and Media](#interactive-messages-and-media) · [Template Best Practices](#template-best-practices) · [Pricing](#pricing) · [Troubleshooting](#troubleshooting) · [Related](#related)

## Quick Reference

### Rules
- Courier sends WhatsApp through Twilio. The provider key is `twilio-whatsapp`
- Connect it under Integrations with a Twilio Account SID, Auth Token and a WhatsApp-enabled From number
- Every send needs a Twilio Content SID (`HX...`). Set it in the template's WhatsApp channel settings, or per send at `providers["twilio-whatsapp"].override.body.ContentSid`. Without one, the send fails with `No Content SID specified.`
- Outside the 24-hour window, the Content SID must belong to a template WhatsApp approved. Submit it in the Twilio Console
- Inside the window, unapproved text, media, quick-reply and list-picker content can go out, but it still needs a Content SID
- Phone numbers go in `phone_number`, in E.164: `+15551234567`
- Template categories are Marketing, Authentication and Utility. Keep promotional wording out of Utility and Authentication, or WhatsApp rejects or recategorizes the template
- WhatsApp requires an explicit opt-in from each user before you message them

### Common Mistakes
- Meta Cloud API shapes (`interactive`, `header.image.link`) in an override. Courier calls Twilio, not Meta

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

## Template Setup

Templates are built and submitted in Twilio's Content Template Builder (**Messaging → Templates** in the Twilio Console). **Save and submit for WhatsApp approval** creates the template, assigns its `HX...` Content SID, and sends it for review.

### Content Types

| Content type | Use | Inside the window | Outside the window |
|--------------|-----|-------------------|--------------------|
| `twilio/text` | Plain text | No approval needed | Needs approval |
| `twilio/media` | Image or document with text | No approval needed | Needs approval |
| `twilio/quick-reply` | Text with reply buttons | No approval needed | Needs approval |
| `twilio/list-picker` | Menu of options | No approval needed | Can't be sent |
| `twilio/card` | Card with buttons | Depends on the button types | Needs approval |
| `whatsapp/authentication` | One-time password with a copy-code button | Needs approval | Needs approval |

## Courier Integration

### Setup

1. In the Twilio Console, copy your Account SID and Auth Token. Your WhatsApp sender is the From number
2. In Courier, open **Integrations → WhatsApp** and enter the Account SID, Auth Token and From number
3. Create the content template in Twilio and get it approved, then paste its Content SID into your Courier template's WhatsApp channel settings

### Template Variable Mapping

The content template uses numbered variables (`{{1}}`, `{{2}}`). Courier sends the Content SID with its variables, and Twilio fills in the approved template. Check the provider request in the message log on the first send to confirm what Courier passed.

A `user_id` send reaches WhatsApp through `profile.phone_number` (E.164). OTPs follow [transactional.md](../transactional.md#sending-an-otp) (idempotency key, `single` routing) with `channels: ["twilio-whatsapp", "sms"]`.

## Interactive Messages and Media

Create `twilio/quick-reply` or `twilio/list-picker` content in Twilio and send its Content SID. List-picker works only inside the 24-hour window. Images and documents go in a `twilio/media` or `twilio/card` content template the same way.

## Template Best Practices

WhatsApp rejects templates whose variable numbers skip an integer (`{{1}}` then `{{3}}`), whose variables sit next to each other (a space between them still counts), or whose body starts or ends with a variable. Keep at least 2x+1 plain words for every x variables.

## Pricing

Meta charges per message, by category and the recipient's country. Twilio adds its own per-message fee.

> **Never quote a price from memory or from this file.** Fetch
> https://developers.facebook.com/docs/whatsapp/pricing and read the current rates for the
> countries the customer sends to.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `No Content SID specified.` | No SID on template or send | Set ContentSid |
| Message not delivered | Unapproved content outside 24hr window | Use an approved template |
| Rate limited | Too many messages | Set a [send rate limit](../guides/providers.md#send-rate-limits) on the provider |

## Related

- [SMS](./sms.md) - Alternative mobile channel
- [Multi-Channel](../guides/multi-channel.md) - Fallback routing
- [Providers](../guides/providers.md) - Provider config and send rate limits
- [Orders](../transactional.md) - Order notification patterns
- [Appointments](../transactional.md) - Appointment reminders
