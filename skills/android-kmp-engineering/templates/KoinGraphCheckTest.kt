// ORIGIN: written for this skill. Many Koin repos have NO graph test; adding it is a
//         change to propose to the owner, not to slip into an unrelated diff.
// PURPOSE: catch `get()` resolving an unbound interface (InstanceCreationException on the first screen that resolves it)
//          at test time instead of on the device.
// PLACE: composeApp/src/androidUnitTest (Koin's verify() is JVM-only). Needs koin-test (same version as koin).

package com.example.app.di

import android.content.Context
import io.ktor.client.HttpClient
import org.koin.core.annotation.KoinExperimentalAPI
import org.koin.test.verify.verify
import kotlin.test.Test

class KoinGraphCheckTest {

    @OptIn(KoinExperimentalAPI::class)
    @Test
    fun everyDefinitionResolvesItsConstructorTypes() {
        // the module list App/AppInitializer starts with; platform types the test JVM cannot build go in extraTypes
        sharedModules.verify(
            extraTypes = listOf(
                Context::class,
                HttpClient::class,
            ),
        )
    }
}

// Still open the touched screen on a device: verify() checks constructor types, not lambdas that call
// get<T>() at runtime or late-init platform globals (iosRemoteConfigBridge, MainApp.appContext).
