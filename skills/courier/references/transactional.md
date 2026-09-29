# Transactional Notifications

Notifications triggered by a user action, expected by the recipient, and required to deliver the service, password resets, OTPs, order updates, receipts, appointment reminders, security alerts.

**Courier does all of these.** This file maps each use case to the Courier primitive that implements it. It deliberately does **not** prescribe cadence, copy, or subject lines, those are product decisions, not integration ones.

## Quick Reference

### Rules

- **Use an idempotency key** where a duplicate would be harmful, payments, OTPs, security alerts. Pass it as a header (see [Reliability](./guides/reliability.md)).
- **Email-change alerts go to BOTH addresses**: old and new. The old address is the only channel the legitimate owner still controls.
- **Render times in the recipient's timezone** with the abbreviation (`2:00 PM PST`), never in server time.
- Transactional sends still respect a user's channel-level preferences unless you explicitly override them.

### Use case → Courier primitive

| Use case | Build it with |
|---|---|
| Password reset, magic link, email verification | Single send + [template](./guides/templates.md). Token lifecycle is yours; Courier delivers. |
| OTP / 2FA code | Single send, SMS-first with email fallback, [multi-channel](./guides/multi-channel.md) `routing.method: "single"` |
| Order confirmation, shipping, delivery | Single send per state change, or a [journey](./guides/journeys.md) when a delay or branch is involved |
| Receipt / invoice | Single send + template; [attach the PDF](./channels/email.md#attachments) or link it |
| Dunning (payment failed) | [Journey](./guides/journeys.md): `send` → `delay` → `branch` on paid? → escalate channels → `exit` |
| Appointment reminder ladder | [Journey](./guides/journeys.md) with `delay` nodes (`mode: "until"`), cancelled via `POST /journeys/cancel` when the appointment moves |
| Trial ending / renewal notice | [Journey](./guides/journeys.md) with `delay` + `branch` on converted? |
| Security alert | Single send, fanned across channels by severity, see [Security Alert Channels](#security-alert-channels) |
| Account / settings change | Single send; mask the changed value |
| Usage or quota threshold | Single send from your metering system; use a [throttle](./guides/journeys.md) node if the threshold can flap |
| Back in stock, waitlist opening | Send to a [list or audience](./guides/patterns.md) |

**Cancelling a ladder is the part people miss.** If an appointment is rescheduled or an invoice is paid, the pending reminders must stop. Set a cancelation token on the journey and call `POST /journeys/cancel`. See [Cancelling Runs](./guides/journeys.md#cancelling-runs).

### Rate limits worth enforcing on your side

Courier delivers whatever you send; abuse prevention is yours.

| Action | Suggested limit | Lockout |
|--------|-------|---------|
| Password reset | 3/hour | 1 hour |
| OTP request | 5/hour | 1 hour |
| Magic link | 5/hour | 1 hour |
| Verification resend | 3/hour | 30 minutes |

<a id="security-alert-channels"></a>

### Security Alert Channels

Fan out by severity. The highest-severity events warrant interrupting the user.

| Event | Channels |
|-------|----------|
| New device login | Email + Push |
| Password changed | Email + Push + SMS |
| Email changed | Old email + New email + SMS |
| 2FA disabled | Email + Push + SMS |
| Suspicious activity | All channels |

### Common mistakes

- Batching or quiet-hour-delaying an OTP (breaks the flow and the security model)
- Sending an email-change alert only to the new address
- Echoing a full email or phone number in a security notification
- Leaving reminder journeys running after the triggering event resolved
- Adding a promotional footer to a receipt
- Omitting the timezone abbreviation on a scheduled-event reminder

---

## Sending an OTP

SMS first, email as fallback, idempotent so a double-submit can't send two codes.

```typescript
await client.send.message({
  message: {
    to: { user_id: userId },
    template: "nt_otp_template_id",
    data: { code, expires_in_minutes: 10 },
    routing: { method: "single", channels: ["sms", "email"] },
  },
}, {
  headers: { "Idempotency-Key": `otp-${userId}-${requestId}` },
});
```

```python
client.send.message(
    message={
        "to": {"user_id": user_id},
        "template": "nt_otp_template_id",
        "data": {"code": code, "expires_in_minutes": 10},
        "routing": {"method": "single", "channels": ["sms", "email"]},
    },
    extra_headers={"Idempotency-Key": f"otp-{user_id}-{request_id}"},
)
```

`routing.method: "single"` delivers to the **first** channel that works, the fallback semantics you want. `"all"` would send the code twice. See [Multi-Channel](./guides/multi-channel.md).

## A security alert with masked values

```typescript
const maskEmail = (e: string) => {
  const [user, domain] = e.split("@");
  return `${user[0]}${"*".repeat(Math.max(user.length - 1, 3))}@${domain}`;
};

await client.send.message({
  message: {
    to: { user_id: userId },
    template: "nt_security_alert_template_id",
    data: {
      event: "password_changed",
      masked_email: maskEmail(user.email),   // j***@example.com
      ip_city: geo.city,                     // never the raw IP
      occurred_at: new Date().toISOString(),
      not_me_url: `https://app.example.com/security/report?t=${reportToken}`,
    },
    routing: { method: "all", channels: ["email", "push", "sms"] },
  },
}, {
  headers: { "Idempotency-Key": `sec-${userId}-${eventId}` },
});
```

Note `routing.method: "all"` here, for a security alert you *want* every channel, unlike the OTP above.

## A dunning sequence

Escalate channels over time and stop the moment payment succeeds. Full node reference in [Journeys](./guides/journeys.md).

```
[trigger] → [send: email]
          → [delay P3D] → [branch: paid?] ─ yes → [exit]
                                          └ no  → [send: email + push]
          → [delay P3D] → [branch: paid?] ─ yes → [exit]
                                          └ no  → [send: all channels]
```

Set a cancelation token like `dunning-{{data.invoice_id}}` on the journey, then call `client.journeys.cancel({ cancelation_token: "dunning-inv-4821" })` from your payment webhook. Cancelling beats waiting for the next `branch` to evaluate.

## Related

- [Journeys](./guides/journeys.md), delays, branches, cancellation for any multi-step sequence
- [Multi-Channel](./guides/multi-channel.md), `routing.method`, fallback vs fan-out, provider failover
- [Reliability](./guides/reliability.md), idempotency keys, retries, delivery statuses, webhook verification
- [Templates](./guides/templates.md), creating and publishing the templates these sends reference
- [Preferences](./guides/preferences.md), how user preferences interact with transactional sends
- [Lifecycle Marketing](./lifecycle-marketing.md), proactive sends: onboarding, adoption, win-back, campaigns
