package de.spartenet.manager.ui

import androidx.compose.material3.SnackbarHostState
import de.spartenet.manager.data.Api
import de.spartenet.manager.data.s
import de.spartenet.manager.data.textMap
import org.json.JSONObject

/** Angemeldetes Konto: Schnittstelle, Rechte und Rückmeldungen an die Oberfläche */
class Sitzung(
    val api: Api,
    ich: JSONObject,
    val version: String,
    val snackbar: SnackbarHostState,
    private val beiAbgelaufen: () -> Unit,
) {
    val name: String = ich.s("name")
    val admin: Boolean = ich.optBoolean("admin")
    val rechtText: String = ich.s("recht_text")
    private val bereiche: Map<String, String> = ich.textMap("bereiche")

    /** dieselbe Logik wie im Manager: Administrator darf alles, sonst Stufe „lesen“ bzw. „schreiben“ je Bereich */
    fun darf(bereich: String, stufe: String = "lesen"): Boolean {
        if (admin) return true
        val rang = mapOf("kein" to 0, "lesen" to 1, "schreiben" to 2)
        return (rang[bereiche[bereich] ?: "kein"] ?: 0) >= (rang[stufe] ?: 1)
    }

    suspend fun melden(text: String) {
        snackbar.currentSnackbarData?.dismiss()
        snackbar.showSnackbar(text)
    }

    /** erste Zeile aus „log“ einer Antwort melden */
    suspend fun meldenLog(a: JSONObject) {
        val log = a.optJSONArray("log")
        if (log != null && log.length() > 0) melden(log.optString(0))
    }

    fun abgelaufen() = beiAbgelaufen()
}
