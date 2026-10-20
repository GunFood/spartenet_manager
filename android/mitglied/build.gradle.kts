import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

// Mitglieder-App (eigene App, nur für Pächter/Mitglieder). Optional: Signatur für Release-Builds aus keystore.properties (liegt NICHT im Repo) oder aus Umgebungsvariablen (GitHub Secrets)
val signatur = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
fun wert(key: String, env: String): String? = signatur.getProperty(key) ?: System.getenv(env)

android {
    namespace = "de.spartenet.mitglied"
    compileSdk = 35

    defaultConfig {
        applicationId = "de.spartenet.mitglied"
        minSdk = 26
        targetSdk = 35
        versionCode = 3
        versionName = "1.2"
        // Adresse des Managers steht verschleiert in data/Speicher.kt (https://manager.wlan-im-garten.de, nur HTTPS)
    }

    signingConfigs {
        create("release") {
            val datei = wert("storeFile", "SPARTENET_KEYSTORE")
            if (datei != null && file(datei).exists()) {
                storeFile = file(datei)
                storePassword = wert("storePassword", "SPARTENET_KEYSTORE_PASSWORT")
                keyAlias = wert("keyAlias", "SPARTENET_KEY_ALIAS")
                keyPassword = wert("keyPassword", "SPARTENET_KEY_PASSWORT")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            val rel = signingConfigs.getByName("release")
            if (rel.storeFile != null) signingConfig = rel
        }
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf(
            "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api",
            "-opt-in=androidx.compose.foundation.layout.ExperimentalLayoutApi",
        )
    }
    buildFeatures {
        compose = true
    }
    lint {
        abortOnError = false   // Bericht als Artefakt, bricht den Bau aber nicht ab
    }
    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("androidx.work:work-runtime-ktx:2.10.0")       // Benachrichtigungen und Widget im Hintergrund
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
}
