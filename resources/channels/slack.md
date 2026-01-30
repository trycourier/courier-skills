# Slack Channel

## Quick Reference

### Rules
- Bot token starts with `xoxb-` (not user token `xoxp-`)
- Required scopes: `chat:write`, `chat:write.public`, `users:read.email`
- Use Channel ID (starts with `C`), not channel name
- Rate limit: 1 message per second per channel
- Burst limit: 30-50 messages
- Use Block Kit for rich formatting (not attachments)
- Text formatting: `*bold*`, `_italic_`, `~strike~`, `` `code` ``
- User mention: `<@U0123ABC>`
- Channel mention: `<#C0123ABC>`

### Common Mistakes
- Using channel name instead of channel ID
- Using user token instead of bot token
- Missing `chat:write.public` scope (can't post to channels bot isn't in)
- Exceeding rate limits without queuing
- Using deprecated attachments instead of Block Kit
- Not handling "channel_not_found" or "not_in_channel" errors
- Sending walls of text instead of scannable Block Kit layouts

### Templates

**Send DM by Email:**
```typescript
await courier.send({
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

**Send to Channel:**
```typescript
await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: "C0123ABCDEF"
      }
    },
    template: "DEPLOY_NOTIFICATION"
  }
});
```

**Block Kit Override:**
```typescript
channels: {
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

Best practices for sending Slack notifications with Block Kit formatting.

## Slack App Setup

### Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app and select workspace
4. Navigate to "OAuth & Permissions"

### Required Scopes

**Bot Token Scopes** (recommended):

| Scope | Purpose |
|-------|---------|
| `chat:write` | Send messages |
| `chat:write.public` | Send to channels without joining |
| `users:read` | Look up users |
| `users:read.email` | Look up users by email |

### Install to Workspace

1. Go to "Install App" in your Slack app settings
2. Click "Install to Workspace"
3. Copy the "Bot User OAuth Token" (`xoxb-...`)
4. Add to Courier as a Slack integration

## Message Types

### Direct Messages (DMs)

Send to individual users:

```typescript
await courier.send({
  message: {
    to: {
      slack: {
        access_token: "xoxb-...",
        email: "jane@acme.com" // or user_id
      }
    },
    template: "DEPLOYMENT_COMPLETE"
  }
});
```

### Channel Messages

Send to a channel:

```typescript
await courier.send({
  message: {
    to: {
      slack: {
        access_token: "xoxb-...",
        channel: "C0123ABCDEF" // Channel ID
      }
    },
    template: "SYSTEM_ALERT"
  }
});
```

## Block Kit Formatting

Block Kit is Slack's UI framework for rich messages.

### Basic Structure

```json
{
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Title*\nDescription text"
      }
    }
  ]
}
```

### Common Block Types

**Section Block** - Text with optional accessory

```json
{
  "type": "section",
  "text": {
    "type": "mrkdwn",
    "text": "Your deployment to *production* completed successfully."
  },
  "accessory": {
    "type": "button",
    "text": { "type": "plain_text", "text": "View Logs" },
    "url": "https://acme.com/logs/123"
  }
}
```

**Header Block** - Large text header

```json
{
  "type": "header",
  "text": {
    "type": "plain_text",
    "text": "🚀 Deployment Complete"
  }
}
```

**Context Block** - Secondary information

```json
{
  "type": "context",
  "elements": [
    {
      "type": "mrkdwn",
      "text": "Deployed by <@U0123ABC> • 2 minutes ago"
    }
  ]
}
```

**Actions Block** - Interactive buttons

```json
{
  "type": "actions",
  "elements": [
    {
      "type": "button",
      "text": { "type": "plain_text", "text": "Approve" },
      "style": "primary",
      "action_id": "approve_request"
    },
    {
      "type": "button",
      "text": { "type": "plain_text", "text": "Deny" },
      "style": "danger",
      "action_id": "deny_request"
    }
  ]
}
```

## Courier Integration

### Basic Slack Message

```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        email: "jane@acme.com"
      }
    },
    content: {
      title: "Build Complete",
      body: "Your build #456 completed successfully."
    }
  }
});
```

### With Block Kit Override

```typescript
await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: "C0123ABCDEF"
      }
    },
    template: "DEPLOY_NOTIFICATION",
    data: {
      environment: "production",
      version: "v2.3.1",
      deployedBy: "jane"
    },
    channels: {
      slack: {
        override: {
          body: {
            blocks: [
              {
                type: "header",
                text: {
                  type: "plain_text",
                  text: "🚀 Deployment Complete"
                }
              },
              {
                type: "section",
                fields: [
                  {
                    type: "mrkdwn",
                    text: "*Environment:*\nproduction"
                  },
                  {
                    type: "mrkdwn",
                    text: "*Version:*\nv2.3.1"
                  }
                ]
              }
            ]
          }
        }
      }
    }
  }
});
```

### Using User Profile Slack Token

```typescript
// If user has connected Slack via OAuth
await courier.send({
  message: {
    to: { 
      user_id: "user-123" // Must have slack token in profile
    },
    template: "TASK_ASSIGNED",
    routing: {
      method: "single",
      channels: ["slack"]
    }
  }
});
```

## Formatting Reference

| Format | Syntax | Result |
|--------|--------|--------|
| Bold | `*text*` | **bold** |
| Italic | `_text_` | *italic* |
| Strike | `~text~` | ~~strikethrough~~ |
| Code | `` `code` `` | inline code |
| Link | `<url\|text>` | clickable link |
| User mention | `<@U0123ABC>` | @username |
| Channel | `<#C0123ABC>` | #channel |

### Emoji

Use standard emoji codes: `:rocket:`, `:white_check_mark:`, `:warning:`

## Threading

### Reply to Thread

Keep conversations organized by replying in threads:

```typescript
await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: "C0123ABCDEF"
      }
    },
    content: {
      body: "Build failed. See details above."
    },
    channels: {
      slack: {
        override: {
          body: {
            thread_ts: "1234567890.123456" // Parent message timestamp
          }
        }
      }
    }
  }
});
```

### Update Existing Message

```typescript
// Update a previously sent message
await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: "C0123ABCDEF"
      }
    },
    channels: {
      slack: {
        override: {
          body: {
            ts: "1234567890.123456", // Message to update
            blocks: [
              {
                type: "section",
                text: {
                  type: "mrkdwn",
                  text: "✅ Deployment *complete* to production"
                }
              }
            ]
          }
        }
      }
    }
  }
});
```

## Scheduled Messages

```typescript
// Schedule a message for later
const sendAt = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now

await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: "C0123ABCDEF"
      }
    },
    content: {
      body: "Daily standup reminder!"
    },
    channels: {
      slack: {
        override: {
          body: {
            post_at: sendAt
          }
        }
      }
    }
  }
});
```

## Common Use Cases

### CI/CD Notifications

```typescript
// Build status notification
await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: process.env.SLACK_DEPLOYS_CHANNEL
      }
    },
    channels: {
      slack: {
        override: {
          body: {
            blocks: [
              {
                type: "header",
                text: { type: "plain_text", text: "🚀 Deployment Complete" }
              },
              {
                type: "section",
                fields: [
                  { type: "mrkdwn", text: "*Service:*\napi-gateway" },
                  { type: "mrkdwn", text: "*Environment:*\nproduction" },
                  { type: "mrkdwn", text: "*Version:*\nv2.3.1" },
                  { type: "mrkdwn", text: "*Deployed by:*\n<@U0123ABC>" }
                ]
              },
              {
                type: "actions",
                elements: [
                  {
                    type: "button",
                    text: { type: "plain_text", text: "View Logs" },
                    url: "https://logs.acme.com/deploy/123"
                  },
                  {
                    type: "button",
                    text: { type: "plain_text", text: "Rollback" },
                    style: "danger",
                    action_id: "rollback_deploy"
                  }
                ]
              }
            ]
          }
        }
      }
    }
  }
});
```

### Incident Alert

```typescript
await courier.send({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: process.env.SLACK_INCIDENTS_CHANNEL
      }
    },
    channels: {
      slack: {
        override: {
          body: {
            blocks: [
              {
                type: "header",
                text: { type: "plain_text", text: "🔴 Incident: API Latency Spike" }
              },
              {
                type: "section",
                text: {
                  type: "mrkdwn",
                  text: "*Severity:* P1\n*Started:* 2 minutes ago\n*Affected:* api-gateway, payments-service"
                }
              },
              {
                type: "context",
                elements: [
                  { type: "mrkdwn", text: "On-call: <@U0123ABC> | <https://status.acme.com|Status Page>" }
                ]
              }
            ]
          }
        }
      }
    }
  }
});
```

## Best Practices

### Message Design

- **Keep it scannable** - Use headers, bullet points
- **Be actionable** - Include clear next steps or buttons
- **Add context** - Who, what, when, where
- **Use FactSets** - For structured data (key-value pairs)
- **Use attachments sparingly** - Prefer Block Kit

### Channel vs DM

| Use DM for | Use Channel for |
|------------|-----------------|
| Personal notifications | Team-wide alerts |
| Task assignments | System status updates |
| Approval requests | Deployment notifications |
| Direct mentions | Incident alerts |
| Performance reviews | Standup reminders |

### Rate Limits

| Limit Type | Value |
|------------|-------|
| Messages per second per channel | 1 |
| Burst limit | 30-50 messages |
| Web API rate limits | Tier-based (check Slack docs) |

For high volume, use Courier's built-in queuing and batching.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "channel_not_found" | Invalid channel ID | Use channel ID (C...), not name |
| "not_in_channel" | Bot not in channel | Add `chat:write.public` scope or invite bot |
| "user_not_found" | Invalid email | Verify email matches Slack account |
| "invalid_auth" | Bad token | Regenerate bot token |

## Related

- [MS Teams](./ms-teams.md) - Alternative workplace chat channel
- [Multi-Channel](../guides/multi-channel.md) - Slack in routing strategies
- [Batching](../guides/batching.md) - Batch notifications to channels
- [Throttling](../guides/throttling.md) - Respect Slack rate limits
- [Engagement](../growth/engagement.md) - Alert notification patterns
