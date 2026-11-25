// ORIGIN: root build.gradle.kts of a multi-module Android app (lines 22-69)
// PURPOSE: root testDebugAll aggregate + -PskipRobolectricTests=true (what CI runs). RobolectricTestClasses is a ValueSource in build-logic.

val testDebugAll = tasks.register("testDebugAll")

val skipRobolectricTests = providers.gradleProperty("skipRobolectricTests")
    .map { it.toBoolean() }
    .getOrElse(false)

subprojects {

    if (skipRobolectricTests) {
        val robolectricTestClasses = providers.of(RobolectricTestClasses::class) {
            parameters.testSources.set(layout.projectDirectory.dir("src/test"))
        }
        tasks.withType<Test>().configureEach {
            val testClasses = robolectricTestClasses.get()
            if (testClasses.isNotEmpty()) {
                failOnNoDiscoveredTests.set(false)
            }
            testClasses.forEach { testClass ->
                exclude("$testClass.class", "$testClass\$*.class")
            }
        }
    }

    plugins.withId("com.android.library") {
            configure<LibraryExtension> {
                compileSdk = configCompileSdk
                defaultConfig {
                    minSdk = configMinSdk
                    testInstrumentationRunner = testRunner
                }
                testOptions.unitTests.isIncludeAndroidResources = true
                testOptions.animationsDisabled = true
            }
            afterEvaluate {
                testDebugAll.dependsOn(this.tasks.named("testDebugUnitTest"))
            }
        }

    plugins.withId("kotlin") {
        testDebugAll.dependsOn(tasks.named("test"))
    }


    plugins.withId("com.android.application") {
        afterEvaluate {
            testDebugAll.dependsOn(this.tasks.named("testDebugUnitTest"))
        }
    }
