# Email Channel

## Quick Reference

### Rules
- MUST configure SPF, DKIM, and DMARC before sending (Gmail/Yahoo/Microsoft require it)
- Only ONE SPF record per domain (combine includes if multiple providers)
- DMARC progression: start with `p=none`, then `p=quarantine`, finally `p=reject`
- Keep bounce rate under 2% (under 1% is good)
- Keep complaint rate under 0.1%
- Marketing emails MUST include physical address and unsubscribe link (CAN-SPAM)
- Use subdomains to separate transactional (`t.acme.com`) from marketing (`m.acme.com`)
- Avoid `noreply@` addresses - use monitored inboxes
- Subject lines: under 50 characters for mobile
- Pre-header text: under 90 characters, don't repeat subject

### Common Mistakes
- Missing SPF/DKIM/DMARC authentication (emails go to spam or get rejected)
- Having multiple SPF records (only one allowed per domain)
- Rushing IP warming (causes reputation damage)
- Sending to purchased lists (destroys sender reputation)
- Adding promotional content to transactional emails (reclassifies as marketing)
- Ignoring bounces and complaints (reputation damage)
- Sudden volume spikes (triggers spam filters)
- Using URL shorteners like bit.ly (spam trigger)
- Missing unsubscribe link in marketing emails (CAN-SPAM violation)

### Templates

**Basic Email Send:**
```typescript
await courier.send({
  message: {
    to: { email: "jane@example.com" },
    template: "TEMPLATE_NAME",
    data: { userName: "Jane" }
  }
});
```

**With Provider Override:**
```typescript
await courier.send({
  message: {
    to: { email: "jane@example.com" },
    template: "ORDER_SHIPPED",
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
- `~all` (soft fail) for setup flexibility, `−all` (hard fail) for production
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
| From Name | Company or product name | Acme |
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

## Email Design

### Mobile-First (60%+ opens on mobile)

| Element | Specification |
|---------|---------------|
| Layout | Single column, max 600px |
| Body text | 16px minimum |
| Headings | 20-24px |
| CTA buttons | 44x44px minimum tap target |
| Line height | 1.5 for readability |

### Email Structure

```
┌─────────────────────────────────────┐
│           Logo / Header             │
├─────────────────────────────────────┤
│                                     │
│       Primary Message               │
│       (Above the fold)              │
│                                     │
│         [ CTA Button ]              │
│                                     │
├─────────────────────────────────────┤
│       Supporting Details            │
│       • Item 1                      │
│       • Item 2                      │
├─────────────────────────────────────┤
│   Footer: Unsubscribe | Address     │
└─────────────────────────────────────┘
```

### Subject Lines

| Do | Don't |
|----|-------|
| "Your order #12345 shipped" | "Order update" |
| "Reset your Acme password" | "Important: Action Required!!!" |
| "Jane commented on your post" | "New notification" |
| Keep under 50 characters | ALL CAPS or excessive punctuation |

### Pre-header Text

The preview text shown after the subject line:

```html
<!-- Visible pre-header -->
<span style="display:block;max-width:0;overflow:hidden;">
  Your order arrives Thursday. Track your package →
</span>
```

- Reinforce or complement the subject
- Keep under 90 characters
- Don't repeat the subject line

## Courier Integration

### Basic Email Send

```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

await courier.send({
  message: {
    to: { email: "jane@example.com" },
    template: "WELCOME_EMAIL",
    data: {
      userName: "Jane",
      loginUrl: "https://app.acme.com/login"
    }
  }
});
```

### With Inline Content

```typescript
await courier.send({
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
await courier.send({
  message: {
    to: { email: "jane@example.com" },
    template: "ORDER_SHIPPED",
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
await courier.send({
  message: {
    to: { email: "jane@example.com" },
    template: "WEEKLY_DIGEST",
    // Link tracking enabled in template settings
  }
});

// Receive webhook when links are clicked
// POST /webhooks/courier
// { event: "clicked", link: "https://...", messageId: "..." }
```

## Bounce Handling

| Type | Cause | Action |
|------|-------|--------|
| Hard bounce | Invalid address, domain doesn't exist | Remove immediately |
| Soft bounce | Mailbox full, server temporarily down | Retry: 1h → 4h → 24h |
| Block | Spam filter rejection | Review content, check authentication |

```typescript
// Handle bounce webhooks from Courier
app.post('/webhooks/courier', async (req, res) => {
  const { event, recipient, error } = req.body;
  
  if (event === 'bounced') {
    if (error.type === 'hard') {
      await markEmailInvalid(recipient);
    } else if (error.type === 'soft') {
      await incrementSoftBounceCount(recipient);
    }
  }
  
  res.sendStatus(200);
});
```

## Common Templates

### Password Reset

```typescript
// Template: PASSWORD_RESET
data: {
  resetUrl: "https://acme.com/reset?token=abc123",
  expiresIn: "1 hour",
  userEmail: "jane@example.com"
}

// Subject: Reset your Acme password
// Body: Click to reset. Expires in 1 hour. Didn't request this? Ignore or contact support.
```

### Order Confirmation

```typescript
// Template: ORDER_CONFIRMATION
data: {
  orderNumber: "12345",
  items: [
    { name: "Widget", quantity: 2, price: 29.99 },
    { name: "Gadget", quantity: 1, price: 49.99 }
  ],
  subtotal: 109.97,
  shipping: 5.99,
  total: 115.96,
  shippingAddress: { ... },
  estimatedDelivery: "January 30-31"
}
```

### Weekly Digest

```typescript
// Template: WEEKLY_DIGEST
data: {
  userName: "Jane",
  weekRange: "Jan 20-26",
  stats: {
    views: 1234,
    likes: 56,
    comments: 12
  },
  topContent: [ ... ],
  recommendations: [ ... ]
}
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
- Send from a person, not a brand name
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
await courier.send({
  message: {
    to: { email: "your-test@example.com" },
    template: "ORDER_SHIPPED",
    data: { /* test data */ }
  }
});
```

## Related

- [Compliance](../guides/compliance.md) - CAN-SPAM, GDPR requirements
- [Multi-Channel](../guides/multi-channel.md) - Email as part of routing strategy
- [Reliability](../guides/reliability.md) - Retry logic and error handling
- [Batching](../guides/batching.md) - Email digests
- [Throttling](../guides/throttling.md) - Send rate management
