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

**Send DM by Email (Python):**
```python
import os

client.send.message(
    message={
        "to": {
            "slack": {
                "access_token": os.environ["SLACK_BOT_TOKEN"],
                "email": "jane@acme.com",
            }
        },
        "content": {"title": "Build Complete", "body": "Your build finished."},
    }
)
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
await client.send.message({
  message: {
    to: {
      slack: {
        access_token: "xoxb-...",
        email: "jane@acme.com" // or user_id
      }
    },
    template: "nt_01kmrbyb7x1q5v8d2c6n4w9hj"
  }
});
```

### Channel Messages

Send to a channel:

```typescript
await client.send.message({
  message: {
    to: {
      slack: {
        access_token: "xoxb-...",
        channel: "C0123ABCDEF" // Channel ID
      }
    },
    template: "nt_01kmrbyk2q5x9v1d4c7n8w6hj"
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

## Handling Interactive Actions

When you include `action_id` buttons in Block Kit, Slack sends a POST to your app when users click them. This requires setting up an Interactivity URL.

### Setup

1. In your Slack app settings, go to **Interactivity & Shortcuts**
2. Toggle **Interactivity** on
3. Set **Request URL** to your endpoint (e.g., `https://api.acme.com/slack/actions`)

### Receiving Action Payloads

Slack sends a JSON payload with `type: "block_actions"` when a user clicks a button. The payload includes which action was clicked and who clicked it.

**TypeScript (Express):**
```typescript
import express from "express";

const app = express();
app.use(
  "/slack/actions",
  express.urlencoded({
    extended: true,
    verify: (req, _res, buf) => {
      // Slack signature verification requires the exact raw body bytes.
      (req as { rawBody?: string }).rawBody = buf.toString("utf8");
    },
  })
);

app.post("/slack/actions", async (req, res) => {
  if (!verifySlackRequest(req as { headers: Record<string, string | string[] | undefined>; rawBody?: string })) {
    return res.status(401).send("Invalid Slack signature");
  }

  // Respond within 3 seconds to avoid timeout
  res.status(200).send();

  const payload = JSON.parse(req.body.payload);

  if (payload.type !== "block_actions") return;

  for (const action of payload.actions) {
    const userId = payload.user.id;
    const actionId = action.action_id;
    const responseUrl = payload.response_url;

    switch (actionId) {
      case "approve_request":
        await handleApproval(action.value, userId, responseUrl);
        break;
      case "deny_request":
        await handleDenial(action.value, userId, responseUrl);
        break;
      case "rollback_deploy":
        await handleRollback(action.value, userId, responseUrl);
        break;
    }
  }
});
```

**Python (Flask):**
```python
import json
import hmac
import time
import hashlib
import os
from flask import Flask, request

app = Flask(__name__)

def verify_slack_request() -> bool:
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    raw_body = request.get_data(as_text=True)

    if not timestamp or not signature or not raw_body:
        return False

    # Reject replayed requests older than 5 minutes.
    try:
        request_ts = int(timestamp)
    except ValueError:
        return False

    if abs(time.time() - request_ts) > 300:
        return False

    sig_base = f"v0:{timestamp}:{raw_body}"
    secret = os.environ["SLACK_SIGNING_SECRET"].encode("utf-8")
    computed = "v0=" + hmac.new(
        secret,
        sig_base.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, signature)

@app.route("/slack/actions", methods=["POST"])
def slack_actions():
    if not verify_slack_request():
        return "Invalid Slack signature", 401

    payload = json.loads(request.form["payload"])

    if payload["type"] != "block_actions":
        return "", 200

    for action in payload["actions"]:
        user_id = payload["user"]["id"]
        action_id = action["action_id"]

        if action_id == "approve_request":
            handle_approval(action.get("value"), user_id)
        elif action_id == "deny_request":
            handle_denial(action.get("value"), user_id)

    return "", 200
```

### Updating the Message After Action

After processing an action, update the original message to reflect the new state:

```typescript
import { WebClient } from "@slack/web-api";

const slack = new WebClient(process.env.SLACK_BOT_TOKEN);

async function handleApproval(
  requestId: string,
  approverSlackId: string,
  responseUrl: string
) {
  await processApproval(requestId);

  // Update the original message via response_url from the payload
  await fetch(responseUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      replace_original: true,
      blocks: [
        {
          type: "section",
          text: {
            type: "mrkdwn",
            text: `✅ Approved by <@${approverSlackId}>`,
          },
        },
      ],
    }),
  });
}
```

### Verifying Slack Requests

Validate that requests actually come from Slack using the signing secret:

```typescript
import crypto from "crypto";

function verifySlackRequest(req: {
  headers: Record<string, string | string[] | undefined>;
  rawBody?: string;
}): boolean {
  const tsHeader = req.headers["x-slack-request-timestamp"];
  const sigHeader = req.headers["x-slack-signature"];
  const timestamp = Array.isArray(tsHeader) ? tsHeader[0] : tsHeader;
  const signature = Array.isArray(sigHeader) ? sigHeader[0] : sigHeader;
  const rawBody = req.rawBody ?? "";

  if (!timestamp || !signature || !rawBody) return false;

  // Reject requests older than 5 minutes
  if (Math.abs(Date.now() / 1000 - Number(timestamp)) > 300) return false;

  const sigBaseString = `v0:${timestamp}:${rawBody}`;
  const hmac = crypto
    .createHmac("sha256", process.env.SLACK_SIGNING_SECRET!)
    .update(sigBaseString)
    .digest("hex");

  const expectedSignature = `v0=${hmac}`;
  if (expectedSignature.length !== signature.length) return false;

  return crypto.timingSafeEqual(Buffer.from(expectedSignature), Buffer.from(signature));
}
```

---

## Courier Integration

### Basic Slack Message

```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

await client.send.message({
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
await client.send.message({
  message: {
    to: {
      slack: {
        access_token: process.env.SLACK_BOT_TOKEN,
        channel: "C0123ABCDEF"
      }
    },
    template: "nt_01kmrby3q6x9v2d5c8n1w4ht",
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
await client.send.message({
  message: {
    to: { 
      user_id: "user-123" // Must have slack token in profile
    },
    template: "nt_01kmrbyt6x9q3v7d1c5n8w2hj",
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
await client.send.message({
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
await client.send.message({
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

await client.send.message({
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
await client.send.message({
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
await client.send.message({
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
- **Use Section fields** - For structured key-value data
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
