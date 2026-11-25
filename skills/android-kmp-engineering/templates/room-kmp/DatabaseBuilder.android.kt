// ORIGIN: composeApp/src/androidMain/kotlin/<package>/di/databaseModule.kt of a shipping KMP app
// PURPOSE: Android builder + Koin wiring with BundledSQLiteDriver, IO query context, every migration added.

@file:JvmName("DatabaseModuleAndroid")

package com.example.app.di

import android.content.Context
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import com.example.app.database.AppDatabaseMigrations
import com.example.app.database.AppDatabase
import kotlinx.coroutines.Dispatchers
import org.koin.dsl.module


internal fun getDatabaseBuilder(context: Context): RoomDatabase.Builder<AppDatabase> {
    val appContext = context.applicationContext
    val dbFile = appContext.getDatabasePath("app_database")
    return Room.databaseBuilder<AppDatabase>(
        context = appContext,
        name = dbFile.absolutePath
    )
}

actual val databasePlatformModule = module {
    single<AppDatabase> {
        getDatabaseBuilder(get())
            // comment driver below for database inspector visibility
            .setDriver(BundledSQLiteDriver())
            .setQueryCoroutineContext(Dispatchers.IO)
            .addMigrations(AppDatabaseMigrations.MIGRATION_1_2)
            .addMigrations(AppDatabaseMigrations.MIGRATION_2_3)
            .build()
    }
}
