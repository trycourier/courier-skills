# Microsoft Teams Channel

## Quick Reference

### Rules
- Incoming Webhook (via Workflows): simplest setup, channel-only, no interaction
- Bot Framework: required for DMs and interactive messages
- Office 365 Connector webhooks are deprecated — use Workflows webhooks instead
- Adaptive Card version: use 1.4 or lower for compatibility
- Card JSON must be valid - test in Adaptive Card Designer first
- Required Azure AD permissions: `User.Read.All`, `Chat.Create`, `ChatMessage.Send`
- Webhook URLs expire - must be regenerated periodically
- Use FactSet for key-value data display
- Limit to 2-3 action buttons maximum

### Common Mistakes
- Using Adaptive Card version > 1.4 (won't render)
- Invalid card JSON (returns 400 error)
- Webhook URL expired (message not delivered)
- Missing Azure AD permissions for bot DMs
- Not testing cards in Adaptive Card Designer first
- Too many buttons (cluttered, confusing)
- Not handling webhook expiration

### Templates

**Send via Webhook (TypeScript):**
```typescript
await client.send.message({
  message: {
    to: { ms_teams: { webhook_url: process.env.TEAMS_WEBHOOK_URL } },
    content: { title: "Build Complete", body: "Build #456 succeeded." }
  }
});
```

**Send via Webhook (Python):**
```python
import os

client.send.message(
    message={
        "to": {"ms_teams": {"webhook_url": os.environ["TEAMS_WEBHOOK_URL"]}},
        "content": {"title": "Build Complete", "body": "Build #456 succeeded."},
    }
)
```

**With Adaptive Card** (fragment — pass as `message.channels` on `client.send.message`):
```jsonc
{
  "ms_teams": {
    "override": {
      "body": {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          { "type": "TextBlock", "text": "Deploy Complete", "weight": "bolder", "size": "large" },
          {
            "type": "FactSet",
            "facts": [
              { "title": "Env", "value": "production" },
              { "title": "Version", "value": "v2.3.1" }
            ]
          }
        ]
      }
    }
  }
}
```

---

Best practices for sending Microsoft Teams notifications with Adaptive Cards.

## Integration Methods

### 1. Incoming Webhook (Simplest)

Best for: Channel notifications, alerts, no user interaction needed.

> **Note:** Microsoft has retired Office 365 connectors (the old "Incoming Webhook" integration inside a Teams channel). Creation of new connectors has been disabled since early 2025, and Microsoft has been pushing a final cutoff for existing connector URLs through multiple extensions in 2025–2026 — treat any existing connector URL as **unreliable** and migrate now. The supported replacement is the **Workflows** app in Teams (Power Automate) with the "Post to a channel when a webhook request is received" template, which produces a new webhook URL. For net-new integrations, use Workflows webhooks or the Bot Framework; do not create new connectors. Check Microsoft's current Teams connectors retirement doc for the latest exact dates before architecting anything long-lived.

**Setup:**
1. In Teams, go to channel → Manage channel → Workflows → "Post to a channel when a webhook request is received"
2. Configure and copy the workflow webhook URL
3. POST messages to webhook URL

### 2. Bot Framework (Full Featured)

Best for: DMs, interactive messages, user-specific notifications.

**Setup:**
1. Register app in Azure AD
2. Create Bot Channel Registration
3. Configure in Courier

### 3. Courier Integration

Courier supports both methods through configuration.

## Azure AD App Registration

### Create App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. App registrations → New registration
3. Name: "Acme Notifications"
4. Supported account types: "Accounts in any organizational directory"
5. Redirect URI: Leave blank for now

### Add API Permissions

Required permissions:
- `User.Read.All` (Application)
- `TeamsAppInstallation.ReadWriteForUser.All` (Application)
- `Chat.Create` (Application)
- `ChatMessage.Send` (Application)

Grant admin consent for your organization.

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

### Via Incoming Webhook

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

await client.send.message({
  message: {
    to: {
      ms_teams: {
        webhook_url: "https://outlook.office.com/webhook/..."
      }
    },
    content: {
      title: "Build Complete",
      body: "Build #456 completed successfully."
    }
  }
});
```

### With Adaptive Card Override

```typescript
await client.send.message({
  message: {
    to: {
      ms_teams: {
        webhook_url: process.env.TEAMS_WEBHOOK_URL
      }
    },
    template: "nt_01kmrby3q6x9v2d5c8n1w4ht",
    channels: {
      ms_teams: {
        override: {
          body: {
            type: "AdaptiveCard",
            version: "1.4",
            body: [
              {
                type: "TextBlock",
                text: "🚀 Deployment Complete",
                weight: "bolder",
                size: "large"
              },
              {
                type: "FactSet",
                facts: [
                  { title: "Environment", value: "Production" },
                  { title: "Version", value: "v2.3.1" },
                  { title: "Deployed by", value: "Jane Doe" }
                ]
              }
            ],
            actions: [
              {
                type: "Action.OpenUrl",
                title: "View Deployment",
                url: "https://acme.com/deploys/123"
              }
            ]
          }
        }
      }
    }
  }
});
```

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

`Action.Submit` requires a Bot Framework bot — webhooks cannot receive interactive responses. Ensure:

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

## Best Practices

### Card Design

- **Keep it scannable** - Use FactSets for key data
- **Limit actions** - 2-3 buttons maximum
- **Use color sparingly** - Rely on Teams theme
- **Test on mobile** - Cards render differently
- **Use icons/emoji** - Help visual scanning

### Content Guidelines

- **Be concise** - Teams is fast-paced
- **Include context** - Who, what, when
- **Make actionable** - Clear next steps
- **Respect focus time** - Don't over-notify
- **Consider Do Not Disturb** - Teams honors user status

### Channel vs Chat

| Use Channel for | Use Chat (DM) for |
|-----------------|-------------------|
| Team announcements | Personal notifications |
| System alerts | Task assignments |
| Deployment updates | Approval requests |
| Incident notifications | Direct mentions |
| Standup reminders | Performance feedback |

## Adaptive Card Designer

Use Microsoft's [Adaptive Card Designer](https://adaptivecards.io/designer/) to:
- Visually design cards
- Preview across platforms
- Export JSON
- Test interactions

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook returns 400 | Invalid card JSON | Validate in Card Designer |
| Message not delivered | Webhook expired | Regenerate webhook |
| Bot can't send DM | Missing permissions | Check Azure AD permissions |
| Card not rendering | Unsupported version | Use version 1.4 or lower |

## Related

- [Slack](./slack.md) - Alternative workplace chat channel
- [Multi-Channel](../guides/multi-channel.md) - Teams in routing strategies
- [Reliability](../guides/reliability.md) - Webhook error handling
- [Batching](../guides/batching.md) - Batch notifications to channels
- [Throttling](../guides/throttling.md) - Rate limit management
