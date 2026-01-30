# Order Notifications

## Quick Reference

### Rules
- Order confirmation: Send within 1 minute of order placement
- ALWAYS include order number prominently
- ALWAYS use idempotency keys: `order-confirmation-{orderId}`
- Shipping: Send as soon as tracking number available
- Multi-package: Send separate notification per package
- NO promotional content in order notifications

### Required Fields by Type
| Notification | Required Fields |
|--------------|-----------------|
| Order confirmation | Order #, items, total, address, delivery estimate |
| Shipping | Order #, tracking #, carrier, items, ETA |
| Out for delivery | Order #, delivery window |
| Delivered | Order #, timestamp, proof photo (if available) |
| Refund | Order #, amount, method, processing time |

### Channel Selection
| Stage | Channels |
|-------|----------|
| Order placed | Email |
| Shipped | Email + Push |
| Out for delivery | Push + SMS |
| Delivered | Email + Push |
| Delivery exception | Email + Push + SMS |

### Common Mistakes
- Delayed order confirmation (users expect immediate)
- Missing order number in subject line
- Not including tracking link
- Promotional content ("Use SAVE20 on next order!")
- No idempotency key (duplicate confirmations)
- Not handling multi-package orders separately
- Missing "delivery exception" notification

### Templates

**Order Confirmation:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_CONFIRMATION",
    data: {
      orderNumber: "12345",
      items: [{ name: "Widget", qty: 2, price: 29.99 }],
      total: 64.97,
      estimatedDelivery: "Jan 30-31"
    }
  }
}, {
  idempotencyKey: `order-confirmation-12345`
});
```

**Shipping Update:**
```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_SHIPPED",
    data: {
      orderNumber: "12345",
      trackingNumber: "1Z999AA10123456784",
      carrier: "UPS",
      trackingUrl: "https://acme.co/track/12345"
    },
    routing: { method: "all", channels: ["email", "push"] }
  }
}, {
  idempotencyKey: `shipping-12345-shipped`
});
```

---

Best practices for order confirmations, shipping updates, and delivery notifications.

## Order Lifecycle

| Stage | Notification | Channels |
|-------|--------------|----------|
| Order Placed | Order Confirmation | Email |
| Order Confirmed | Confirmation | Email |
| Shipped | Shipping Notification | Email + Push |
| Out for Delivery | Delivery Update | Push + SMS |
| Delivered | Delivery Confirmation | Email + Push |

## Order Confirmation

### Timing

Send **immediately** after order is placed (within 1 minute).

### Content Requirements

- Order number (prominent)
- Items ordered with quantities and prices
- Subtotal, tax, shipping, total
- Shipping address
- Estimated delivery date
- Payment method (last 4 digits)
- Order tracking link (if available)
- Support contact

### Email Structure

Subject: Order #12345 confirmed - Thanks for your order!

Include sections for:
- Logo and order number header
- Item list with images, quantities, and prices
- Order totals breakdown
- Shipping address
- Estimated delivery
- View Order button

Always use idempotency keys (e.g., `order-confirmation-{orderId}`) to prevent duplicate sends.

## Shipping Notifications

### When to Send

- When carrier provides tracking number
- Include tracking link immediately

### Multi-Package Orders

For orders with multiple packages, send a notification for each package with:
- Package number (e.g., "Package 1 of 3")
- Items in this package
- Tracking number for this package

### Email Content

Subject: Your order has shipped - Track your package

Include:
- Carrier name
- Tracking number
- Tracking link/button
- Estimated arrival date
- List of items in shipment

### Push Notification

Title: "Your order shipped!"
Body: "Order #12345 is on its way. Tap to track."
Include deep link to tracking page.

## Delivery Updates

### Out for Delivery

High urgency - use push/SMS for real-time awareness.

Push: "Your order is out for delivery! Arriving today between 2:00 PM - 6:00 PM"

SMS: "Acme: Your order #12345 is out for delivery. Arriving today 2-6 PM. Track: acme.co/t/12345"

### Delivered

Channels: Email + Push

Include:
- Delivery timestamp
- Proof of delivery photo (if available)
- "Rate your experience" option

### Delivery Exception

Handle issues proactively. Send to all channels: Email + Push + SMS.

Include:
- What happened
- Next attempt date
- Support link

## Returns & Refunds

### Return Initiated

Include:
- Return number
- Items being returned
- Return label download
- Drop-off locations

### Return Received

Include:
- Confirmation that return was received
- Refund amount
- Refund method
- Processing time (e.g., "3-5 business days")

### Refund Processed

Include:
- Refund amount
- Payment method refunded to
- Transaction ID

## Back in Stock

For items the user requested to be notified about.

Channels: Email + Push

Include:
- Product name and image
- Current price
- Direct link to purchase

**Note:** This is transactional (user requested it), not marketing.

## Channel Strategy

| Event | Email | Push | SMS | In-App |
|-------|-------|------|-----|--------|
| Order confirmed | Yes | - | - | Yes |
| Order shipped | Yes | Yes | - | Yes |
| Out for delivery | - | Yes | Yes | Yes |
| Delivered | Yes | Yes | - | Yes |
| Delivery exception | Yes | Yes | Yes | Yes |
| Return label | Yes | - | - | - |
| Refund processed | Yes | Yes | - | Yes |

## Best Practices

### Order Numbers

- Make them prominent
- Use consistent format (e.g., #12345)
- Include in subject lines
- Make searchable in email

### Images

- Include product images (helps recognition)
- Optimize for email (< 100KB each)
- Use alt text for accessibility

### Timing

- Confirmation: Immediate (< 1 minute)
- Shipping: As soon as tracking available
- Delivery updates: Real-time from carrier

### Idempotency

Always use idempotency keys to prevent duplicate sends:
- `order-confirmation-{orderId}`
- `shipment-{shipmentId}`
- `delivery-{orderId}-{deliveryId}`

## Related

- [Email](../channels/email.md) - Email design best practices
- [Push](../channels/push.md) - Push notification patterns
- [SMS](../channels/sms.md) - SMS for delivery alerts
- [Reliability](../guides/reliability.md) - Idempotency patterns
