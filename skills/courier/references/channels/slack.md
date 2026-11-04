# Slack Channel

**Contents:** [Quick Reference](#quick-reference) · [Slack App Setup](#slack-app-setup) · [Handling Interactive Actions](#handling-interactive-actions) · [Courier Integration](#courier-integration) · [Threading](#threading) · [Scheduled Messages](#scheduled-messages) · [Troubleshooting](#troubleshooting) · [Slack in Journeys](#slack-in-journeys) · [Related](#related)

## Quick Reference

### Rules
- Bot token starts with `xoxb-` (not user token `xoxp-`)
- Required bot scopes: `chat:write`, `im:write`, `users:read`, `users:read.email`. Add `chat:write.public` to post in channels the bot hasn't joined
- Use Channel ID (starts with `C`), not channel name
- Slack overrides go in `providers.slack.override.body`, which Courier passes to `chat.postMessage`. `message.channels` keys are channel ids such as `direct_message`, not `slack`
- Journey send nodes: `access_token` must be a runtime reference, never a literal token — see [Slack in Journeys](#slack-in-journeys)

### Common Mistakes
- Exceeding Slack's rate limits (about 1 message per second per channel). Set a [send rate limit](../guides/providers.md#send-rate-limits) on the Slack provider config and Courier queues the excess. It covers the whole config, not one channel

### Templates

**Send DM by Email (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        email: "jane@acme.com"
      }
    },
    content: { title: "Build Complete", body: "Your build finished." }
  }
});
```

**Send to Channel (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: "C0123ABCDEF"
      }
    },
    template: "nt_01kmrby3q6x9v2d5c8n1w4ht"
  }
});
```

**Block Kit Override** (a fragment: the `providers` key of `message`):
```typescript
providers: {
  slack: {
    override: {
      body: {
        blocks: [
          { type: "header", text: { type: "plain_text", text: "Title" } },
          { type: "section", text: { type: "mrkdwn", text: "*Bold* text" } }
        ]
      }
    }
  }
}
```

---

## Slack App Setup

Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps), add the bot scopes from [Rules](#rules), install it to the workspace and copy the Bot User OAuth Token (`xoxb-...`). The Courier Slack integration takes no token. Pass it as `to.slack.access_token`, or store it on the profile as `slack.access_token` beside one target (`channel`, `user_id` or `email`), or on a tenant's `user_profile`.

## Handling Interactive Actions

Courier only posts the message. Button clicks (`action_id`) go to your Slack app's Interactivity Request URL (**Interactivity & Shortcuts** in the app settings), not to Courier. Verify the request with the app's signing secret against the raw body, acknowledge within 3 seconds, and update the message through the payload's `response_url`.

---

## Courier Integration

### Using User Profile Slack Token

```typescript
// If user has connected Slack via OAuth
await client.send.message({
  message: {
    to: { 
      user_id: "user-123" // profile.slack needs access_token plus one of channel, user_id, email
    },
    template: "nt_01kmrbyt6x9q3v7d1c5n8w2hj",
    routing: {
      method: "single",
      channels: ["direct_message"]
    }
  }
});
```

## Threading

### Reply to Thread

Set the parent message's `ts` as `thread_ts` in `providers.slack.override.body`; Courier passes it to `chat.postMessage`.

### Update Existing Message

A `ts` in the override doesn't edit anything. The override body goes to Slack's `chat.postMessage`, which only posts. To update a sent message, set a replacement key (usually `ts`) in the template's Slack channel settings, and Courier updates the message instead of posting a new one. Read the original `ts` from `providers[].reference.ts` on `GET /messages/{message_id}`. See [Updating notifications](https://www.courier.com/docs/integrations/direct-message/slack#updating-notifications).

## Scheduled Messages

```typescript
// Schedule with Courier's delay. Slack's post_at isn't read by chat.postMessage
await client.send.message({
  message: {
    to: { slack: { access_token: process.env.SLACK_BOT_TOKEN, channel: "C0123ABCDEF" } },
    content: { version: "2022-01-01", elements: [{ type: "text", content: "Daily standup reminder!" }] },
    delay: { until: new Date(Date.now() + 60 * 60 * 1000).toISOString() } // 1 hour from now
  }
});
```

A delay can run up to 31 days. See [scheduling.md](../guides/scheduling.md#timestamp-delay).

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "channel_not_found" | Invalid channel ID | Use channel ID (C...), not name |
| "not_in_channel" | Bot not in channel | Add `chat:write.public` scope or invite bot |
| "user_not_found" | Invalid email | Verify email matches Slack account |
| "invalid_auth" | Bad token | Regenerate bot token |

## Slack in Journeys

Journey send nodes deliver to Slack via the node's `to.slack` override — exactly one destination (`channel` ID, `user_id`, or `email`) plus an optional `access_token`. Two rules differ from the Send API: the token must be a **runtime reference** like `{{data.slack_token}}` (a literal `xoxb-...` is rejected; omit it to use the stored profile or tenant token), and the destination never falls back to the journey's user — always set it on the node. Full node shape, examples, and template channel values: [journeys.md](../guides/journeys.md#slack-and-teams-sends).

## Related

- [Journeys](../guides/journeys.md) - Slack send nodes in multi-step flows
- [MS Teams](./ms-teams.md) - Alternative workplace chat channel
- [Multi-Channel](../guides/multi-channel.md) - Routing and fallback across channels
- [Batching](../guides/batching.md) - Batch notifications to channels
- [Throttling](../guides/throttling.md) - Respect Slack rate limits
- [Engagement](../lifecycle-marketing.md) - Alert notification patterns
