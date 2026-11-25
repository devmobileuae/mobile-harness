---
name: mobile-swiftdata-migration
tags: [mobile, incident]
runs: 3
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

The app (already on the App Store, people have data in it) has a SwiftData model:

```swift
@Model final class TaskItem { var title: String; var done: Bool
  init(title: String, done: Bool = false) { self.title = title; self.done = done } }
```
Add a field priority: Int with a default value of 0. Just show the new model code.
