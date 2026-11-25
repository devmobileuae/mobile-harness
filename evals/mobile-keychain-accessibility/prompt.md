---
name: mobile-keychain-accessibility
tags: [mobile-feature-delivery]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our subscription app (iOS, shipped, about 20k active users) keeps the auth token in the Keychain with this helper. The background refresh fails while the phone is locked, so the token should be accessible after first unlock. Change the helper.

```swift
import Foundation
import Security

enum TokenStore {
    private static let service = "app.example.auth"

    private static func baseQuery(_ key: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: service,
         kSecAttrAccount as String: key]
    }

    static func save(_ value: String, key: String) {
        var q = baseQuery(key)
        SecItemDelete(q as CFDictionary)
        q[kSecValueData as String] = Data(value.utf8)
        SecItemAdd(q as CFDictionary, nil)
    }

    static func read(_ key: String) -> String? {
        var q = baseQuery(key)
        q[kSecReturnData as String] = true
        q[kSecMatchLimit as String] = kSecMatchLimitOne
        var out: AnyObject?
        guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess,
              let data = out as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
}
```

Show me the new code.
