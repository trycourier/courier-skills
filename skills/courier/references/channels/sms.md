# SMS Channel

**Contents:** [Quick Reference](#quick-reference) · [Courier Integration](#courier-integration) · [Opt-Out Handling](#opt-out-handling) · [Timing Considerations](#timing-considerations) · [Related](#related)

## Quick Reference

### Rules
- US A2P messaging needs 10DLC registration (it can take a week or more). Unregistered traffic is filtered or blocked by carriers
- Your SMS provider handles STOP, not Courier. Twilio blocks later sends to that number with error 21610, so the message ends UNDELIVERABLE. Mirror opt-outs into preferences (see [Opt-Out Handling](#opt-out-handling))
- SMS requires a configured provider. Add one in [Integrations](https://app.courier.com/integrations) before sending (email works in test mode without this, SMS does not). One AWS SNS integration serves both SMS and push, so it appears as a provider on both channels; its Topic ARN field applies to push only, and a `phone_number` on the profile always wins for SMS

### Templates

**OTP Code (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { phone_number: "+15551234567" },
    content: {
      title: "Your Acme code", // required by the shorthand; SMS sends only the body
      body: "Acme: Your code is 847293. Expires in 10 min. Never share this code."
    }
  }
});
```

---

## Courier Integration

A `user_id` send reaches SMS through `profile.phone_number`, stored in E.164. For an OTP sent SMS-first with an email fallback and an idempotency key, see [transactional.md](../transactional.md#sending-an-otp). For fallback chains, see [multi-channel.md](../guides/multi-channel.md).

## Opt-Out Handling

Your SMS provider answers STOP, START and HELP itself. Take the provider's inbound webhook and write the user's preference, which Courier applies on every send.

### Handle in Your App

With Twilio's Advanced Opt-Out, the Messaging Service's inbound webhook carries `OptOutType` (`STOP`, `START`, or `HELP`). Verify Twilio's signature before trusting the body:

```typescript
// Twilio inbound webhook (form-encoded) -> Courier preference
app.post('/webhooks/twilio-inbound', async (req, res) => {
  if (!twilio.validateRequest(process.env.TWILIO_AUTH_TOKEN!, req.header('X-Twilio-Signature') ?? '', WEBHOOK_URL, req.body)) return res.sendStatus(403);
  const { From, OptOutType } = req.body;
  const userId = await findUserIdByPhone(From); // your own lookup

  if (userId && (OptOutType === 'STOP' || OptOutType === 'START')) {
    // An SMS-only topic, so opting out stops SMS and nothing else
    await client.users.preferences.updateOrCreateTopic(SMS_TOPIC_ID, {
      user_id: userId,
      topic: { status: OptOutType === 'STOP' ? 'OPTED_OUT' : 'OPTED_IN' },
    });
  }

  res.type('text/xml').send('<Response></Response>'); // Twilio already sent the reply
});
```

`OPTED_OUT` blocks every channel on that topic, so keep SMS sends on their own topic. Dropping only SMS from a shared topic takes `has_custom_routing` and `custom_routing`, and where custom routing over the API isn't available, that write returns `402`. See [Preferences API](https://www.courier.com/docs/recipients/preferences/api).

## Timing Considerations

### Quiet Hours

To hold non-urgent SMS outside a window, use a [delivery window](../guides/scheduling.md#delivery-window-business-hours-quiet-hours).

## Related

- [Authentication](../transactional.md) - OTP and 2FA patterns
- [Multi-Channel](../guides/multi-channel.md) - SMS in fallback chains
- [Throttling](../guides/throttling.md) - SMS rate limiting
- [WhatsApp](./whatsapp.md) - Alternative mobile channel
