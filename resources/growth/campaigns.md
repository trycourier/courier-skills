# Campaign Notifications

## Quick Reference

### Rules
- ALWAYS requires explicit opt-in (not pre-checked boxes)
- MUST include physical address (CAN-SPAM)
- MUST include unsubscribe link (functional for 30 days)
- Honor opt-out within 10 business days
- Max frequency: 1-2 promotional emails per week
- SMS campaigns: Express written consent + TCPA compliance
- Push campaigns: Only if user opted into promotional push

### Valid vs Invalid Opt-In
| Valid | Invalid |
|-------|---------|
| User checks unchecked box | Pre-checked boxes |
| "Subscribe to newsletter" click | Assumed from purchase |
| Explicit request for updates | Bundled consent |

### Required Email Elements (CAN-SPAM)
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

**Check Opt-In Before Send:**
```typescript
const prefs = await courier.users.preferences.get(userId);
const marketingPref = prefs.items.find(p => p.topic_id === "marketing");

if (marketingPref?.status !== "OPTED_IN") {
  return; // Skip - not opted in
}

await courier.send({
  message: {
    to: { user_id: userId },
    template: "SUMMER_SALE",
    data: { discount: "30%", code: "SUMMER30", expiresAt: "Aug 31" }
  }
});
```

**Promotional Email:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "UPGRADE_PROMO",
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
  
  // Verify token
  if (!verifyUnsubscribeToken(token)) {
    return res.status(400).send('Invalid link');
  }
  
  // Update preferences
  await courier.users.preferences.update(userId, category, {
    status: "OPTED_OUT"
  });
  
  res.send('You have been unsubscribed.');
});
```

---

Promotional messages for sales, upgrades, and marketing campaigns.

## Key Distinction

**Campaign notifications require explicit opt-in.** Unlike transactional or product notifications, these are promotional messages subject to CAN-SPAM, GDPR, and other regulations.

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

### CAN-SPAM Compliance

Every marketing email must include:

1. **Physical address**
2. **Unsubscribe link** (functional for 30 days)
3. **Clear identification as advertisement** (if applicable)
4. **Accurate subject line**

Example footer:
"You're receiving this because you opted in to marketing emails from Acme. Unsubscribe | Manage preferences. Acme, Inc., 123 Main Street, San Francisco, CA 94102"

### GDPR Compliance (EU)

- Explicit consent required
- Easy withdrawal of consent
- Clear privacy policy link
- Right to data access

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
- TCPA requires express written consent
- Higher unsubscribe risk
- Reserve for high-value, time-sensitive offers

Only send SMS campaigns to users who explicitly opted in with date recorded. See [Compliance](../guides/compliance.md) for consent language requirements and record-keeping.

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

- [Compliance](../guides/compliance.md) - CAN-SPAM, GDPR details
- [Email](../channels/email.md) - Email deliverability
- [Preferences](../guides/preferences.md) - Preference management
- [Re-engagement](./reengagement.md) - Win-back campaigns
