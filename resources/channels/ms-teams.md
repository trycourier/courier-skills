# Microsoft Teams Channel

## Quick Reference

### Rules
- Incoming Webhook: simplest setup, channel-only, no interaction
- Bot Framework: required for DMs and interactive messages
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

**Via Webhook:**
```typescript
await courier.send({
  message: {
    to: {
      ms_teams: {
        webhook_url: "https://outlook.office.com/webhook/..."
      }
    },
    content: { title: "Build Complete", body: "Build #456 succeeded." }
  }
});
```

**Adaptive Card Override:**
```typescript
channels: {
  ms_teams: {
    override: {
      body: {
        type: "AdaptiveCard",
        version: "1.4",
        body: [
          { type: "TextBlock", text: "Title", weight: "bolder", size: "large" },
          { type: "FactSet", facts: [
            { title: "Status", value: "Complete" },
            { title: "Duration", value: "2m 34s" }
          ]}
        ],
        actions: [
          { type: "Action.OpenUrl", title: "View", url: "https://..." }
        ]
      }
    }
  }
}
```

**Via Bot (DM):**
```typescript
await courier.send({
  message: {
    to: {
      ms_teams: {
        tenant_id: process.env.AZURE_TENANT_ID,
        service_url: "https://smba.trafficmanager.net/...",
        user_id: "29:1abc..."
      }
    },
    template: "TASK_ASSIGNED"
  }
});
```

---

Best practices for sending Microsoft Teams notifications with Adaptive Cards.

## Integration Methods

### 1. Incoming Webhook (Simplest)

Best for: Channel notifications, alerts, no user interaction needed.

**Setup:**
1. In Teams, go to channel → Connectors → Incoming Webhook
2. Configure and copy webhook URL
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
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

await courier.send({
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
await courier.send({
  message: {
    to: {
      ms_teams: {
        webhook_url: process.env.TEAMS_WEBHOOK_URL
      }
    },
    template: "DEPLOY_NOTIFICATION",
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
await courier.send({
  message: {
    to: {
      ms_teams: {
        tenant_id: process.env.AZURE_TENANT_ID,
        service_url: "https://smba.trafficmanager.net/...",
        user_id: "29:1abc..." // Teams user ID
      }
    },
    template: "TASK_ASSIGNED",
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

### Deployment Notification

```typescript
const deployCard = {
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
        { title: "Service", value: "api-gateway" },
        { title: "Environment", value: "Production" },
        { title: "Version", value: "v2.3.1" },
        { title: "Deployed by", value: "Jane Doe" },
        { title: "Duration", value: "2m 34s" }
      ]
    }
  ],
  actions: [
    {
      type: "Action.OpenUrl",
      title: "View Logs",
      url: "https://logs.acme.com/deploy/123"
    },
    {
      type: "Action.OpenUrl",
      title: "Release Notes",
      url: "https://acme.com/releases/v2.3.1"
    }
  ]
};
```

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
await courier.send({
  message: {
    to: {
      ms_teams: {
        tenant_id: process.env.AZURE_TENANT_ID,
        service_url: conversationReference.serviceUrl,
        conversation_id: conversationReference.conversation.id
      }
    },
    template: "WEEKLY_SUMMARY"
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
