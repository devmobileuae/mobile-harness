// ORIGIN: composeApp/build.gradle.kts of a KMP calling app (one Gradle module, iOS + Android)
// PURPOSE: one build number for both apps — Android versionCode read from the iOS xcconfig; fail, never guess.

// One release build number for both apps, kept where Xcode reads it (iOS CFBundleVersion is
// $(CURRENT_PROJECT_VERSION)). Fail the build rather than guess a versionCode.
val releaseBuildNumber: Int = providers
    .fileContents(rootProject.layout.projectDirectory.file("iosApp/Configuration/Config.xcconfig"))
    .asText.get()
    .lineSequence()
    .firstNotNullOfOrNull { Regex("""^\s*CURRENT_PROJECT_VERSION\s*=\s*(\d+)\s*$""").find(it) }
    ?.groupValues?.get(1)?.toInt()
    ?: error("iosApp/Configuration/Config.xcconfig: CURRENT_PROJECT_VERSION must be a plain integer (it is also Android's versionCode)")

// then in android { defaultConfig { versionCode = releaseBuildNumber; versionName = "2026.11.1" } }
