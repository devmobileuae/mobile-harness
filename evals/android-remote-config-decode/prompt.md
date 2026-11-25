---
name: android-remote-config-decode
tags: [android-kmp-engineering]
runs: 3
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our habit tracker is a KMP app (Compose Multiplatform, kotlinx.serialization, Firebase Remote Config via a wrapper that gives us the raw string). We keep one Remote Config param `remote` of type JSON. QA edits it by hand in the Firebase console. Current value:

```json
{
  "allowedIds": ["u_19f2", "u_77ab"],
  "appUpdate": {
    "minSupportedVersion": "41",
    "latestVersion": "42",
    "storeUrl": "https://play.google.com/store/apps/details?id=com.example.habits"
  }
}
```

`allowedIds` is the allow-list for the new voice-notes feature; `appUpdate` drives the "please update" screen. Write the commonMain code that turns the raw string into something the app can query: `isVoiceNotesOn(userId)` and `updateGate(currentBuild: Int)`. If the value is missing or broken, fall back to safe defaults. Just the code and a short note.
