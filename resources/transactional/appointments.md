# Appointment Notifications

## Quick Reference

### Rules
- Confirmation: Send within 1 minute of booking
- ALWAYS display times in user's local timezone
- ALWAYS include timezone abbreviation (e.g., "2:00 PM PST")
- Include calendar links (Google, Outlook, .ics)
- SMS reminders: Keep under 160 characters
- Virtual appointments: Include join link prominently

### Reminder Schedule
| Timing | Channels | Purpose |
|--------|----------|---------|
| 7 days before | Email | Allow rescheduling |
| 24 hours before | Email + SMS | Final preparation |
| 2 hours before | SMS + Push | Immediate reminder |
| 15 min before (virtual) | Push | Join call reminder |

### Required Fields
| Notification | Required |
|--------------|----------|
| Confirmation | Date, time, timezone, location/link, provider, calendar links |
| Reminder | Date, time, location/link, confirm/reschedule option |
| Reschedule | Old time, new time, provider, calendar links |
| Virtual join | Join link, password (if any), "join 5 min early" note |

### Common Mistakes
- Missing timezone (user in different timezone gets wrong time)
- No calendar links (user has to manually add)
- SMS reminder over 160 chars (gets split, costs more)
- No easy reschedule option
- Virtual: Join link buried in text
- No pre-appointment checklist email
- Missing no-show follow-up

### Templates

**Booking Confirmation:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "APPOINTMENT_CONFIRMED",
    data: {
      date: "January 30, 2026",
      time: "2:00 PM PST",
      provider: "Dr. Smith",
      location: "123 Medical Center",
      calendarLinks: { google: "...", outlook: "...", ics: "..." }
    }
  }
});
```

**24-Hour Reminder:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "APPOINTMENT_REMINDER_24H",
    data: {
      date: "Tomorrow",
      time: "2:00 PM PST",
      provider: "Dr. Smith",
      location: "123 Medical Center"
    },
    routing: { method: "all", channels: ["email", "sms"] }
  }
});
```

**SMS Reminder (under 160 chars):**
```
Acme: Reminder - Appt with Dr. Smith tomorrow at 2pm. 123 Medical Center. Reply Y to confirm.
```

---

Best practices for booking confirmations, reminders, and rescheduling notifications.

## Appointment Lifecycle

| Stage | Notification | Channels |
|-------|--------------|----------|
| Booked | Confirmation | Email |
| 7 days before | Reminder | Email |
| 24 hours before | Reminder | Email + SMS |
| 2 hours before | Reminder | SMS + Push |
| 15 min before (virtual) | Join reminder | Push |
| After | Follow-up | Email |

## Booking Confirmation

### Timing

Send **immediately** after booking (within 1 minute).

### Content Requirements

- Appointment date and time (with timezone)
- Location or video link
- Provider/staff name (if applicable)
- What to bring/prepare
- Cancellation/reschedule policy
- Add to calendar links
- Contact information

### Email Content

Subject: Appointment confirmed - January 30 at 2:00 PM

Include:
- Confirmation checkmark
- Date, time, timezone
- Location with address or video link
- Provider name
- Calendar links (Google, Outlook, .ics download)
- What to bring section
- Reschedule/Cancel buttons
- Cancellation policy

### Virtual Appointments

For video appointments, include:
- Join link prominently displayed
- Video password (if applicable)
- "Click the link 5 minutes before" instruction

## Reminders

### Reminder Strategy

| Timing | Channels | Purpose |
|--------|----------|---------|
| 7 days before | Email | Allow rescheduling |
| 24 hours before | Email + SMS | Final preparation |
| 2 hours before | SMS + Push | Immediate reminder |
| 15 minutes before | Push (virtual only) | Join call reminder |

### 24-Hour Reminder

**Email:** Full details with date, time, location, provider, and what to bring.

**SMS:** Keep under 160 characters. Example: "Acme: Reminder - Your appointment with Dr. Johnson is tomorrow at 2:00 PM. Location: 123 Main St. Reply HELP for info."

### 2-Hour Reminder

**SMS:** Brief reminder with essential details.

**Push:** Title "Appointment in 2 hours" / Body "Dr. Johnson at 2:00 PM - 123 Main St" / Action "Get Directions"

### Virtual Appointment - 15 Minutes

**Push only:** Title "Your appointment starts in 15 minutes" / Body "Tap to join your video call with Dr. Johnson" / Action opens video link.

## Rescheduling

### User Initiated

Subject: Appointment rescheduled to February 3 at 10:00 AM

Include:
- Previous date/time (crossed out)
- New date/time (highlighted)
- Location and provider
- Add to calendar link
- Reschedule/Cancel buttons for further changes

### Provider Initiated

Channels: Email + SMS + Push (higher urgency)

Subject: Your appointment needs to be rescheduled

Include:
- Apology for inconvenience
- Previous date/time
- Reason (briefly)
- Available alternative times
- Reschedule button
- Phone number to call

## Cancellation

### Confirmation

Subject: Appointment canceled - January 30 at 2:00 PM

Include:
- Canceled appointment details
- Provider name
- Refund info (if applicable)
- Rebook button

## Waitlist

### Added to Waitlist

Include:
- Requested date
- Provider
- Position on waitlist
- Estimated wait time

### Slot Available

High priority - user needs to act quickly. Channels: Email + SMS + Push.

Include:
- Available date/time
- Provider name
- Time limit to claim (e.g., "Book within 4 hours")
- Book now button

Push example: "A slot opened up! Dr. Johnson on Feb 1 at 3PM. Book now - expires in 4 hours."

## Pre-Appointment

### Preparation Instructions

Send 2-3 days before.

Include:
- Checklist of tasks (e.g., complete intake form, upload documents)
- Links to forms
- Deadline for completion

### Check-In Available

For locations with digital check-in.

Channels: Email + Push

Include:
- When check-in opens (e.g., "30 minutes before")
- Check-in link

## No-Show Handling

Subject: We missed you at your appointment

Include:
- Missed appointment details
- Understanding tone ("If something came up, we understand")
- Rebook button
- No-show fee info (if applicable)
- Contact option

## Channel Strategy

| Notification | Email | SMS | Push | Timing |
|--------------|-------|-----|------|--------|
| Booking confirmation | Yes | - | - | Immediate |
| 7-day reminder | Yes | - | - | 7 days before |
| 24-hour reminder | Yes | Yes | - | 24 hours before |
| 2-hour reminder | - | Yes | Yes | 2 hours before |
| 15-min reminder (virtual) | - | - | Yes | 15 min before |
| Reschedule needed | Yes | Yes | Yes | Immediate |
| Waitlist slot | Yes | Yes | Yes | Immediate |

## Best Practices

### Time Zones

Always display times in user's local timezone. Include timezone abbreviation (e.g., "2:00 PM PST").

### Calendar Links

Include multiple calendar options:
- Google Calendar
- Outlook/Office 365
- Apple Calendar (.ics download)

### SMS Length

Keep SMS reminders under 160 characters to avoid splitting.

### Reduce No-Shows

Studies show:
- SMS reminders reduce no-shows by 30-40%
- Multiple touchpoints (7d + 24h + 2h) most effective
- Include easy reschedule option

## Related

- [SMS](../channels/sms.md) - SMS reminder best practices
- [Push](../channels/push.md) - Push notification timing
- [Multi-Channel](../guides/multi-channel.md) - Reminder channel strategy
