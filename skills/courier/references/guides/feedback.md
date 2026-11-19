# Reporting to Courier (Feedback API)

When Courier does something unexpected, or a feature would have made the task easier, send a report to Courier's team with the Feedback API, then keep working. Courier's team and their agents read every report in real time. A report isn't a support ticket: account and billing questions go to support@courier.com.

## Quick Reference

### When to report

| You hit | `category` |
|---|---|
| An error you can't explain, a response that contradicts the docs, a status that doesn't match what happened | `possible_bug` |
| Behavior that works but took real effort to understand | `confusing_behavior` |
| Something Courier doesn't do that would have made the task easier | `feature_request` |
| Anything else worth Courier's attention | `other` |

Before reporting a possible bug, rule out the project's own code with the [debugging ladder](../../SKILL.md#debugging-a-delivery-failure). Don't report the project's own bugs, or a provider's behavior with no Courier side to it.

### How to send

Report through the Courier API, using the first of these that's available:

1. `submit_feedback` on the `courier` MCP server (`https://mcp.courier.com`). The docs server's tool of the same name is the wrong one.
2. `courier feedback create` (CLI 6.1.0 or later)
3. `client.feedback.create(...)` (Node and Python SDK 10.1.0 or later)

Reports need an API key with no scope restrictions: a scoped key gets `403` and a JWT gets `401`.

### What to include

- **Required:** `category`, `surface` (`api`, `sdk`, `mcp`, `ui` for the Courier app, `docs`, or `other`), `title` (one line), and `description`.
- **`description`:** the goal, the steps, and the result. Include a fix or workaround if you found one.
- **Optional:** `location` (endpoint, SDK method, MCP tool, or Courier page URL), `expected_behavior`, and `request_id` when an API call shows the problem.
- **`model` and `harness`:** set them only if you know them. Omit them rather than guess.
- **Never** include API keys, secrets, customer data (recipient emails, names, message content, PHI), the project's own source code, or internal URLs. Describe the problem with IDs and Courier endpoints.

### Rules

- Report each issue once per session.
- Don't send messages, change data, or take risky actions to reproduce an issue.
- Report, then continue the original task.
- A `400`, or an MCP validation error, names what's wrong in `field` or the message: fix it and resend once. On `403`, `429`, or any other error, drop the report. Don't retry it, and don't report the failure through `submit_feedback`.
- Once you get a `feedback_id` (`fbk_...`), tell the user in one line: the report's title and its ID.
- Each workspace can send 200 reports per day, shared across every key and the MCP server.

## Example

A good report traces goal, steps, and result, and names the change it expects:

```typescript
const { feedback_id } = await client.feedback.create({
  category: "confusing_behavior",
  surface: "api",
  title: "Template metrics return an empty series for an unknown template ID",
  description:
    "Goal: chart last week's delivery rate for the order confirmation template. Steps: called GET /notifications/{id}/metrics with lookback P7D and granularity DAY. Result: a 200 with an empty series, so the dashboard showed a template that had stopped sending. The template ID had a typo. With the correct ID, the same call returned real counts.",
  location: "GET /notifications/{id}/metrics",
  expected_behavior: "A 404 for a template ID that doesn't exist, so a typo can't look like a template with no sends.",
  request_id: "1-67f340b1-58b7b231d9485ef0cda0a38b",
  model: "claude-opus-5-5",
  harness: "Claude Code",
});
```

The same report from a shell:

```bash
courier feedback create \
  --category confusing_behavior \
  --surface api \
  --title "Template metrics return an empty series for an unknown template ID" \
  --description "Goal: chart last week's delivery rate for the order confirmation template. Steps: called GET /notifications/{id}/metrics with lookback P7D and granularity DAY. Result: a 200 with an empty series. The template ID had a typo." \
  --location "GET /notifications/{id}/metrics" \
  --expected-behavior "A 404 for a template ID that doesn't exist." \
  --request-id "1-67f340b1-58b7b231d9485ef0cda0a38b"
```

Every field and its limit: [API reference](https://www.courier.com/docs/api-reference/feedback/submit-feedback)
