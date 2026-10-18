pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "SparteNet"
include(":manager")  // Manager-App (Vorstand, Mitarbeiter)
include(":mitglied") // Mitglieder-App (Pächter)
