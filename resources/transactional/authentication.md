# Authentication Notifications

## Quick Reference

### Rules
- OTP codes: 6 digits, expire in 5-10 minutes, single use
- Password reset: 1 hour expiry, single use, secure token (UUID v4)
- Email verification: 24-48 hour expiry, allow resend after 60 seconds
- Magic links: 15 minute expiry, single use
- ALWAYS include "I didn't request this" in security emails
- NEVER batch or delay OTP, password reset, or security alert notifications — send them immediately, bypass digests/quiet hours
- Security alerts fan out based on severity — see [Security Alert Channels](#security-alert-channels) below; most events go to email + push, and the highest-severity events (password change, 2FA disabled, suspicious activity) also include SMS

### Rate Limits
| Action | Limit | Lockout |
|--------|-------|---------|
| Password reset | 3/hour | 1 hour |
| OTP request | 5/hour | 1 hour |
| Magic link | 5/hour | 1 hour |
| Verification resend | 3/hour | 30 minutes |

### Security Alert Channels
| Event | Channels |
|-------|----------|
| New device login | Email + Push |
| Password changed | Email + Push + SMS |
| Email changed | Old email + New email + SMS |
| 2FA disabled | Email + Push + SMS |
| Suspicious activity | All channels |

### Common Mistakes
- OTP expiry too long (> 10 minutes is security risk)
- No rate limiting on password reset (abuse vector)
- Missing "I didn't request this" link
- Not invalidating token after use
- Sending OTP via email as primary (SMS preferred)
- No security alert when password/email changes
- Not logging "I didn't request this" clicks

### Templates

**Send OTP (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { phone_number: "+15551234567" },
    content: {
      body: "Your Acme code is 847293. Expires in 10 min. Never share this code."
    }
  }
}, {
  // otpRequestId: row ID from your OTP attempts table. Using it in the key
  // means retries of THIS attempt collapse, while the user's "Resend code"
  // button generates a new otpRequestId → new send.
  headers: { "Idempotency-Key": `otp-user123-${otpRequestId}` },
});
```

**Send OTP (Python):**
```python
# otp_request_id is the row ID from your OTP attempts table.
client.send.message(
    message={
        "to": {"phone_number": "+15551234567"},
        "content": {
            "body": "Your Acme code is 847293. Expires in 10 min. Never share this code."
        },
    },
    extra_headers={"Idempotency-Key": f"otp-user123-{otp_request_id}"},
)
```

**Security Alert (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbv3q6x9v2d5c8n1w4ht",
    data: { device: "Chrome on Windows", location: "New York" },
    routing: { method: "all", channels: ["email", "push", "sms"] }
  }
}, {
  headers: { "Idempotency-Key": `login-alert-user-123-${sessionId}` }
});
```

**Security Alert (Python):**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbv3q6x9v2d5c8n1w4ht",
        "data": {"device": "Chrome on Windows", "location": "New York"},
        "routing": {"method": "all", "channels": ["email", "push", "sms"]},
    },
    extra_headers={"Idempotency-Key": f"login-alert-user-123-{session_id}"},
)
```

---

Best practices for password reset, OTP, verification, and security alerts. See [Transactional Overview](./index.md) for delivery timing requirements.

## Password Reset

### Flow

1. User clicks "Forgot Password"
2. Generate secure token (UUID v4) and store with expiry
3. Send reset email immediately
4. User clicks link → Verify token → Allow password change

### Email Content

Subject: Reset your password for Acme

Include:
- Reset button/link
- Expiration time (e.g., "This link expires in 1 hour")
- User's email address for context
- "I didn't request this" option with security contact

### Best Practices

- **Token expiration:** 1 hour (not too long, not too short)
- **Single use:** Invalidate token after use
- **Secure generation:** UUID v4 or crypto.randomBytes
- **Rate limiting:** Max 3 requests per hour per email
- **Include "I didn't request this":** Always
- **Use idempotency keys:** Prevent duplicate sends

## OTP / 2FA Codes

### Channel Selection

SMS is preferred for OTP because:
- Immediate delivery (< 10 seconds)
- Works without internet
- Higher visibility than email
- Users expect codes via SMS

### SMS Content

Example: "Your Acme verification code is: 847293. Expires in 10 minutes. Don't share this code with anyone."

### Best Practices

- **Code format:** 6 digits (not letters - easier to type)
- **Expiration:** 5-10 minutes
- **Rate limiting:** Max 5 codes per hour
- **Warning:** "Don't share this code"
- **Single use:** Invalidate after use or expiration

### Display in Email (Alternative)

If sending OTP via email, display the code prominently in large, monospace font. Include expiration time below.

## Email Verification

### Flow

1. User signs up with email
2. Account created (unverified)
3. Send verification email immediately
4. User clicks link → Verify token → Mark email verified

### Email Content

Subject: Verify your email for Acme

Include:
- Verify Email button
- Expiration time (24 hours)
- Note that they can ignore if they didn't create an account

### Best Practices

- **Longer expiration:** 24-48 hours (not urgent like password reset)
- **Resend option:** Allow after 60 seconds
- **Clear CTA:** Large, prominent button
- **Reminder:** Send again after 24 hours if not verified

## Magic Links (Passwordless)

### Email Content

Subject: Sign in to Acme

Include:
- Sign In button
- Expiration time (15 minutes)
- Note that link can only be used once
- "I didn't request this" option

## Security Alerts

### New Device / Location Login

**Email Content:**

Subject: New sign-in to your Acme account

Include:
- Device information (browser, OS)
- Location (city, country)
- IP address
- Timestamp
- "Secure My Account" button if it wasn't them

### Alert Types

| Event | Urgency | Channels |
|-------|---------|----------|
| New device login | High | Email + Push |
| Password changed | High | Email + Push + SMS |
| Email changed | Critical | Email (old) + Email (new) + SMS |
| 2FA disabled | Critical | Email + Push + SMS |
| Suspicious activity | Critical | All channels |

### Password Changed Alert

Subject: Your Acme password was changed

Include:
- Timestamp of change
- "If you made this change, no action is needed"
- Reset password link if they didn't make the change
- Security contact information

## Multi-Channel Patterns

### OTP with Fallback

Try SMS first, fall back to email if SMS fails. Use single-channel routing with fallback order: SMS → Email.

### Security Alert Escalation

Channel fan-out is **tiered by event severity** — see the canonical [Security Alert Channels](#security-alert-channels) table above. The highest-severity events (suspicious activity) go to every available channel (Email + Push + SMS + In-app) for maximum reach; lower-severity events like a new device login go to Email + Push only to avoid SMS fatigue. Never downgrade the tier for a specific event; if you want to include SMS on new-device-login in your product, update the table — don't silently diverge.

## Rate Limiting

Enforce the rate limits defined in [Quick Reference > Rate Limits](#rate-limits) above. Always lock out the user after exceeding the limit.

## Troubleshooting

### OTP Not Received

1. Check phone number format (E.164)
2. Verify SMS provider configuration
3. Check carrier filtering (10DLC registration)
4. Offer email alternative

### Reset Link Not Working

1. Check token hasn't expired
2. Verify token hasn't been used
3. Check for URL encoding issues
4. Provide support contact

## Related

- [SMS](../channels/sms.md) - SMS delivery
- [Email](../channels/email.md) - Email deliverability
- [Reliability](../guides/reliability.md) - Idempotency for auth flows
