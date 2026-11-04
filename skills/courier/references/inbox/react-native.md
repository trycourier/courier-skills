# Courier Inbox for React Native

## Quick Reference

### Rules
- `signIn` takes **`accessToken`**, not `jwt`. It's the same JWT the web SDKs call `jwt`, under a different name.
- Gate `signIn` on having the token.
- There is no `listenForUpdates()`; that's the web API. `CourierInboxView` keeps itself updated. For a custom UI or your own unread badge use `addInboxListener({ onMessagesChanged, onUnreadCountChanged, onMessageEvent })`, which resolves to a `CourierInboxListener`, and remove it with `removeInboxListener({ listenerId })`.
- Web CSP guidance doesn't apply (native has no CSP), but push setup does, see [push.md](../channels/push.md).

### Installation

```bash
npm install @trycourier/courier-react-native
```

### Setup

```tsx
import { useEffect } from "react";
import { useNavigation } from "@react-navigation/native";
import Courier, { CourierInboxView } from "@trycourier/courier-react-native";

// useCourierToken: fetches a short-lived JWT from your backend and refreshes it,
// see auth.md, "JWT Refresh Strategy".

function App() {
  const navigation = useNavigation();
  const courierToken = useCourierToken("user-123");

  useEffect(() => {
    if (!courierToken) return;
    Courier.shared.signIn({
      accessToken: courierToken,
      userId: "user-123",
    });
  }, [courierToken]);

  return (
    <CourierInboxView
      onClickInboxMessageAtIndex={(message, _index) => {
        if (message.data?.screen) navigation.navigate(message.data.screen);
      }}
    />
  );
}
```

---
