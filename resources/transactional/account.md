# Account Notifications

## Quick Reference

### Rules
- Transactional welcome: NO promotional content (or it becomes marketing)
- Email changed: Send to BOTH old and new email addresses
- Security changes: ALWAYS include "I didn't request this" option
- 2FA disabled: High urgency - send to all channels
- Mask sensitive data: email (j***@example.com), phone (•••• 4567)

### Security-Sensitive Changes
| Change | Channels | Include |
|--------|----------|---------|
| Email changed | Old email + New email | "Secure account" link |
| Password changed | Email + Push | Timestamp, device info |
| 2FA enabled | Email + Push | Backup codes link |
| 2FA disabled | Email + Push + SMS | "Secure account" link |
| New device login | Email + Push | Device, location, IP |

### Required "I Didn't Do This" Link
Include in ALL of these:
- Password changes
- Email changes
- 2FA changes
- New device logins
- Any security-sensitive setting change

### Common Mistakes
- Promotional content in welcome email (reclassifies as marketing)
- Email change only sent to new address (old address owner unaware)
- No "I didn't request this" in security emails
- Exposing full email/phone in notifications (security risk)
- 2FA disabled treated as low priority (it's critical!)
- No confirmation for significant profile changes

### Templates

**Transactional Welcome (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbvs6x9q3v7d1c5n8w2hj",
    data: {
      email: "jane@example.com",
      loginUrl: "https://acme.com/login"
    }
  }
}, {
  headers: { "Idempotency-Key": `welcome-user-123` }
});
```

**Transactional Welcome (Python):**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbvs6x9q3v7d1c5n8w2hj",
        "data": {
            "email": "jane@example.com",
            "loginUrl": "https://acme.com/login",
        },
    },
    extra_headers={"Idempotency-Key": "welcome-user-123"},
)
```

**Email Changed (send to old email):**
```typescript
await client.send.message({
  message: {
    to: { email: "old-email@example.com" },
    template: "nt_01kmrbwb8x2q6v1d4c7n5j9ht",
    data: {
      newEmailMasked: "j***@newdomain.com",
      timestamp: "January 29, 2026 at 2:30 PM",
      secureAccountUrl: "https://acme.com/security"
    }
  }
}, {
  headers: { "Idempotency-Key": `email-changed-user-123-${changeEventId}` }
});
```

**2FA Disabled (critical):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbwj3q6x9v2d5c8n1w4ht",
    data: {
      timestamp: "January 29, 2026 at 2:30 PM",
      secureAccountUrl: "https://acme.com/security"
    },
    routing: { method: "all", channels: ["email", "push", "sms"] }
  }
}, {
  headers: { "Idempotency-Key": `2fa-disabled-user-123-${changeEventId}` }
});
```

---

Best practices for welcome messages, profile updates, and settings notifications.

## Welcome Messages

### Transactional vs Growth

**Transactional welcome:** Confirms account creation, provides essential setup info. No promotional content.

**Growth welcome:** Onboarding sequences, feature discovery. See [Onboarding](../growth/onboarding.md).

### When to Send

Immediately after account creation/email verification.

### Content Requirements

- Confirmation of account creation
- Essential next steps (not promotional)
- Key links (login, settings, support)
- No upsells, discounts, or promotional content

### Email Content

Subject: Welcome to Acme

Include:
- Account email confirmation
- Quick links (sign in, settings, docs, support)
- Reply contact for questions

**What NOT to include:**
- "Use code WELCOME20 for 20% off!"
- "Upgrade to Pro for more features"
- "Check out our latest products"

## Profile Updates

### Email Changed

Send to BOTH old and new email addresses.

**To old email:**

Subject: Your Acme email address was changed

Include:
- Masked new email (e.g., j***@example.com)
- Timestamp of change
- "Secure My Account" button if they didn't make the change

**To new email:**

Subject: Email address updated for your Acme account

Include:
- Confirmation of update
- Security contact if they didn't request it

### Password Changed

Channels: Email + Push

Subject: Your Acme password was changed

Include:
- Timestamp
- Device information
- "Secure My Account" option if they didn't make the change

### Profile Updated

For significant profile changes, send confirmation with:
- What fields changed
- Timestamp
- Link to review settings

## Settings Changes

### Notification Preferences Changed

Subject: Notification preferences updated

Include:
- Confirmation of update
- Link to review settings
- Security note if they didn't make the change

### Two-Factor Authentication

**2FA Enabled:**

Channels: Email + Push

Subject: Two-factor authentication enabled

Include:
- Method enabled (authenticator app or SMS)
- Link to backup codes
- "Secure My Account" if they didn't enable it

**2FA Disabled:**

Higher urgency - Channels: Email + Push + SMS (because this reduces security)

Include:
- Timestamp
- Security concern messaging
- "Secure My Account" button

## Usage & Quota Alerts

### Approaching Limit

Subject: You've used 80% of your monthly API calls

Include:
- Current usage vs limit
- Percentage used
- Estimated time until limit
- Link to usage details
- Link to plan options (keep it informational — a bare "View plans" link is transactional; promotional copy like "Upgrade now and save 20%" crosses into marketing and requires opt-in)

### Limit Reached

Channels: Email + Push + In-app

Include:
- What limit was reached
- Reset date
- Link to plan options (same boundary as above — informational link is fine, promotional upsell is not)
- Impact on service

## Account Deletion

### Deletion Requested

Subject: Account deletion scheduled

Include:
- Deletion date (typically 30 days out)
- Export data link
- Cancel deletion link
- Warning that data cannot be recovered after deletion

### Deletion Complete

Subject: Your Acme account has been deleted

Include:
- Confirmation of deletion
- Feedback request (optional)
- Note that they can create a new account anytime

## Connected Apps / Integrations

### App Connected

Include:
- App name
- Permissions granted
- Timestamp
- Link to manage connected apps

### App Disconnected

Include:
- App name
- Timestamp

## Channel Strategy

| Notification | Email | Push | SMS | Priority |
|--------------|-------|------|-----|----------|
| Welcome | Yes | - | - | Standard |
| Email changed | Yes (both) | - | - | High |
| Password changed | Yes | Yes | - | High |
| 2FA enabled | Yes | Yes | - | High |
| 2FA disabled | Yes | Yes | Yes | Critical |
| Usage warning | Yes | - | - | Standard |
| Usage limit | Yes | Yes | - | High |
| Account deletion | Yes | - | - | High |

## Security Considerations

### Always Include "I Didn't Do This"

For security-sensitive changes:
- Password changes
- Email changes
- 2FA changes
- New device logins

Include a "Secure My Account" button and security contact.

### Mask Sensitive Data

- Email: j***@example.com
- Phone: •••• 4567
- Card: •••• 4242

## Best Practices

### Timing

- Security changes: Immediate
- Profile updates: Immediate
- Usage alerts: As threshold crossed
- Deletion: Immediate + reminder at 7 days

### Confirmation Pattern

Always confirm significant changes:
1. User takes action
2. System processes change
3. Send confirmation with details
4. Include "undo" or "report" option

### Keep Records

Log what notifications were sent for:
- Security audits
- Customer support
- Internal auditing and data-deletion requests

## Related

- [Authentication](./authentication.md) - Password reset, security alerts
- [Preferences](../guides/preferences.md) - User notification preferences
