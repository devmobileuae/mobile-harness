// ORIGIN: written for this skill. Pattern = "migrations are tested with MigrationTestHelper, starting
//         from version 1" + the AppDatabaseMigrations template (schemas 1.json–3.json).
// PURPOSE: prove an upgrade install keeps user rows — the Android equivalent of the SwiftData lesson
//          (in-memory fresh-DB tests stayed green while real installs broke).
// PLACE: composeApp/src/androidInstrumentedTest (or androidUnitTest with Robolectric). Gradle:
//   androidTestImplementation("androidx.room:room-testing:<room>")  and expose schemas:
//   android { sourceSets["androidTest"].assets.srcDir("$projectDir/schemas") }

package com.example.app.database

import androidx.room.testing.MigrationTestHelper
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.execSQL
import androidx.test.platform.app.InstrumentationRegistry
import kotlin.test.Test
import kotlin.test.assertEquals

class AppDatabaseMigrationTest {

    private val dbFile = InstrumentationRegistry.getInstrumentation().targetContext
        .getDatabasePath("migration-test.db")

    private val helper = MigrationTestHelper(
        instrumentation = InstrumentationRegistry.getInstrumentation(),
        file = dbFile,
        driver = BundledSQLiteDriver(),
        databaseClass = AppDatabase::class,
    )

    @Test
    fun v1RowSurvivesUpgradeToLatest() {
        // 1. create the OLD schema exactly as shipped and write a row the way the old build did
        helper.createDatabase(1).apply {
            execSQL("INSERT INTO items (id /* , …v1 columns… */) VALUES ('item_1')")
            close()
        }

        // 2. run every migration the app registers, validating against the exported 3.json
        val db = helper.runMigrationsAndValidate(
            3,
            listOf(AppDatabaseMigrations.MIGRATION_1_2, AppDatabaseMigrations.MIGRATION_2_3),
        )

        // 3. the old row is still there and new columns hold the defaults = previous behaviour
        db.prepare("SELECT current_color, was_clicked FROM items WHERE id = 'item_1'").use {
            it.step()
            assertEquals("gray", it.getText(0))
            assertEquals(0L, it.getLong(1))
        }
        db.close()
    }
}
