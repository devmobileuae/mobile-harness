---
arm: both
type: llm
focus: final
weight: 2
---

The trap: the app is shipped, so every existing user already has a token item stored WITHOUT an explicit accessibility (default `kSecAttrAccessibleWhenUnlocked`). If `kSecAttrAccessible` is added to the shared `baseQuery`, then `read` (SecItemCopyMatching) no longer matches those items (errSecItemNotFound, -25300) and `save`'s SecItemDelete no longer deletes them, so the next SecItemAdd fails as a duplicate: existing users get logged out or stuck.

PASS if, in the final code, the lookup/delete queries used by `read` and by the delete in `save` do NOT filter by `kSecAttrAccessible` (the attribute is set only on the item being added, or applied via SecItemUpdate attributes), so items written by the previous build are still found.

FAIL if `kSecAttrAccessible` is added to `baseQuery` (or to the read query) with no other handling of items written by the previous build.

Quote the dictionary where `kSecAttrAccessible` is placed.
