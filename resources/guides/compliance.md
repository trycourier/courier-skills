# Compliance

## Quick Reference

### Rules by Channel

**Email (CAN-SPAM, GDPR, CASL):**
- Marketing: MUST have opt-in, MUST include unsubscribe link
- MUST include physical mailing address
- Honor opt-out within 10 business days (CAN-SPAM)
- GDPR: Explicit opt-in required, consent must be freely given
- Transactional: No opt-in needed if no promotional content

**SMS (TCPA):**
- Marketing: MUST have express written consent
- MUST disclose message frequency and rates
- MUST support STOP keyword
- Honor opt-outs immediately
- US requires 10DLC registration for A2P
- Violations: $500-$1,500 per message

**Push:**
- Platform permission required (iOS/Android)
- No specific regulations beyond platform rules
- Best practice: Offer in-app preference controls

**WhatsApp:**
- Explicit opt-in required
- Templates must be approved by Meta
- Record consent with timestamp

### Penalties Quick Reference
| Regulation | Penalty |
|------------|---------|
| CAN-SPAM | Up to $53k/email |
| GDPR | €20M or 4% revenue |
| CASL | $10M CAD |
| TCPA | $500-$1,500/message |

### Common Mistakes
- Pre-checked opt-in boxes (invalid under GDPR)
- Adding promotional content to transactional emails (reclassifies as marketing)
- Missing physical address in marketing emails (CAN-SPAM violation)
- No unsubscribe link or hard-to-find unsubscribe
- Sending marketing SMS without written consent
- Not recording consent with timestamp and method
- Ignoring opt-out requests
- Missing 10DLC registration for US SMS

### Consent Record Template

```typescript
interface ConsentRecord {
  userId: string;
  email?: string;
  phone?: string;
  consentedAt: Date;
  method: 'web_form' | 'sms_keyword' | 'verbal' | 'import';
  ipAddress?: string;
  consentText: string;
  categories: string[];
  expiresAt?: Date; // For implied consent (CASL)
}
```

---

Legal requirements for notifications by channel and region.

**Disclaimer:** This is not legal advice. Consult with legal counsel for your specific situation.

## Email Compliance

### CAN-SPAM (United States)

**Applies to:** Commercial email messages

**Requirements:**
1. **Accurate header information** (From, To, Reply-To)
2. **Non-deceptive subject lines**
3. **Physical mailing address** in every email
4. **Clear opt-out mechanism**
5. **Honor opt-out within 10 business days**
6. **Identify as advertisement** (if applicable)

**Transactional emails exempt** if:
- Primary purpose is transactional
- No promotional content included

Example footer: "[Unsubscribe] | [Manage Preferences] | Acme, Inc., 123 Main Street, San Francisco, CA 94102"

### GDPR (European Union)

**Applies to:** Processing data of EU residents

**Requirements:**
1. **Explicit opt-in consent** (not pre-checked boxes)
2. **Consent must be freely given, specific, informed**
3. **Easy to withdraw consent** (as easy as giving it)
4. **Right to access data**
5. **Right to deletion** ("right to be forgotten")
6. **Data breach notification** (within 72 hours)

**Lawful bases for email:**
- **Consent** (marketing)
- **Contract** (transactional)
- **Legitimate interest** (carefully considered)

**Record consent:** Store user ID, email, timestamp, method, IP address, consent text, and categories.

### CASL (Canada)

**Applies to:** Commercial electronic messages to Canadians

**Consent types:**
- **Express consent:** User explicitly opted in
- **Implied consent:** Existing relationship (2 years) or inquiry (6 months)

**Requirements:**
1. **Clear sender identification** (valid for 60 days)
2. **Unsubscribe functional for 60 days**
3. **Process unsubscribe within 10 business days**
4. **Keep consent records 3 years after expiration**

## SMS Compliance

### TCPA (United States)

**Applies to:** SMS and automated calls

**Requirements:**
1. **Express written consent** for marketing SMS
2. **Clear disclosure** of message frequency and rates
3. **Easy opt-out** (STOP keyword)
4. **Honor opt-out immediately**
5. **No SMS to numbers on Do Not Call Registry** (for marketing)

**Transactional SMS:** May not require express consent if:
- Directly related to active transaction
- User provided number for this purpose

**10DLC Registration:** Required for A2P SMS in US. See [SMS Channel](../channels/sms.md) for detailed registration steps and timeline.

### Consent Language Example

"By checking this box, you agree to receive order updates and promotional messages via SMS to the phone number provided. Message frequency varies. Message and data rates may apply. Reply STOP to unsubscribe. Reply HELP for help."

### Opt-Out Handling

Must support standard keywords:
- **Opt-out:** STOP, STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT
- **Opt-in:** START, YES, UNSTOP
- **Help:** HELP, INFO

## Push Notification Compliance

### iOS

- **Permission required** before sending
- **No regulatory requirement** beyond platform rules
- **Apple guidelines:** No spam, relevant content only

### Android

- **Android 13+:** Permission required (like iOS)
- **Pre-Android 13:** Opt-out model
- **Google Play policies:** No deceptive notifications

### Best Practice

Even without legal requirements:
- Respect user preferences
- Don't over-notify
- Provide easy disable in app settings

## WhatsApp Compliance

### Meta Business Policies

- **Opt-in required** before messaging
- **Template approval** for business-initiated messages
- **24-hour window** for session messages
- **No promotional content** in template messages (UTILITY category)

### Opt-In Requirements

Must collect opt-in that:
- Is freely given
- Clearly describes message types
- Is recorded and stored

## In-App Notifications

### Generally Less Regulated

- No specific regulations for in-app
- Good practice: Still offer preferences
- GDPR may apply if processing personal data

## Regional Summary

### United States

| Channel | Primary Regulation | Key Requirement |
|---------|-------------------|-----------------|
| Email | CAN-SPAM | Opt-out mechanism |
| SMS | TCPA | Express written consent |
| Push | Platform rules | Permission prompt |
| Voice | TCPA | Express consent |

### European Union

| Channel | Primary Regulation | Key Requirement |
|---------|-------------------|-----------------|
| Email | GDPR + ePrivacy | Explicit opt-in |
| SMS | GDPR + ePrivacy | Explicit opt-in |
| Push | GDPR | Purpose limitation |
| Any | GDPR | Right to deletion |

### Canada

| Channel | Primary Regulation | Key Requirement |
|---------|-------------------|-----------------|
| Email | CASL | Express/implied consent |
| SMS | CASL + CRTC | Express consent |

## Consent Management

### Record What You Need

For each consent:
- User ID
- Contact info (email or phone)
- Consent type (express/implied)
- Timestamp
- Method (form, checkbox, SMS keyword)
- IP address and user agent (optional)
- Exact consent text
- Categories consented to
- Source (where collected)
- Expiration date (for implied consent)

### Consent Audit Trail

Keep history of all consent changes:
- User ID
- Action (granted, revoked, updated)
- Timestamp
- Categories affected
- Method and IP address

## Data Retention

### By Regulation

| Regulation | Requirement |
|------------|-------------|
| GDPR | Keep only as long as necessary |
| CASL | Keep consent records 3 years after expiration |
| CCPA | Maintain records of requests for 24 months |

### Best Practice

- Define retention periods per data type
- Automatically delete expired data
- Honor deletion requests promptly
- Document your retention policy

## Unsubscribe Requirements

| Regulation | Timing | Duration |
|------------|--------|----------|
| CAN-SPAM | 10 business days | Functional 30 days after send |
| GDPR | Immediately | - |
| CASL | 10 business days | Functional 60 days after send |
| TCPA | Immediately | - |

## Checklist

### Before Sending Marketing Email

- User has opted in
- Consent is recorded with timestamp
- Email includes physical address
- Email includes unsubscribe link
- Unsubscribe is functional
- Subject line is accurate

### Before Sending Marketing SMS

- User has express written consent
- Consent includes frequency disclosure
- STOP keyword works
- 10DLC registration complete (US)
- Phone number validated

### For GDPR Compliance

- Consent is explicit (not pre-checked)
- Purpose is clearly stated
- Withdrawal is easy
- Data access requests can be fulfilled
- Deletion requests can be fulfilled
- Privacy policy is current

## Related

- [Preferences](./preferences.md) - Implementing preference management
- [Email](../channels/email.md) - Email-specific compliance
- [SMS](../channels/sms.md) - SMS/TCPA compliance
- [Campaigns](../growth/campaigns.md) - Marketing compliance
