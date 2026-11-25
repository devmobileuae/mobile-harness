---
arm: both
type: llm
focus: final
---

The owner's goal is that the background refresh works while the phone is locked for EXISTING users too. Items already on devices keep their old accessibility (`WhenUnlocked`) until something rewrites them, so changing only the add path fixes new installs and fresh logins, not the current 20k users.

PASS if the final code moves existing items to the new accessibility: e.g. a one-time `SecItemUpdate` that sets `kSecAttrAccessible: kSecAttrAccessibleAfterFirstUnlock` on the matching items, or re-saving the token with the new accessibility after a successful read, run at launch/foreground (when the device is unlocked).

FAIL if only the save/add path sets the new accessibility and nothing updates items that already exist (a prose remark without code does not count).

Quote the code that migrates existing items, or say it is missing.
