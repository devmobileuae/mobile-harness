// ORIGIN: composeApp/src/commonMain/kotlin/<package>/database/Database.kt of a shipping KMP app (header lines)
// PURPOSE: @Database with exportSchema + @ConstructedBy expect object. Gradle: room { schemaDirectory("$projectDir/schemas") }
//   + ksp: kspCommonMainMetadata, kspAndroid, kspIosArm64, kspIosSimulatorArm64 (libs.room.compiler).

package com.example.app.database

import androidx.room.ConstructedBy
import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.RoomDatabaseConstructor
import androidx.room.TypeConverters
import com.example.app.database.dao.DailyPickDao
import com.example.app.database.dao.ItemDao
import com.example.app.database.entities.DailyPick
import com.example.app.database.entities.Item

/**
 * Main Room database for the app
 * Internal - use ItemRepository instead
 */
@Database(
    entities = [
        DailyPick::class,
        Item::class
    ],
    version = 3,
    exportSchema = true
)
@TypeConverters(
    ModeConverter::class,
    ItemColorConverter::class
)
@ConstructedBy(AppDatabaseConstructor::class)
internal abstract class AppDatabase : RoomDatabase() {
    internal abstract fun dailyPickDao(): DailyPickDao
    internal abstract fun itemDao(): ItemDao
}

@Suppress("NO_ACTUAL_FOR_EXPECT")
internal expect object AppDatabaseConstructor: RoomDatabaseConstructor<AppDatabase> {
    override fun initialize(): AppDatabase
}
