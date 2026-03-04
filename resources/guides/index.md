# Cross-Cutting Guides

## Quick Reference

### Rules
- These guides apply across all channels and notification types
- Start with [Quickstart](./quickstart.md) if you're new to Courier
- Use the routing table below to find the right guide for your task
- Most tasks need only 1-2 guides; don't read all of them

### Guide Routing

| Need to... | See |
|------------|-----|
| Send your first notification | [Quickstart](./quickstart.md) |
| Route across multiple channels, set up fallbacks | [Multi-Channel](./multi-channel.md) |
| Manage user notification preferences | [Preferences](./preferences.md) |
| Ensure GDPR, TCPA, CAN-SPAM compliance | [Compliance](./compliance.md) |
| Handle retries, idempotency, error recovery | [Reliability](./reliability.md) |
| Combine notifications into digests | [Batching](./batching.md) |
| Control frequency, prevent fatigue | [Throttling](./throttling.md) |
| Plan notifications for your app type | [Catalog](./catalog.md) |
| Use the CLI for debugging and agent workflows | [CLI](./cli.md) |
| Find reusable code patterns | [Patterns](./patterns.md) |

---

## Overview

Cross-cutting guides cover concerns that span multiple channels and notification types. They complement the channel-specific guides (`channels/`) and notification-type guides (`transactional/`, `growth/`).

## Categories

| Guide | What It Covers |
|-------|---------------|
| [Quickstart](./quickstart.md) | Send your first notification with SDK, CLI, or curl |
| [Multi-Channel](./multi-channel.md) | Routing methods (`single` vs `all`), channel priority, escalation patterns, provider failover |
| [Preferences](./preferences.md) | Preference topics, channel opt-outs, frequency controls, preference center UI |
| [Compliance](./compliance.md) | GDPR, TCPA, CAN-SPAM, CCPA, CASL; consent records, data retention, right to erasure |
| [Reliability](./reliability.md) | Idempotency keys, retry with backoff, webhook handling, circuit breakers, dead letter queues |
| [Batching](./batching.md) | Digest strategies, batch windows, aggregation rules |
| [Throttling](./throttling.md) | Per-user rate limits, channel-specific frequency caps, priority-based throttling |
| [Catalog](./catalog.md) | Notification planning by app type (SaaS, e-commerce, marketplace, mobile) |
| [CLI](./cli.md) | Courier CLI for ad-hoc operations, debugging, CI/CD, and AI agent workflows |
| [Patterns](./patterns.md) | Copy-paste implementations: idempotency, consent check, quiet hours, retry, webhooks, data masking |

## Common Combinations

| Task | Guides to Read |
|------|---------------|
| New to Courier | [Quickstart](./quickstart.md) |
| Building multi-channel notifications | [Multi-Channel](./multi-channel.md), [Preferences](./preferences.md) |
| Making sends reliable | [Reliability](./reliability.md), [Patterns](./patterns.md) |
| Compliance audit | [Compliance](./compliance.md), [Preferences](./preferences.md) |
| Reducing notification fatigue | [Throttling](./throttling.md), [Batching](./batching.md), [Preferences](./preferences.md) |
| Debugging delivery issues | [CLI](./cli.md), [Reliability](./reliability.md) |
| Planning notification system | [Catalog](./catalog.md), [Multi-Channel](./multi-channel.md) |

## Related

- [Channels](../channels/email.md) - Channel-specific best practices
- [Transactional](../transactional/index.md) - Transactional notification types
- [Growth](../growth/index.md) - Growth and lifecycle notifications
