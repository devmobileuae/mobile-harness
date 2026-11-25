// ORIGIN: navigation/extensions.kt of a KMP + CMP port of an Android app
//         + commonTest/.../navigation/NavigationResultTransportTest.kt (first test)
// PURPOSE: never put a raw @Serializable into SavedStateHandle (Android bundleOf crash).

fun NavController.passReturnResult(targetRoute: String, result: ReturnResult) {
    getBackStackEntry(targetRoute).savedStateHandle[resultKey] = result.encodeReturnResult()
}

internal fun ReturnResult.encodeReturnResult(): SavedState =
    encodeToSavedState(ReturnResult.serializer(), this)

internal fun SavedState.decodeReturnResult(): ReturnResult =
    decodeFromSavedState(ReturnResult.serializer(), this)

// ---- test ----
class NavigationResultTransportTest {

    @Test
    fun navigationBackResult_roundTripsThroughSavedStateTransport() {
        val original = ReturnResult.NavigationBackResult(refresh = true, showShimmer = true)

        // write side (passReturnResult): encode to SavedState, store at resultKey
        val handle = SavedStateHandle()
        handle[resultKey] = original.encodeReturnResult()

        // read side (ResultReceiver): observe the SavedState, decode
        val stored: SavedState? = handle.getStateFlow<SavedState?>(resultKey, null).value
        assertNotNull(stored, "transport must store a non-null SavedState, never a bare model")
        assertEquals(original, stored.decodeReturnResult())
