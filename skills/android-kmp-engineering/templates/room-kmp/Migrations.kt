// ORIGIN: composeApp/src/commonMain/kotlin/<package>/database/AppDatabaseMigrations.kt of a shipping KMP app
// PURPOSE: house pattern for a Room KMP migration (SQLiteConnection API, ADD COLUMN NOT NULL DEFAULT keeps rows).

package com.example.app.database

import androidx.room.migration.Migration
import androidx.sqlite.SQLiteConnection

internal object AppDatabaseMigrations {

    val MIGRATION_1_2: Migration = object : Migration(1, 2) {
        override fun migrate(connection: SQLiteConnection) {
            // Add non-null column with a safe default to preserve existing rows.
            val statement = connection.prepare(
                "ALTER TABLE items ADD COLUMN current_color TEXT NOT NULL DEFAULT 'gray'"
            )
            try {
                statement.step()
            } finally {
                statement.close()
            }
        }
    }

    val MIGRATION_2_3: Migration = object : Migration(2, 3) {
        override fun migrate(connection: SQLiteConnection) {
            // Tracks whether an item card/banner was opened at least once.
            val statement = connection.prepare(
                "ALTER TABLE items ADD COLUMN was_clicked INTEGER NOT NULL DEFAULT 0"
            )
            try {
                statement.step()
            } finally {
                statement.close()
            }
        }
    }
}
