# Referral Notifications

## Quick Reference

### Rules
- State rewards clearly: "You both get $10"
- Explain qualification: "When they make a purchase"
- Referrer consented by sharing; referee needs separate consent
- Require qualification action to prevent fraud (purchase, activity)
- Prompt sharing after positive moments (achievement, upgrade)
- Include easy sharing: pre-written messages, multiple channels

### Referral Flow
```
Referrer shares → Referee signs up → Referee qualifies → Both notified
```

### Notification Triggers
| Event | Notify | Channels |
|-------|--------|----------|
| Invite sent | Referrer (confirmation) | In-app only |
| Referee signed up | Referrer | Push + In-app |
| Referee qualified | Both | Email + Push + In-app |
| Milestone reached | Referrer | Email + Push + In-app |
| Leaderboard change | Referrer | Push |

### Common Mistakes
- Unclear reward structure ("refer a friend for rewards!")
- No qualification requirement (fraud abuse)
- Prompting share at wrong time (before user has value)
- Missing easy sharing options (copy link, social buttons)
- Not celebrating milestone achievements
- Reward notification without explaining how to use it

### Templates

**Referral Signed Up (to referrer):**
```typescript
await courier.send({
  message: {
    to: { user_id: "referrer-123" },
    content: {
      title: "Bob signed up!",
      body: "They need to make a purchase for you both to earn $10."
    },
    routing: { method: "all", channels: ["push", "inbox"] }
  }
});
```

**Referral Qualified (to referrer):**
```typescript
await courier.send({
  message: {
    to: { user_id: "referrer-123" },
    template: "REFERRAL_REWARD_EARNED",
    data: {
      refereeName: "Bob",
      rewardAmount: "$10",
      totalEarned: "$50",
      referralLink: "https://acme.com/refer/abc123"
    },
    routing: { method: "all", channels: ["email", "push", "inbox"] }
  }
});
```

**Share Prompt (after positive moment):**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    content: {
      title: "Share the love!",
      body: "You just hit 100 tasks. Invite friends and you both get $10."
    },
    routing: { method: "single", channels: ["inbox"] }
  }
});
```

---

Drive viral growth through referral programs and social sharing.

## Referral Program Types

| Type | Mechanics | Best For |
|------|-----------|----------|
| Two-sided | Both referrer and referee get reward | Consumer apps |
| One-sided | Only referrer gets reward | B2B, high-value |
| Milestone | Rewards unlock at referral counts | Building advocates |
| Leaderboard | Top referrers get special rewards | Competitive users |

## Referral Flow

1. Referrer shares link/code
2. Referee clicks and signs up
3. Referee qualifies (completes action like purchase)
4. Both parties notified of rewards

### Qualification Validation

Always require a qualification action before issuing rewards to prevent fraud:

```typescript
interface Referral {
  referrerId: string;
  refereeId: string;
  refereeEmail: string;
  signedUpAt: Date;
  qualifiedAt?: Date;
  rewardIssuedAt?: Date;
}

async function onRefereeAction(
  referral: Referral,
  action: "signup" | "purchase" | "activation"
): Promise<void> {
  if (action === "signup") {
    // Notify referrer their friend signed up (no reward yet)
    await courier.send({
      message: {
        to: { user_id: referral.referrerId },
        content: {
          title: `${referral.refereeEmail} signed up!`,
          body: "They need to make a purchase for you both to earn $10.",
        },
        routing: { method: "all", channels: ["push", "inbox"] },
      },
    });
  }

  if (action === "purchase" && !referral.qualifiedAt) {
    // Validate against fraud rules before issuing reward
    const isValid = await validateReferral(referral);
    if (!isValid) return;

    referral.qualifiedAt = new Date();
    await issueReward(referral.referrerId, "$10");
    await issueReward(referral.refereeId, "$10");

    // Notify both parties
    await courier.send({
      message: {
        to: { user_id: referral.referrerId },
        template: "REFERRAL_REWARD_EARNED",
        data: {
          refereeName: referral.refereeEmail,
          rewardAmount: "$10",
        },
        routing: { method: "all", channels: ["email", "push", "inbox"] },
      },
    });
  }
}
```

### Basic Fraud Prevention

```typescript
async function validateReferral(referral: Referral): Promise<boolean> {
  // Same IP address as referrer
  const referrerIp = await getSignupIp(referral.referrerId);
  const refereeIp = await getSignupIp(referral.refereeId);
  if (referrerIp === refereeIp) return false;

  // Referrer hit daily/monthly limit
  const recentReferrals = await getReferralCount(referral.referrerId, "30d");
  if (recentReferrals >= 25) return false;

  // Referee signed up too quickly after link click (bot)
  const signupLatency = referral.signedUpAt.getTime() - Date.now();
  if (signupLatency < 5000) return false; // Under 5 seconds

  return true;
}
```

## Inviting / Sharing

### Invite Email

Subject: Jane thinks you'd love Acme

Include:
- Personal intro from referrer
- Quote or message from referrer
- Reward for signing up
- CTA button: "Accept [Name]'s Invite"

### Share Reminder

Prompt users to share after positive moments (milestone, achievement, upgrade).

Channel: In-app

Include:
- Achievement they just reached
- Referral link
- Reward reminder (e.g., "You both get $10")
- Share buttons (Twitter, LinkedIn, Copy Link)

## Reward Notifications

### Referral Signed Up

When referee signs up (but hasn't qualified yet).

Channel: In-app + Push

Include:
- Who signed up
- Status update
- What needs to happen for reward (e.g., "They need to complete a purchase")

Push example: "Bob signed up using your link! They need to make a purchase for you both to earn your $10 credit."

### Referral Qualified

When referee completes qualifying action.

Channel: Email + In-app + Push

**Email:**

Subject: You earned $10! Thanks for referring Bob

Include:
- Reward amount
- How it's applied
- Total earned from referrals
- Referral link to keep sharing

**Push:**

"You earned $10! Bob made a purchase. Your credit has been applied."

### Referee Welcome

Subject: Welcome! Your $10 credit is ready

Include:
- Welcome message mentioning referrer
- Reward amount and that it's applied
- CTA to start exploring
- Their own referral link to continue the loop

## Milestone Programs

### Milestone Achieved

Define milestones with increasing rewards:
- 1 referral: $10 credit
- 5 referrals: Free month
- 10 referrals: Lifetime discount
- 25 referrals: VIP status

Channel: Email + In-app + Push

Subject: 5 referrals! You earned a free month

Include:
- Achievement
- Reward earned
- Total rewards to date
- Next milestone and reward

### Progress Update

Subject: 2 more referrals until your free month!

Include:
- Current count vs target
- Progress bar visual
- CTA to share

## Leaderboard Notifications

### Weekly Leaderboard Update

Subject: You're #12 on the referral leaderboard

Include:
- Current position
- Top referrers
- Prize for top performers
- How many referrals to move up
- CTA to share

### Position Change

When user moves up in leaderboard.

Channel: Push

Example: "You moved up to #8! 2 more referrals and you're in the top 5."

## Social Proof / FOMO

### Others Are Sharing

Subject: Your friends are earning rewards

Include:
- Total rewards earned by referrers this month
- Examples of what others earned
- User's own referral link
- Reward reminder

## Channel Strategy

| Notification | Email | Push | In-App |
|--------------|-------|------|--------|
| Invite sent confirmation | - | - | Yes |
| Referral signed up | Yes | Yes | Yes |
| Reward earned | Yes | Yes | Yes |
| Milestone achieved | Yes | Yes | Yes |
| Leaderboard update | Yes | - | - |
| Position change | - | Yes | - |
| Share prompt | - | - | Yes |

## Best Practices

### Clear Value Proposition

- State rewards clearly: "You both get $10"
- Explain how to earn: "When they make a purchase"
- Show progress: "2 more until free month"

### Make Sharing Easy

- Pre-written share messages
- Multiple channels (email, Twitter, LinkedIn, copy link)
- Mobile-friendly sharing

### Timely Prompts

Share prompts work best after:
- User achieves something
- User has been active for a while
- User upgrades or makes purchase

### Prevent Fraud

- Require qualification action (purchase, activity threshold) before issuing rewards
- Limit referrals per user (e.g., 25/month)
- Detect suspicious patterns (same IP, rapid signups, disposable emails)
- See fraud validation code in the [Referral Flow](#referral-flow) section above

## Related

- [Onboarding](./onboarding.md) - Welcome referred users
- [Engagement](./engagement.md) - Activity after referral
- [Campaigns](./campaigns.md) - Promotional referral campaigns
