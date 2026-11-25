// ORIGIN: a call-recording controller test in a KMP calling app (commonTest, first 45 lines; package renamed)
// PURPOSE: testing a class with an endless while(true){delay} ticker without hanging.

package com.example.app.calls.domain

import com.example.app.calls.data.FakeAudioPlayer
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * The controller runs an endless 200ms position ticker while playing. Tests therefore:
 *  - run the controller on [kotlinx.coroutines.test.TestScope.backgroundScope] so the ticker is
 *    auto-cancelled at test end and never blocks completion, and
 *  - drive everything on a single [UnconfinedTestDispatcher] passed into `runTest` (so launched
 *    work executes eagerly and shares runTest's scheduler — using a separate scheduler hangs).
 * We never call advanceUntilIdle(): that would spin the infinite ticker forever.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class CallRecordingControllerTest {

    private val repository = object : RecordingRepository {
        override suspend fun getLocalPath(callId: String, step: Int) =
            Result.success("/cache/${callId}_$step.mp3")
    }

    @Test
    fun play_loads_and_marks_playing() = runTest(UnconfinedTestDispatcher()) {
        val player = FakeAudioPlayer()
        val c = CallRecordingController(player, repository, backgroundScope)
        c.play("call-1", 2)

        val key = "call-1_2"
        assertEquals(key, c.state.value.audibleKey)
        assertEquals(CallRecordingController.Status.Playing, c.state.value.rows[key]?.status)
        assertEquals(10_000L, c.state.value.rows[key]?.durationMs)
        assertTrue(player.playing)
    }

    @Test
    fun starting_b_pauses_a_and_remembers_position() = runTest(UnconfinedTestDispatcher()) {
        val player = FakeAudioPlayer()
        val c = CallRecordingController(player, repository, backgroundScope)
        c.play("a", 1)
}
