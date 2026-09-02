# Courier Inbox for React Native

## Common Mistakes

- Passing the JWT as `jwt`. The React Native `signIn` parameter is **`accessToken`**, the same token under a different name.
- Signing in before the token resolves. Gate on having it.
- Forgetting `listenForUpdates()`, so the feed only refreshes on remount.
- Expecting web CSP guidance to apply. It doesn't, native has no CSP, but push setup does apply, see [push.md](../channels/push.md).

### Installation

```bash
npm install @trycourier/courier-react-native
```

### Setup

```tsx
import { useEffect, useState } from "react";
import { useNavigation } from "@react-navigation/native";
import { Courier, CourierInboxView } from "@trycourier/courier-react-native";

// Fetches a short-lived Courier JWT from your backend. The React Native
// signIn API uses the parameter name `accessToken` (it's the same JWT as
// the web `jwt` field — just named differently in the RN SDK).
function useCourierToken(userId: string): string | null {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    fetch("https://api.example.com/courier-token")
      .then((r) => r.json())
      .then((d) => setToken(d.token));
  }, [userId]);

  return token;
}

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
      onClickMessageAtIndex={(message, _index) => {
        if (message.data?.screen) navigation.navigate(message.data.screen);
      }}
    />
  );
}
```

---
