---
arm: both
type: llm
weight: 3
---

PASS if the checklist explicitly includes updating the Firebase Remote Config update gate (`appUpdate` or "force/soft update gate") in BOTH the Android and the iOS Firebase projects (they are separate projects), together with the version bump. FAIL if the update gate is missing or only one platform's Firebase project is mentioned.
