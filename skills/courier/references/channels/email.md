# Email Channel

## Quick Reference

### Rules
- MUST configure SPF, DKIM, and DMARC before sending (Gmail/Yahoo/Microsoft require it)
- Only ONE SPF record per domain (combine includes if multiple providers)
- DMARC progression: start with `p=none`, then `p=quarantine`, finally `p=reject`
- Keep bounce rate under 2% (under 1% is good)
- Keep complaint rate under 0.1%
- Use subdomains to separate transactional (`t.acme.com`) from marketing (`m.acme.com`)
- Avoid `noreply@` addresses - use monitored inboxes
- Subject lines: under 50 characters for mobile
- Pre-header text: under 90 characters, don't repeat subject

### Common Mistakes
- Missing SPF/DKIM/DMARC authentication (emails go to spam or get rejected)
- Having multiple SPF records (only one allowed per domain)
- Rushing IP warming (causes reputation damage)
- Sending to purchased lists (destroys sender reputation)
- Ignoring bounces and complaints (reputation damage)
- Sudden volume spikes (triggers spam filters)
- Using URL shorteners like bit.ly (spam trigger)

### Templates

**Basic Email Send (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    template: "nt_01kmrc1k3q6x9v2d5c8n1w4ht",
    data: { userName: "Jane" }
  }
});
```

**Basic Email Send (Python):**
```python
client.send.message(
    message={
        "to": {"email": "jane@example.com"},
        "template": "nt_01kmrc1k3q6x9v2d5c8n1w4ht",
        "data": {"userName": "Jane"},
    }
)
```

**With Provider Override (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    channels: {
      email: {
        override: {
          from: { email: "orders@t.acme.com", name: "Acme Orders" },
          reply_to: "support@acme.com"
        }
      }
    }
  }
});
```

---

Best practices for sending emails that reach inboxes and engage users.

## Email Authentication

**Required by Gmail/Yahoo/Microsoft** - unauthenticated emails will be rejected or spam-filtered.

### SPF (Sender Policy Framework)

Specifies which servers can send email for your domain.

```
# Example DNS TXT record
v=spf1 include:sendgrid.net include:_spf.google.com ~all
```

- Add the SPF TXT record provided by your email provider
- `~all` (soft fail) for setup flexibility, `-all` (hard fail) for production
- Only one SPF record per domain (combine includes if multiple providers)

### DKIM (DomainKeys Identified Mail)

Cryptographic signature proving email authenticity.

- Your email provider generates DKIM keys
- Add CNAME or TXT records to your DNS as instructed
- Common selector names: `s1._domainkey`, `mail._domainkey`

### DMARC

Policy for handling SPF/DKIM failures + reporting.

```
# Start with monitoring (p=none)
_dmarc.yourdomain.com  TXT  "v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com"

# Progress to quarantine
v=DMARC1; p=quarantine; pct=10; rua=mailto:dmarc@yourdomain.com

# Finally, reject
v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com
```

**Progression:** `p=none` (monitor) → `p=quarantine` (spam folder) → `p=reject` (block)

## Sender Configuration

| Field | Best Practice | Example |
|-------|--------------|---------|
| From Name | Brand name for transactional/system mail (recognizable sender builds reputation); a person's name for Primary-inbox marketing (e.g., Gmail Promotions → Primary) | Transactional: `Acme` · Marketing: `Jane at Acme` |
| From Email | Subdomain for transactional | notifications@t.acme.com |
| Reply-To | Monitored inbox | support@acme.com |

### Subdomain Strategy

Separate sender reputation by email type:

| Subdomain | Purpose | Example |
|-----------|---------|---------|
| `t.acme.com` | Transactional | receipts, password resets |
| `m.acme.com` | Marketing | newsletters, promotions |
| `alerts.acme.com` | Alerts | security, system status |

**Why?** If marketing reputation suffers, transactional emails still deliver.

### Avoid `noreply@`

- Users DO reply to transactional emails (questions about orders, etc.)
- Signals low trust to spam filters
- Use `notifications@` or `hello@` with forwarding rules instead

## Sender Reputation

### IP Warming Schedule

New sending domain/IP? Gradually increase volume:

| Week | Daily Volume | Target Audience |
|------|-------------|-----------------|
| 1 | 50-100 | Most engaged users |
| 2 | 200-500 | Recent active users |
| 3 | 1,000-2,000 | Active in last 30 days |
| 4 | 5,000-10,000 | Full list |
| 5+ | Full volume | All subscribers |

**Tips:**
- Send to engaged users first (recently opened/clicked)
- Maintain consistent daily volume
- Monitor bounce rates closely
- Pause if bounce rate exceeds 2%

### Reputation Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Bounce rate | <1% | 1-2% | >2% |
| Complaint rate | <0.05% | 0.05-0.1% | >0.1% |
| Open rate | >20% | 10-20% | <10% |

### List Hygiene

```typescript
// Implement automatic list cleaning
async function cleanEmailList() {
  // Remove hard bounces immediately
  await removeHardBounces();
  
  // Remove soft bounces after 3 consecutive failures
  await removePersistentSoftBounces(3);
  
  // Sunset inactive subscribers (no opens in 6+ months)
  await archiveInactiveSubscribers(180);
}
```

## Courier Integration

For the basic email send pattern, see the [Quick Reference templates](#templates) above. The examples below show additional options.

### With Inline Content

```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    content: {
      title: "Your order has shipped",
      body: "Hi Jane, your order #12345 is on the way!\n\nTrack at: https://acme.com/track/12345"
    }
  }
});
```

### With Email-Specific Overrides

```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: { orderNumber: "12345" },
    channels: {
      email: {
        override: {
          from: {
            email: "orders@t.acme.com",
            name: "Acme Orders"
          },
          reply_to: "support@acme.com",
          bcc: "records@acme.com",
          headers: {
            "X-Order-ID": "12345"
          }
        }
      }
    }
  }
});
```

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

The **override nesting is provider-specific**. It mirrors that provider's own send API. SendGrid nests `attachments` under `body` (above); Mailgun takes `attachments` directly under `override`. Match the provider you've configured; check its [integration doc](https://www.courier.com/docs/external-integrations/email/intro-to-email) for the exact field. Attachments aren't part of the template. They're per-send data you supply at call time.

### Provider Failover

Configure multiple email providers in Courier dashboard. If SendGrid fails, automatically try Mailgun:

```
Priority 1: SendGrid
Priority 2: Mailgun  
Priority 3: AWS SES
```

Courier handles failover automatically based on your configuration.

## Link Tracking

Courier can track link clicks for analytics:

```typescript
await client.send.message({
  message: {
    to: { email: "jane@example.com" },
    template: "nt_01kmrbu5x8q2v6d1c4n7w9hj",
    // Link tracking enabled in template settings
  }
});

// Receive webhook when links are clicked
// POST /webhooks/courier
// { type: "message:updated", data: { status: "CLICKED", id: "...", ... } }
```

## Bounce Handling

| Type | Cause | Action |
|------|-------|--------|
| Hard bounce | Invalid address, domain doesn't exist | Remove immediately |
| Soft bounce | Mailbox full, server temporarily down | Retry: 1h → 4h → 24h |
| Block | Spam filter rejection | Review content, check authentication |

```typescript
// Handle delivery webhooks from Courier
// Bounces surface as UNDELIVERABLE message:updated events with
// provider-specific reason in data.providers[].error and data.reason.
app.post('/webhooks/courier', async (req, res) => {
  const { type, data } = req.body;

  if (type === 'message:updated' && data.status === 'UNDELIVERABLE') {
    const providerError = data.providers?.[0]?.error;
    if (providerError?.type === 'hard_bounce') {
      await markEmailInvalid(data.recipient);
    } else {
      await incrementSoftBounceCount(data.recipient);
    }
  }

  res.sendStatus(200);
});
```

## Troubleshooting

### Emails Going to Spam?

1. **Check authentication:** Verify SPF, DKIM, DMARC at [MXToolbox](https://mxtoolbox.com)
2. **Check reputation:** [Google Postmaster Tools](https://postmaster.google.com), [Microsoft SNDS](https://sendersupport.olc.protection.outlook.com/snds/)
3. **Review content:** Avoid spam trigger words, excessive images, URL shorteners
4. **Check patterns:** Sudden volume spikes damage reputation

### Low Open Rates?

| Issue | Solution |
|-------|----------|
| Poor subject lines | A/B test, be specific |
| Wrong send time | Test different times, use send-time optimization |
| Low relevance | Segment by interest, personalize |
| Deliverability issues | Check spam folder placement |

### Gmail Tabs

To land in Primary (not Promotions):
- Avoid heavy images and marketing language
- Include personalization
- Prefer a person-in-brand sender (e.g., `Jane at Acme`) for marketing mail, raw brand senders (`Acme`) are fine for transactional but tend to get sorted into Promotions for promotional copy
- Keep content relevant and expected

## Testing

### Pre-Send Checklist

- [ ] Subject line under 50 characters
- [ ] Pre-header text set
- [ ] Unsubscribe link present
- [ ] Physical address in footer
- [ ] Links tested and working
- [ ] Mobile preview checked
- [ ] Plain text version included
- [ ] Personalization tokens have fallbacks

### Send Test Emails

```typescript
// Send to yourself first
await client.send.message({
  message: {
    to: { email: "your-test@example.com" },
    template: "nt_01kmrbqf7z9dn2v6w4x8cj5ht",
    data: { /* test data */ }
  }
});
```

## Related

- [Quickstart](../guides/quickstart.md) - New to Courier? Start here for install, API key, first send
- [Multi-Channel](../guides/multi-channel.md) - Email as part of routing strategy
- [Reliability](../guides/reliability.md) - Retry logic and error handling
- [Batching](../guides/batching.md) - Email digests
- [Throttling](../guides/throttling.md) - Send rate management
