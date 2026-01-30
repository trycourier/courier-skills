# Notification Catalog

## Quick Reference

### Rules
- Start with essential transactional notifications first
- Add authentication/security notifications second
- Add engagement notifications based on product needs
- Add growth notifications as you scale
- Before adding any notification, ask: Does user need this? Is it actionable?

### Universal Essential Notifications
Every app needs these:
- Email verification
- Password reset
- Security alerts (new login, password changed)
- Payment confirmation (if applicable)
- Payment failed (if applicable)

### Channel Selection by Category
| Category | Primary | Secondary |
|----------|---------|-----------|
| Transactional | Email | Push |
| Authentication | SMS | Email |
| Engagement | Push | In-app |
| Growth | Email | In-app |
| Marketing | Email | Push (opt-in only) |

### Common Mistakes
- Building all notifications at once (start small)
- Skipping essential transactional notifications
- Over-notifying (causes users to disable notifications)
- No security notifications (new login, password change)
- Same channel strategy for all notification types
- Not considering mobile-first (60%+ read on mobile)

### App Type Quick Guide
| App Type | Start With |
|----------|------------|
| SaaS | Welcome, verify, password reset, payment |
| E-commerce | Order confirm, shipped, delivered, payment |
| Social | Verify, password reset, DM, mention |
| Fintech | Transaction, security, password, OTP |
| Healthcare | Appointment confirm, reminders, check-in |

---

Notification recommendations by app type to help you plan what to build.

## How to Use This

1. Find your app type
2. Review essential vs optional notifications
3. Check channel recommendations
4. Use as a starting point - adapt to your needs

## SaaS / Subscription Apps

### Essential

| Notification | Category | Channels |
|--------------|----------|----------|
| Welcome email | Account | Email |
| Email verification | Auth | Email |
| Password reset | Auth | Email |
| Payment confirmation | Billing | Email |
| Payment failed | Billing | Email → Push → SMS |
| Subscription renewal reminder | Billing | Email |
| Trial ending | Billing | Email + Push |
| Plan changed | Billing | Email |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| Onboarding sequence | Growth | Email |
| Feature announcement | Adoption | Email + In-app |
| Usage warning (approaching limit) | Account | Email + In-app |
| Security alert (new login) | Auth | Email + Push |
| Team member invited | Account | Email |
| Weekly digest | Engagement | Email |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| NPS survey | Engagement | Email |
| Referral prompt | Referral | In-app + Email |
| Upgrade promotion | Campaign | Email |

---

## E-Commerce / Marketplace

### Essential

| Notification | Category | Channels |
|--------------|----------|----------|
| Order confirmation | Orders | Email |
| Shipping notification | Orders | Email + Push |
| Delivery update | Orders | Push + SMS |
| Delivery confirmation | Orders | Email + Push |
| Payment receipt | Billing | Email |
| Password reset | Auth | Email |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| Out for delivery | Orders | Push + SMS |
| Return initiated | Orders | Email |
| Refund processed | Billing | Email |
| Back in stock | Orders | Email + Push |
| Price drop alert | Growth | Email + Push |
| Review request | Engagement | Email |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| Cart abandonment | Re-engagement | Email |
| Wishlist sale | Growth | Email + Push |
| Loyalty points update | Engagement | Email |
| Seasonal sale | Campaign | Email |

---

## Fintech / Banking

### Essential (Higher Security)

| Notification | Category | Channels |
|--------------|----------|----------|
| Transaction confirmation | Billing | Push + Email |
| Large transaction alert | Auth | Push + SMS |
| Password/PIN changed | Auth | Email + Push + SMS |
| New device login | Auth | Email + Push + SMS |
| Account locked | Auth | Email + SMS |
| OTP / 2FA | Auth | SMS |
| Payment failed | Billing | Email + Push |
| Low balance alert | Account | Push + Email |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| Direct deposit received | Billing | Push |
| Bill due reminder | Billing | Email + Push |
| Card expiring | Account | Email |
| Suspicious activity | Auth | Push + SMS |
| Statement ready | Billing | Email |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| Spending insights | Engagement | Email |
| Budget exceeded | Account | Push |
| New feature (security) | Adoption | Email |

---

## Social / Community Platform

### Essential

| Notification | Category | Channels |
|--------------|----------|----------|
| Email verification | Auth | Email |
| Password reset | Auth | Email |
| Direct message | Engagement | Push + In-app |
| Mention | Engagement | Push + In-app |
| Comment on your post | Engagement | Push + In-app |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| New follower | Engagement | In-app |
| Post liked (batched) | Engagement | In-app |
| Friend request | Engagement | Push + In-app |
| Friend joined | Engagement | Push + In-app |
| Your post is trending | Engagement | Push |
| Weekly activity digest | Engagement | Email |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| Birthday reminder | Engagement | Push |
| Suggested connections | Growth | In-app |
| Invite friends | Referral | In-app |

---

## Healthcare / Appointments

### Essential

| Notification | Category | Channels |
|--------------|----------|----------|
| Appointment confirmation | Appointments | Email + SMS |
| Appointment reminder (24hr) | Appointments | Email + SMS |
| Appointment reminder (2hr) | Appointments | SMS + Push |
| Appointment rescheduled | Appointments | Email + SMS |
| Appointment cancelled | Appointments | Email + SMS |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| Appointment reminder (7 day) | Appointments | Email |
| Pre-appointment checklist | Appointments | Email |
| Check-in available | Appointments | SMS + Push |
| Lab results ready | Account | Email + Push |
| Prescription ready | Account | SMS + Push |
| Waitlist availability | Appointments | SMS + Push |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| Health tips | Engagement | Email |
| Annual checkup reminder | Appointments | Email |

**Note:** Healthcare apps should minimize PHI in notifications. Link to secure portal for details.

---

## Developer Tools / API Platform

### Essential

| Notification | Category | Channels |
|--------------|----------|----------|
| Email verification | Auth | Email |
| Password reset | Auth | Email |
| API key created | Auth | Email |
| Payment confirmation | Billing | Email |
| Payment failed | Billing | Email + Push |
| Usage limit warning | Account | Email + In-app |
| Usage limit reached | Account | Email + Push |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| API key expiring | Auth | Email |
| Deprecation warning | Adoption | Email |
| New API version | Adoption | Email |
| Incident notification | Account | Email + Push |
| Status page updates | Account | Email |
| Build/deploy status | Account | Push + Slack |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| Onboarding tips | Growth | Email |
| Documentation updates | Adoption | Email |
| Community digest | Engagement | Email |

---

## Productivity / Project Management

### Essential

| Notification | Category | Channels |
|--------------|----------|----------|
| Mentioned in task/comment | Engagement | Push + In-app |
| Task assigned to you | Engagement | Push + In-app + Email |
| Task due soon | Engagement | Push + In-app |
| Project shared with you | Account | Email |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| Task completed | Engagement | In-app |
| Comment added | Engagement | In-app |
| Weekly summary | Engagement | Email |
| Deadline changed | Engagement | Push + In-app |
| Daily agenda | Engagement | Email + Push |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| Productivity insights | Engagement | Email |
| Team activity digest | Engagement | Email |
| Invite team members | Referral | In-app |

---

## Gaming / Entertainment

### Essential

| Notification | Category | Channels |
|--------------|----------|----------|
| Account verification | Auth | Email |
| Password reset | Auth | Email |
| Purchase confirmation | Billing | Email |

### Recommended

| Notification | Category | Channels |
|--------------|----------|----------|
| Friend request | Engagement | Push |
| Game invite | Engagement | Push |
| Achievement unlocked | Engagement | Push + In-app |
| Event starting soon | Engagement | Push |
| Daily reward available | Engagement | Push |
| Streak at risk | Engagement | Push |

### Optional

| Notification | Category | Channels |
|--------------|----------|----------|
| New content available | Adoption | Push |
| Leaderboard update | Engagement | Push |
| Friend activity | Engagement | Push |
| Special offer | Campaign | Push |

---

## General Best Practices

### Start Small

Don't build all notifications at once:
1. Start with essential transactional
2. Add authentication/security
3. Add engagement based on product needs
4. Add growth notifications as you scale

### Channel Selection Summary

| Category | Primary | Secondary |
|----------|---------|-----------|
| Transactional (orders, billing) | Email | Push |
| Authentication (OTP, security) | SMS | Email |
| Engagement (social, activity) | Push | In-app |
| Growth (onboarding, adoption) | Email | In-app |
| Campaigns (marketing) | Email | Push (opt-in) |

### Don't Over-Notify

Before adding a notification, ask:
1. Does the user need to know this?
2. Is it actionable?
3. What's the right urgency?
4. Will it cause fatigue?

## Related

- [Multi-Channel](./multi-channel.md) - Channel routing strategies
- [Preferences](./preferences.md) - Let users control what they receive
- [Transactional](../transactional/index.md) - Transactional patterns
- [Growth](../growth/index.md) - Growth notification patterns
