# Microsoft Teams Channel

**Contents:** [Quick Reference](#quick-reference) · [Setup](#setup) · [Courier Integration](#courier-integration) · [Handling Action.Execute Responses](#handling-actionexecute-responses) · [Proactive Messaging](#proactive-messaging) · [Troubleshooting](#troubleshooting) · [Teams in Journeys](#teams-in-journeys) · [Related](#related)

## Quick Reference

### Rules
- Courier sends to Teams only through a Bot Framework bot. `ms_teams` has no field for an incoming-webhook or Workflows URL, so don't use one
- Channel sends need the Teams app installed in that team. Uploading it covers personal chats only
- Teams renders Adaptive Cards up to version 1.6. A card with `Action.Execute` needs version 1.5 or later
- Graph permissions are needed only to address by `email` or `channel_name`: `ChannelSettings.Read.All`, `TeamSettings.Read.All`, `User.Read.All` (Application, admin consent). Sends by `user_id`, `channel_id` or `conversation_id` need none
- Journey send nodes: address Teams via `to.ms_teams`; most targets need `service_url` and/or `tenant_id` — see [Teams in Journeys](#teams-in-journeys)

### Templates

**Send to a Channel (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { ms_teams: { tenant_id: TENANT_ID, service_url: SERVICE_URL, channel_id: "19:abc123..." } },
    content: { title: "Build Complete", body: "Build #456 succeeded." }
  }
});
```

**With an Adaptive Card** (built in a Jsonnet block in the template's Teams channel, values in `data`):
```typescript
await client.send.message({
  message: {
    to: { ms_teams: { tenant_id: TENANT_ID, service_url: SERVICE_URL, channel_id: "19:abc123..." } },
    template: "nt_01kmrby3q6x9v2d5c8n1w4ht",
    data: { env: "production", version: "v2.3.1" }
  }
});
```

The only documented Teams provider override is `providers.msteams.override.config` (`appId`, `appPassword` for one send). The provider key is `msteams`. The recipient key stays `ms_teams`.

---

## Setup

Courier sends to Teams through a Bot Framework bot. You create an Azure app registration, a Teams app to install, and the bot, then add the bot's App ID and client secret to Courier. Full steps: [Microsoft Teams integration](https://www.courier.com/docs/integrations/direct-message/microsoft-teams).

Setup creates two app registrations. The first (multitenant) only links the Teams app in the Developer Portal. The bot you add under Developer Portal > Tools > Bot Management gets its own registration. Add the Graph permissions and the client secret on the bot's registration. Give Courier that registration's Application (client) ID as App ID and the secret's Value as App Password.

## Courier Integration

A `channel_id` target can be swapped for `user_id`, `conversation_id` or `email`; the [Templates](#templates) above show a channel send and a card send. Build the card in a Jsonnet block in the template's Teams channel (paste the JSON from the [Adaptive Card Designer](https://adaptivecards.io/designer/)) and pass its values in `data`, not the card itself.

### Via Bot (User DM)

```typescript
await client.send.message({
  message: {
    to: {
      ms_teams: {
        tenant_id: process.env.AZURE_TENANT_ID,
        service_url: "https://smba.trafficmanager.net/...",
        user_id: "29:1abc..." // Teams user ID
      }
    },
    template: "nt_01kmrbyt6x9q3v7d1c5n8w2hj",
    data: {
      taskName: "Review PR #123",
      assignedBy: "Bob"
    }
  }
});
```

## Handling Action.Execute Responses

Courier only sends the card. An `Action.Execute` click goes to your own bot's messaging endpoint as an `invoke` activity named `adaptiveCard/action`, with the button's `data` at `activity.value.action.data`. Your bot service (registered in Azure Bot Service, messaging endpoint set to your server) handles it, verifies the Bot Framework JWT before trusting `activity.from` (for example with botbuilder's `CloudAdapter`), and can return a replacement card (`type: "application/vnd.microsoft.card.adaptive"`).

---

## Proactive Messaging

### Send to an existing conversation

Courier opens the conversation itself for `user_id`, `email` and `channel_id` (send `tenant_id` with a `user_id`, since Teams needs it to open a personal chat). Store a `conversation_id` only to post into an existing conversation, such as a group chat, and send it in `to.ms_teams` with `tenant_id` and `service_url`.

### Reply in a thread

To reply under an earlier channel message, send `to.ms_teams` with `reply_to_activity_id` and `conversation_id` (plus `tenant_id` and `service_url`), taking `activityId` and `conversationId` from that send's `provider:sent` event, with no need to wait for `DELIVERED`. Channels only, not 1:1 or group chats. `reply_to_activity_id` isn't in the Node SDK 10 recipient types, so send the body as JSON or widen the type. See [Thread replies](https://www.courier.com/docs/integrations/direct-message/microsoft-teams#thread-replies).

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 400 from Teams | Invalid card JSON | Validate in Card Designer |
| 401 | App not installed in the team, wrong or expired bot credentials, the Teams app ID or the other registration's ID in Courier, a single-tenant app registration, or no `tenant_id` | Install the app in the team, use the bot registration's App ID and secret Value, use a multitenant registration, send `tenant_id` |
| `tenant_id is required when using 'email' or 'channel_name'` | No `tenant_id` | Send `tenant_id`, or put it in the `service_url` path |
| Card not rendering | Unsupported version | Use version 1.6 or lower |

## Teams in Journeys

Journey send nodes deliver to Teams via the node's `to.ms_teams` override — exactly one target: `channel_id`, `channel_name` with `team_id`, `user_id`, or `email`. Most targets also need `service_url` and/or `tenant_id` (the **Microsoft** tenant, not your Courier tenant), and `conversation_id`/`reply_to_activity_id` are not supported on journey nodes. Full node shape, rules, examples, and template channel values: [journeys.md](../guides/journeys.md#slack-and-teams-sends).

## Related

- [Journeys](../guides/journeys.md) - Teams send nodes in multi-step flows
- [Slack](./slack.md) - Alternative workplace chat channel
- [Multi-Channel](../guides/multi-channel.md) - Routing and fallback across channels
- [Reliability](../guides/reliability.md) - Retries and delivery statuses
- [Batching](../guides/batching.md) - Batch notifications to channels
- [Throttling](../guides/throttling.md) - Rate limit management
