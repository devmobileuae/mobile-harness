// ORIGIN: composeApp/src/iosMain/kotlin/<package>/di/databaseModule.kt of a shipping KMP app (builder only)
// PURPOSE: iOS builder path in NSDocumentDirectory. Drop the println debugging when copying.

package com.example.app.di

import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import com.example.app.database.AppDatabaseMigrations
import com.example.app.database.AppDatabase
import kotlinx.cinterop.ExperimentalForeignApi
import org.koin.dsl.module
import platform.Foundation.NSDocumentDirectory
import platform.Foundation.NSFileManager
import platform.Foundation.NSUserDomainMask

actual val databasePlatformModule = module {
    single<AppDatabase> {
        try {
            val database = getDatabaseBuilder()
                .setDriver(BundledSQLiteDriver())
                .addMigrations(AppDatabaseMigrations.MIGRATION_1_2)
                .addMigrations(AppDatabaseMigrations.MIGRATION_2_3)
                .build()
            database
        } catch (e: Exception) {
            throw e
        }
    }
}

/**
 * Creates Room database builder for iOS
 */
@OptIn(ExperimentalForeignApi::class)
internal fun getDatabaseBuilder(): RoomDatabase.Builder<AppDatabase> {
    return try {
        val docDir = NSFileManager.defaultManager.URLForDirectory(
            directory = NSDocumentDirectory,
            inDomain = NSUserDomainMask,
            appropriateForURL = null,
            create = false,
            error = null
        )
        val dbFilePath = requireNotNull(docDir?.path) + "/app_database.db"
        println("iOS Database path: $dbFilePath")

        val builder = Room.databaseBuilder<AppDatabase>(
            name = dbFilePath
        )
        println("iOS Database builder created successfully")
        builder
    } catch (e: Exception) {
        println("iOS Database builder creation failed: ${e.message}")
        println("Stack trace: ${e.stackTraceToString()}")
        throw e
    }
}
