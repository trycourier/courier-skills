# Campaign Notifications

## Quick Reference

### Rules
- Marketing notifications should be opt-in only; record when and how the user opted in
- MUST include physical address in marketing email
- MUST include unsubscribe link (functional for 30 days after send)
- Honor opt-out immediately in-loop; suppress on the next send, don't wait for a batch job
- Max frequency: 1-2 promotional emails per week
- SMS campaigns require opt-in always, not opt-out
- Push campaigns: Only if user opted into promotional push

### Valid vs Invalid Opt-In
| Valid | Invalid |
|-------|---------|
| User checks unchecked box | Pre-checked boxes |
| "Subscribe to newsletter" click | Assumed from purchase |
| Explicit request for updates | Bundled consent |

### Required Email Elements
- Physical mailing address
- Unsubscribe link
- Accurate subject line
- Sender identification

### Best Send Times
| Audience | Best Time |
|----------|-----------|
| B2B | Tue-Thu, 9-11 AM |
| B2C | Test for your audience |
| Avoid | Monday AM, Friday PM |

### Common Mistakes
- Pre-checked opt-in boxes (invalid consent)
- Missing physical address in email
- Hidden unsubscribe link
- Misleading subject lines
- SMS promotions without written consent
- Too frequent (> 2/week = high unsubscribe)
- Emailing unsubscribed users

### Templates

**Check Opt-In Before Send (TypeScript):**
```typescript
const prefs = await client.users.preferences.retrieve(userId);
const marketingPref = prefs.items.find(p => p.topic_id === "marketing");

if (marketingPref?.status !== "OPTED_IN") {
  return; // Skip - not opted in
}

await client.send.message({
  message: {
    to: { user_id: userId },
    template: "nt_01kmrbt4n7q1x5c8v2d6w9hf",
    data: { discount: "30%", code: "SUMMER30", expiresAt: "Aug 31" }
  }
});
```

**Check Opt-In Before Send (Python):**
```python
prefs = client.users.preferences.retrieve(user_id)
marketing_pref = next((t for t in prefs.items if t.topic_id == "marketing"), None)

if not marketing_pref or marketing_pref.status != "OPTED_IN":
    return

client.send.message(
    message={
        "to": {"user_id": user_id},
        "template": "nt_01kmrbt4n7q1x5c8v2d6w9hf",
        "data": {"discount": "30%", "code": "SUMMER30", "expiresAt": "Aug 31"},
    }
)
```

**Promotional Email:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbtc8x2q6v1d5n9w4j7h",
    data: {
      discount: "50%",
      code: "UPGRADE50",
      expiresAt: "January 31, 2026",
      currentPlan: "Free",
      upgradePlan: "Pro"
    }
  }
});
```

**Unsubscribe Handler:**
```typescript
app.get('/unsubscribe', async (req, res) => {
  const { token, userId, category } = req.query;

  if (!token || !userId || !category) {
    return res.status(400).send('Missing parameters');
  }

  if (!verifyUnsubscribeToken(String(token), String(userId), String(category))) {
    return res.status(400).send('Invalid link');
  }

  await client.users.preferences.updateOrCreateTopic(String(category), {
    user_id: String(userId),
    topic: { status: "OPTED_OUT" }
  });

  res.send('You have been unsubscribed.');
});
```

---

Promotional messages for sales, upgrades, and marketing campaigns.

## Key Distinction

**Campaign notifications are opt-in only.** Unlike transactional or product notifications, these are promotional messages. Only send them to users who explicitly opted in, record how and when they opted in, and honor opt-outs immediately. Opt-in everywhere also protects list health and deliverability.

## Opt-In Requirements

### What Counts as Opt-In

**Valid:**
- User checks unchecked box: "Send me promotional emails"
- User clicks "Subscribe to newsletter"
- User explicitly requests updates

**Invalid:**
- Pre-checked boxes
- Assumed consent from purchase
- Bundled consent ("By signing up you agree to receive...")

### Implementation

Always check opt-in status before sending campaigns. Skip users who are not opted in.

## Campaign Types

### Sales & Promotions

Subject: Summer Sale - 30% off everything

Include:
- Sale name and discount
- Promo code
- Expiration date
- Featured products
- Required footer (unsubscribe, address)

### Upgrade Promotions

Subject: Upgrade to Pro - 50% off for 3 months

Include:
- Current plan and what they're missing
- Discount offer with code
- Benefits of upgrading (list 3-4)
- Usage-based hook (e.g., "you've used 3 of 3 projects")
- Expiration date

### Event Invitations

Subject: You're invited: Product Launch Webinar

Include:
- Event name, date, time with timezone
- What they'll learn
- Speakers
- Register button
- Note about recording availability

### Seasonal Campaigns

Subject: Black Friday: 40% off Pro

Include:
- Headline with discount
- Code
- Start and end dates
- Countdown urgency

## A/B Testing

### Test Elements

- Subject lines
- Send time
- CTA button text
- Offer amount
- Email design

### Implementation

Assign variants deterministically (e.g., based on user ID) and track which variant was sent for analytics.

Example test:
- Variant A: "30% off - Today only"
- Variant B: "Your exclusive discount inside"

Track: Open rate, click rate, conversion rate

## Segmentation

### By User Type

- Free users: Upgrade to paid
- Pro users: Upgrade to Enterprise
- Churned users: Win-back campaign

### By Behavior

- Users who viewed pricing but didn't upgrade
- Users with high engagement
- Users approaching usage limits

## Frequency & Timing

### Frequency Guidelines

| Campaign Type | Max Frequency |
|---------------|---------------|
| Sales/promotions | 1-2/week |
| Newsletter | 1/week |
| Product updates | 2-4/month |
| Events | As needed |

### Best Send Times

Research varies, but generally:
- **B2B:** Tuesday-Thursday, 9-11 AM
- **B2C:** Varies by audience, test
- **Avoid:** Monday morning, Friday afternoon

## Required Elements

### Marketing Email Requirements

Every marketing email must include:

1. **Physical mailing address**
2. **Unsubscribe link** (functional for at least 30 days after send)
3. **Clear identification as advertisement** (if applicable)
4. **Accurate subject line and sender identification**
5. **Link to your privacy policy**

Example footer:
"You're receiving this because you opted in to marketing emails from Acme. Unsubscribe | Manage preferences. Acme, Inc., 123 Main Street, San Francisco, CA 94102"

## Unsubscribe Handling

### One-Click Unsubscribe

Make unsubscribe simple. Verify token and update user preferences immediately.

### Preference Center

Better than all-or-nothing unsubscribe. Let users choose:
- Product updates (new features, improvements)
- Promotions and offers
- Weekly newsletter
- Event invitations

## Channel Strategy

| Campaign Type | Email | Push | SMS |
|---------------|-------|------|-----|
| Sales/promotions | Yes | Yes* | Yes* |
| Newsletter | Yes | - | - |
| Event invitations | Yes | Yes* | - |
| Product updates | Yes | - | - |

*Only if explicitly opted in for push/SMS marketing

### SMS Campaigns (Extra Caution)

SMS marketing has stricter rules:
- Requires explicit opt-in — never opt-out
- Higher unsubscribe risk
- Reserve for high-value, time-sensitive offers

Only send SMS campaigns to users who explicitly opted in with the date recorded.

## Metrics

### Track

- **Open rate** (email)
- **Click-through rate**
- **Conversion rate**
- **Unsubscribe rate**
- **Revenue attributed**

### Benchmarks

| Metric | Average | Good |
|--------|---------|------|
| Open rate | 20% | 30%+ |
| Click rate | 2.5% | 5%+ |
| Unsubscribe | 0.5% | < 0.3% |
| Conversion | Varies | Track trend |

### If Unsubscribes Are High

- Review frequency (too many emails?)
- Check relevance (right audience?)
- Evaluate value (worth opening?)
- Consider preference center

## Anti-Spam Best Practices

### Do

- Only email opted-in users
- Provide clear unsubscribe
- Honor opt-outs immediately
- Send relevant content
- Monitor engagement metrics

### Don't

- Buy email lists
- Hide unsubscribe links
- Use misleading subject lines
- Email unsubscribed users
- Send from no-reply addresses

## Related

- [Email](../channels/email.md) - Email deliverability
- [Preferences](../guides/preferences.md) - Preference management
- [Re-engagement](./reengagement.md) - Win-back campaigns
