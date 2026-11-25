---
type: llm
arm: both
focus: final
---
PASS if the answer asks for the app's IDs and links (for example bundle ID, App Store Connect app ID, PostHog project ID, RevenueCat project) and, for API keys or tokens, tells the user to put them in a local file (such as local/secrets.env) instead of pasting them into the chat.
FAIL if it asks the user to paste an API key, token or private key into the chat, or if it does not ask for any app-specific ID at all.
