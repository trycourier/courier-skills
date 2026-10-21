# Microsoft Teams Channel

## Quick Reference

### Rules
- Courier sends to Teams through a Bot Framework bot. The Courier docs don't cover Teams incoming webhooks or Workflows webhooks, and `ms_teams` has no webhook URL field
- Channel sends need the Teams app installed in that team. Uploading it covers personal chats only
- Adaptive Card version: use 1.4 or lower for compatibility
- Card JSON must be valid - test in Adaptive Card Designer first
- Graph permissions are needed only to address by `email` or `channel_name`: `ChannelSettings.Read.All`, `TeamSettings.Read.All`, `User.Read.All` (Application, admin consent). Sends by `user_id`, `channel_id` or `conversation_id` need none
- Use FactSet for key-value data display
- Limit to 2-3 action buttons maximum
- Journey send nodes: address Teams via `to.ms_teams`; most targets need `service_url` and/or `tenant_id` — see [Teams in Journeys](#teams-in-journeys)

### Common Mistakes
- Using Adaptive Card version > 1.4 (won't render)
- Invalid card JSON (returns 400 error)
- App not installed in the target team (channel sends fail with 401)
- Missing Graph permissions when addressing by `email` or `channel_name`
- Not testing cards in Adaptive Card Designer first
- Too many buttons (cluttered, confusing)

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

**Send to a Channel (Python):**
```python
import os

client.send.message(
    message={
        "to": {"ms_teams": {"tenant_id": TENANT_ID, "service_url": SERVICE_URL, "channel_id": "19:abc123..."}},
        "content": {"title": "Build Complete", "body": "Build #456 succeeded."},
    }
)
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

Best practices for sending Microsoft Teams notifications with Adaptive Cards.

## Setup

Courier sends to Teams through a Bot Framework bot. You create an Azure app registration, a Teams app to install, and the bot, then add the bot's App ID and client secret to Courier. Full steps: [Microsoft Teams integration](https://www.courier.com/docs/integrations/direct-message/microsoft-teams).

## Azure AD App Registration

### Create App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. App registrations → New registration
3. Name: "Acme Notifications"
4. Supported account types: "Accounts in any organizational directory"
5. Redirect URI: Leave blank for now

### Add API Permissions (only for `email` or `channel_name`)

Microsoft Graph permissions, added as Application permissions:
- `ChannelSettings.Read.All`
- `TeamSettings.Read.All`
- `User.Read.All`

An administrator must grant admin consent. Sends by `user_id`, `channel_id` or `conversation_id` skip this step.

### Create Client Secret

1. Certificates & secrets → New client secret
2. Copy the secret value immediately

## Adaptive Cards

Adaptive Cards are Microsoft's cross-platform card format.

### Basic Structure

```json
{
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "TextBlock",
      "text": "Notification Title",
      "weight": "bolder",
      "size": "large"
    },
    {
      "type": "TextBlock",
      "text": "Notification body text"
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "View Details",
      "url": "https://acme.com/details"
    }
  ]
}
```

### Common Elements

**TextBlock** - Display text

```json
{
  "type": "TextBlock",
  "text": "Hello, **World**!",
  "wrap": true,
  "weight": "bolder",
  "size": "medium",
  "color": "accent"
}
```

**FactSet** - Key-value pairs

```json
{
  "type": "FactSet",
  "facts": [
    { "title": "Status:", "value": "Complete" },
    { "title": "Duration:", "value": "2m 34s" },
    { "title": "Environment:", "value": "Production" }
  ]
}
```

**ColumnSet** - Multi-column layout

```json
{
  "type": "ColumnSet",
  "columns": [
    {
      "type": "Column",
      "width": "auto",
      "items": [
        {
          "type": "Image",
          "url": "https://acme.com/avatar.png",
          "size": "small",
          "style": "person"
        }
      ]
    },
    {
      "type": "Column",
      "width": "stretch",
      "items": [
        {
          "type": "TextBlock",
          "text": "Jane Doe",
          "weight": "bolder"
        },
        {
          "type": "TextBlock",
          "text": "Deployed to production",
          "spacing": "none"
        }
      ]
    }
  ]
}
```

### Actions

**OpenUrl** - Link button

```json
{
  "type": "Action.OpenUrl",
  "title": "View Details",
  "url": "https://acme.com/details/123"
}
```

**Submit** - Interactive button (requires bot)

```json
{
  "type": "Action.Submit",
  "title": "Approve",
  "data": {
    "action": "approve",
    "requestId": "req-123"
  }
}
```

## Courier Integration

### Send to a Channel

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

await client.send.message({
  message: {
    to: {
      ms_teams: {
        tenant_id: process.env.AZURE_TENANT_ID,
        service_url: process.env.TEAMS_SERVICE_URL,
        channel_id: "19:abc123..."      // or user_id / conversation_id / email
      }
    },
    content: {
      title: "Build Complete",
      body: "Build #456 completed successfully."
    }
  }
});
```

### With an Adaptive Card

Build the card in a Jsonnet block in the template's Teams channel (paste the JSON from the [Adaptive Card Designer](https://adaptivecards.io/designer/)), and pass the values in `data`:

```typescript
await client.send.message({
  message: {
    to: {
      ms_teams: {
        tenant_id: process.env.AZURE_TENANT_ID,
        service_url: process.env.TEAMS_SERVICE_URL,
        channel_id: "19:abc123..."      // or user_id / conversation_id / email
      }
    },
    template: "nt_01kmrby3q6x9v2d5c8n1w4ht",
    data: { env: "production", version: "v2.3.1", deployedBy: "Jane Doe" }
  }
});
```

The only documented Teams provider override is `providers.msteams.override.config` (`appId`, `appPassword` for one send). The provider key is `msteams`. The recipient key stays `ms_teams`.

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

## Message Formatting

### Markdown Support

Teams supports a subset of markdown:

| Format | Syntax |
|--------|--------|
| Bold | `**text**` |
| Italic | `_text_` |
| Link | `[text](url)` |
| Code | `` `code` `` |
| List | `- item` or `1. item` |

### Mentions

To mention users in Adaptive Cards:

```json
{
  "type": "TextBlock",
  "text": "Hey <at>Jane</at>, please review this."
}
```

With entities:

```json
{
  "msteams": {
    "entities": [
      {
        "type": "mention",
        "text": "<at>Jane</at>",
        "mentioned": {
          "id": "29:1abc...",
          "name": "Jane Doe"
        }
      }
    ]
  }
}
```

## Common Use Cases

### Incident Alert

```typescript
const incidentCard = {
  type: "AdaptiveCard",
  version: "1.4",
  body: [
    {
      type: "TextBlock",
      text: "🔴 P1 Incident: API Latency Spike",
      weight: "bolder",
      size: "large",
      color: "attention"
    },
    {
      type: "TextBlock",
      text: "High latency detected in api-gateway affecting customer-facing services.",
      wrap: true
    },
    {
      type: "FactSet",
      facts: [
        { title: "Started", value: "2 minutes ago" },
        { title: "Severity", value: "P1 - Critical" },
        { title: "On-call", value: "Jane Doe" }
      ]
    }
  ],
  actions: [
    {
      type: "Action.OpenUrl",
      title: "View Dashboard",
      url: "https://monitoring.acme.com/incidents/123"
    },
    {
      type: "Action.OpenUrl",
      title: "Runbook",
      url: "https://wiki.acme.com/runbooks/latency"
    }
  ]
};
```

### Approval Request

```typescript
const approvalCard = {
  type: "AdaptiveCard",
  version: "1.4",
  body: [
    {
      type: "TextBlock",
      text: "📋 Approval Required",
      weight: "bolder",
      size: "large"
    },
    {
      type: "TextBlock",
      text: "Bob Smith is requesting access to production database.",
      wrap: true
    },
    {
      type: "FactSet",
      facts: [
        { title: "Requester", value: "Bob Smith" },
        { title: "Resource", value: "prod-db-001" },
        { title: "Access Level", value: "Read-only" },
        { title: "Duration", value: "4 hours" },
        { title: "Reason", value: "Investigating customer issue #4567" }
      ]
    }
  ],
  actions: [
    {
      type: "Action.Submit",
      title: "Approve",
      style: "positive",
      data: { action: "approve", requestId: "req-123" }
    },
    {
      type: "Action.Submit",
      title: "Deny",
      style: "destructive", 
      data: { action: "deny", requestId: "req-123" }
    },
    {
      type: "Action.OpenUrl",
      title: "View Details",
      url: "https://acme.com/access-requests/123"
    }
  ]
};
```

## Handling Action.Submit Responses

When a user clicks an `Action.Submit` button in an Adaptive Card, Teams sends the data to your bot's messaging endpoint. This requires a Bot Framework registration.

### How It Works

1. User clicks "Approve" or "Deny" on an Adaptive Card
2. Teams sends a POST to your bot's messaging endpoint with `type: "invoke"` and `name: "adaptiveCard/action"`
3. Your bot processes the action and returns an updated card

### Receiving Submit Payloads

**TypeScript (Express with Bot Framework):**
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/api/messages", async (req, res) => {
  const activity = req.body;

  if (activity.type === "invoke" && activity.name === "adaptiveCard/action") {
    const actionData = activity.value.action.data;
    const userId = activity.from.id;

    let responseCard;

    switch (actionData.action) {
      case "approve":
        await processApproval(actionData.requestId, userId);
        responseCard = buildConfirmationCard(
          `Approved by ${activity.from.name}`,
          actionData.requestId
        );
        break;
      case "deny":
        await processDenial(actionData.requestId, userId);
        responseCard = buildConfirmationCard(
          `Denied by ${activity.from.name}`,
          actionData.requestId
        );
        break;
    }

    // Return updated card to replace the original
    res.json({
      statusCode: 200,
      type: "application/vnd.microsoft.card.adaptive",
      value: responseCard,
    });
    return;
  }

  res.status(200).send();
});

function buildConfirmationCard(status: string, requestId: string) {
  return {
    type: "AdaptiveCard",
    version: "1.4",
    body: [
      {
        type: "TextBlock",
        text: `✅ ${status}`,
        weight: "bolder",
        size: "large",
      },
      {
        type: "TextBlock",
        text: `Request ${requestId} has been processed.`,
        wrap: true,
      },
    ],
  };
}
```

**Python (Flask):**
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/messages", methods=["POST"])
def messages():
    activity = request.json

    if activity.get("type") == "invoke" and activity.get("name") == "adaptiveCard/action":
        action_data = activity["value"]["action"]["data"]
        user_name = activity["from"]["name"]

        if action_data["action"] == "approve":
            process_approval(action_data["requestId"], activity["from"]["id"])
            status = f"Approved by {user_name}"
        elif action_data["action"] == "deny":
            process_denial(action_data["requestId"], activity["from"]["id"])
            status = f"Denied by {user_name}"

        return jsonify({
            "statusCode": 200,
            "type": "application/vnd.microsoft.card.adaptive",
            "value": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": status, "weight": "bolder", "size": "large"},
                    {"type": "TextBlock", "text": f"Request {action_data['requestId']} processed.", "wrap": True},
                ],
            },
        })

    return "", 200
```

### Bot Registration for Action.Submit

`Action.Submit` posts the click to your bot's messaging endpoint, so your own bot service must handle it. Ensure:

1. Bot is registered in Azure Bot Service
2. Messaging endpoint is set to your server URL (e.g., `https://api.acme.com/api/messages`)
3. App ID and password are configured in your server
4. The bot is installed in the user's Teams client or the target team

---

## Proactive Messaging

### Send to New Users

To send proactive messages (not in response to user), you need the conversation reference:

```typescript
// Store when user installs app or messages bot
const conversationReference = {
  serviceUrl: "https://smba.trafficmanager.net/...",
  conversation: { id: "19:abc..." },
  user: { id: "29:xyz..." }
};

// Later, send proactively
await client.send.message({
  message: {
    to: {
      ms_teams: {
        tenant_id: process.env.AZURE_TENANT_ID,
        service_url: conversationReference.serviceUrl,
        conversation_id: conversationReference.conversation.id
      }
    },
    template: "nt_01kmrbtw1v4q8x2c6d9n5j7h"
  }
});
```

## Adaptive Card Designer

Use Microsoft's [Adaptive Card Designer](https://adaptivecards.io/designer/) to:
- Visually design cards
- Preview across platforms
- Export JSON
- Test interactions

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 400 from Teams | Invalid card JSON | Validate in Card Designer |
| 401 | App not installed in the team, wrong or expired bot credentials, a single-tenant app registration, or no `tenant_id` | Install the app in the team, check the App ID and App Password, use a multitenant registration, send `tenant_id` |
| `tenant_id is required when using 'email' or 'channel_name'` | No `tenant_id` | Send `tenant_id`, or put it in the `service_url` path |
| Card not rendering | Unsupported version | Use version 1.4 or lower |

## Teams in Journeys

Journey send nodes deliver to Teams via the node's `to.ms_teams` override — exactly one target: `channel_id`, `channel_name` with `team_id`, `user_id`, or `email`. Most targets also need `service_url` and/or `tenant_id` (the **Microsoft** tenant, not your Courier tenant), and `conversation_id`/`reply_to_activity_id` are not supported on journey nodes. Full node shape, rules, examples, and template channel values: [journeys.md](../guides/journeys.md#slack-and-teams-sends).

## Related

- [Journeys](../guides/journeys.md) - Teams send nodes in multi-step flows
- [Slack](./slack.md) - Alternative workplace chat channel
- [Multi-Channel](../guides/multi-channel.md) - Teams in routing strategies
- [Reliability](../guides/reliability.md) - Webhook error handling
- [Batching](../guides/batching.md) - Batch notifications to channels
- [Throttling](../guides/throttling.md) - Rate limit management
