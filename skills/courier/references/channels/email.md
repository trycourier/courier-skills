# Email Channel

**Contents:** [Quick Reference](#quick-reference) · [Courier Integration](#courier-integration) · [Link Tracking](#link-tracking) · [Bounce Handling](#bounce-handling) · [Troubleshooting](#troubleshooting) · [Testing](#testing) · [Related](#related)

## Quick Reference

### Rules
- Authenticate the sending domain (SPF, DKIM, DMARC) at your email provider and in DNS before sending. Gmail, Yahoo and Microsoft reject or spam-file unauthenticated mail
- Overrides apply after rendering and aren't templated, and attachments go through a provider-specific override. See [Courier Integration](#courier-integration)
- Courier doesn't classify bounces as hard or soft. See [Bounce Handling](#bounce-handling)

### Templates

Build email templates from Elemental blocks unless the design needs markup the blocks cannot express. Blocks stay editable in Design Studio's drag-and-drop editor; a `raw` HTML or MJML body renders and displays in Design Studio but has to be edited as HTML. See [elemental.md](../guides/elemental.md#channel).

---

## Courier Integration

### With Email-Specific Overrides

`message.channels.email.override` changes parts of an email at send time, for every email provider
on the send. A `message.providers.<key>.override` targets one provider and wins when both set a field.

```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: { orderNumber: "12345" },
    channels: {
      email: {
        override: {
          from: "Acme Orders <orders@t.acme.com>",
          reply_to: "support@acme.com",
          bcc: "records@acme.com",
        },
      },
    },
  },
});
```

| Field | Does |
|---|---|
| `subject` | Replaces the subject line |
| `from`, `reply_to` | A plain address or `"Display Name <email>"` |
| `cc`, `bcc` | Comma-separated addresses |
| `html`, `text` | Replaces the rendered body entirely |
| `attachments` | Files, in the provider's shape (below) |
| `brand` | Brand settings, same schema as the Brands API |
| `tracking` | `{ "open": false }` turns off open tracking |

Overrides apply **after** rendering, so the Rendered tab in message logs doesn't show them; check the
Raw provider request. They are passed to the provider as-is: an override `subject` or `html` is not
a template and variables in it are not filled in. On a send held for a [digest](../guides/digests.md),
overrides are dropped at release.

### Attachments

Courier attaches files through a **provider override**. You pass the file on the send, in the shape the underlying provider expects. File content is base64-encoded. This is how you deliver the PDF for a receipt or invoice.

```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    template: "nt_receipt",
    data: { orderNumber: "12345" },
    providers: {
      sendgrid: {
        override: {
          body: {
            attachments: [
              {
                content: pdfBase64,            // base64-encoded file
                type: "application/pdf",
                filename: "receipt-12345.pdf",
              },
            ],
          },
        },
      },
    },
  },
});
```

The **override nesting is provider-specific**. It mirrors that provider's own send API. SendGrid nests `attachments` under `body` (above); Mailgun takes `attachments` directly under `override`. Match the provider you've configured; check its [integration doc](https://www.courier.com/docs/integrations/email/overview) for the exact field. Attachments aren't part of the template. They're per-send data you supply at call time.

A request body caps at **6 MB**, and base64 adds about a third, so one send holds about 4.5 MB of attachments. A bigger body returns `413 Payload Too Large`. Host larger files and link to them.

### Other Provider Settings

- **SMTP per send:** `message.providers.smtp.override.config` takes [Nodemailer transport options](https://nodemailer.com/smtp) (`host`, `port`, `secure`, `auth`) and replaces the stored SMTP settings for that one message. See [SMTP](https://www.courier.com/docs/integrations/email/smtp#transport-override).
- **SendGrid template import** needs a key with Full Access to Template Engine. A Mail Send key sends fine but lists no templates, so the import shows none.
- **Failover to a second email provider:** see [multi-channel.md](../guides/multi-channel.md#provider-failover).

## Link Tracking

Open and click tracking are workspace settings (Settings → Tracking), not template settings. Links need absolute URLs. To skip one link, set `disable_tracking: true` on an Elemental action, or `data-courier-link-tracking="false"` on the `<a>`. To skip open tracking for one send, set `channels.email.override.tracking: { open: false }`.

## Bounce Handling

**Courier does not classify a bounce as hard or soft.** `data.providers[].error` is the provider's
own message as a **string**, worded differently by each provider, so don't pattern-match it in
delivery logic. Record the failure and let repetition drive suppression; if you need the hard/soft
distinction itself, take it from your email provider's own webhooks.

```typescript
// Handle delivery webhooks from Courier
// Bounces surface as message:updated with status UNDELIVERABLE.
app.post('/webhooks/courier', async (req, res) => {
  const { type, data } = req.body;

  if (type === 'message:updated' && data.status === 'UNDELIVERABLE') {
    // e.g. "probe@example.com belongs to a reserved domain name." — a string, not a code
    const providerError = data.providers?.[0]?.error;
    await recordDeliveryFailure(data.recipient, data.reason, providerError);
    if (await failureCount(data.recipient) >= 3) await markEmailInvalid(data.recipient);
  }

  res.sendStatus(200);
});
```

## Troubleshooting

### AWS SES Messages Stay at SENT

SES reports delivery through SNS, so every SES message stays at `SENT` until an SES configuration set publishes `Bounce`, `Delivery` and `Reject` to an SNS topic subscribed to the SES integration's **Message Events Webhook URL** (raw message delivery off). Add the configuration set's ARN to the IAM policy Courier sends with, or every send fails with `not authorized to perform ses:SendRawEmail`. Steps: [AWS SES](https://www.courier.com/docs/integrations/email/aws-ses).

### Gmail Clips the Email

Gmail clips HTML over about 102 KB, hiding the footer and unsubscribe link. Check the size in the [rendered output](../guides/templates.md#verify-the-rendered-output).

## Testing

Render the email on real clients (Outlook, Gmail, Apple Mail, mobile, dark mode) with [Device Preview](../guides/device-preview.md) before a real send, and check what a send produced in its [rendered output](../guides/templates.md#verify-the-rendered-output).

## Related

- [Elemental](../guides/elemental.md) - Email content and layout: element types, styled text, columns/cards
- [Quickstart](../guides/quickstart.md) - New to Courier? Start here for install, API key, first send
- [Multi-Channel](../guides/multi-channel.md) - Email as part of routing strategy
- [Reliability](../guides/reliability.md) - Retry logic and error handling
- [Digests](../guides/digests.md) - roll many events into one scheduled email
- [Throttling](../guides/throttling.md) - Send rate management
