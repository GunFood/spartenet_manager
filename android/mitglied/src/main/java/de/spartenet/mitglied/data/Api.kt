package de.spartenet.mitglied.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URL
import java.net.URLEncoder
import java.net.UnknownHostException
import javax.net.ssl.SSLException

/** Fehler vom Mitgliederbereich (Text aus {"fehler": …}) oder von der Verbindung */
class ApiFehler(val code: Int, message: String) : Exception(message) {
    val abgemeldet: Boolean get() = code == 401
}

/** Datei-Antwort (Rechnung als PDF) */
class Datei(val daten: ByteArray, val typ: String, val name: String)

/**
 * Client für den Mitgliederbereich (/mein) des SparteNet Managers.
 * Anmeldung mit E-Mail-Adresse und Code aus der E-Mail; danach trägt jede Anfrage „Authorization: Bearer snm_…“.
 * Der Schlüssel gilt nur für den Mitgliederbereich (kein Zugang zum Manager) und wird nie protokolliert.
 */
class Api(basis: String, @Volatile var token: String?) {

    val basis: String = normalisieren(basis)

    val unverschluesselt: Boolean get() = basis.startsWith("http://")

    suspend fun post(pfad: String, body: JSONObject = JSONObject()): JSONObject = withContext(Dispatchers.IO) {
        val c = verbinden("POST", pfad)
        try {
            val roh = body.toString().toByteArray(Charsets.UTF_8)
            c.doOutput = true
            c.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            c.setFixedLengthStreamingMode(roh.size)
            c.outputStream.use { it.write(roh) }
            val code = c.responseCode
            val text = lesen(c, code in 200..299)
            if (code !in 200..299) throw fehlerAus(code, text)
            if (text.isBlank()) JSONObject() else try {
                JSONObject(text)
            } catch (e: Exception) {
                throw ApiFehler(code, "Unerwartete Antwort – ist die Adresse richtig (SparteNet Manager ab 5.6)?")
            }
        } catch (e: ApiFehler) {
            throw e
        } catch (e: IOException) {
            throw verbindungsFehler(e)
        } finally {
            c.disconnect()
        }
    }

    suspend fun datei(pfad: String, parameter: Map<String, String> = emptyMap()): Datei = withContext(Dispatchers.IO) {
        val c = verbinden("GET", pfad + abfrage(parameter))
        try {
            val code = c.responseCode
            if (code !in 200..299) throw fehlerAus(code, lesen(c, false))
            val dispo = c.getHeaderField("Content-Disposition") ?: ""
            val name = Regex("filename=\"?([^\";]+)\"?").find(dispo)?.groupValues?.get(1) ?: "Rechnung.pdf"
            Datei(c.inputStream.use { it.readBytes() }, c.contentType ?: "application/pdf", name)
        } catch (e: ApiFehler) {
            throw e
        } catch (e: IOException) {
            throw verbindungsFehler(e)
        } finally {
            c.disconnect()
        }
    }

    /** prüft, ob unter der Adresse ein eingeschalteter Mitgliederbereich erreichbar ist; liefert den Titel */
    suspend fun info(): JSONObject = post("/mein/info")

    /** Einmalcode anfordern – der Manager verschickt ihn über seinen E-Mail-Versand an die beim Verein hinterlegte Adresse */
    suspend fun codeAnfordern(email: String): String = post("/mein/code", JSONObject().put("email", email.trim()).put("app", true)).s("text")

    /** Code aus der E-Mail → dauerhafter Schlüssel für diese App */
    suspend fun anmelden(email: String, code: String, geraet: String): String {
        val a = post("/mein/anmelden", JSONObject().put("email", email.trim()).put("code", code.trim()).put("app", true).put("geraet", geraet))
        return a.s("token").ifEmpty { throw ApiFehler(401, a.s("fehler").ifEmpty { "Anmeldung fehlgeschlagen." }) }
    }

    private fun verbinden(methode: String, pfad: String): HttpURLConnection {
        // nur verschlüsselt: der Anmelde-Schlüssel darf nie im Klartext übertragen werden
        if (!basis.startsWith("https://")) throw ApiFehler(0, "Nur verschlüsselte Verbindungen (https) sind erlaubt.")
        val c = URL(basis + pfad).openConnection() as HttpURLConnection
        c.requestMethod = methode
        c.connectTimeout = 15_000
        c.readTimeout = 60_000
        c.instanceFollowRedirects = false
        c.useCaches = false
        c.setRequestProperty("Accept", "application/json")
        c.setRequestProperty("User-Agent", "SparteNet-Mitglied-Android/1.0")
        token?.let { c.setRequestProperty("Authorization", "Bearer $it") }
        return c
    }

    private fun lesen(c: HttpURLConnection, ok: Boolean): String {
        val s = (if (ok) c.inputStream else c.errorStream) ?: return ""
        return s.use { it.readBytes().toString(Charsets.UTF_8) }
    }

    private fun fehlerAus(code: Int, text: String): ApiFehler {
        val j = try { JSONObject(text) } catch (e: Exception) { null }
        val meldung = j?.s("fehler")?.ifEmpty { null } ?: when (code) {
            401 -> "Nicht (mehr) angemeldet – bitte neu anmelden."
            404 -> "Der Mitgliederbereich ist unter dieser Adresse nicht eingeschaltet."
            429 -> "Zu viele Versuche – bitte kurz warten."
            in 300..399 -> "Der Server leitet um – bitte die Adresse mit https:// eintragen."
            else -> "Fehler $code vom Server."
        }
        return ApiFehler(code, meldung)
    }

    private fun verbindungsFehler(e: IOException): ApiFehler = ApiFehler(
        0, when (e) {
            is UnknownHostException -> "Server nicht gefunden – Adresse prüfen."
            is SocketTimeoutException -> "Der Server antwortet nicht (Zeitüberschreitung)."
            is SSLException -> "Sichere Verbindung fehlgeschlagen (Zertifikat prüfen)."
            else -> "Keine Verbindung: ${e.javaClass.simpleName}"
        }
    )

    companion object {
        fun normalisieren(adresse: String): String {
            var a = adresse.trim().trimEnd('/')
            if (a.endsWith("/mein")) a = a.removeSuffix("/mein")      // falls jemand die Seiten-Adresse einträgt
            if (a.isEmpty()) return a
            if (!a.startsWith("http://") && !a.startsWith("https://")) a = "https://$a"
            return a
        }

        fun abfrage(p: Map<String, String>): String =
            if (p.isEmpty()) "" else "?" + p.entries.joinToString("&") {
                URLEncoder.encode(it.key, "UTF-8") + "=" + URLEncoder.encode(it.value, "UTF-8")
            }
    }
}

// ---- kleine JSON-Helfer ------------------------------------------------------------------------------------
fun JSONObject.s(k: String): String = if (isNull(k)) "" else optString(k, "")
fun JSONObject.i(k: String, standard: Int = 0): Int = if (isNull(k)) standard else optInt(k, standard)
fun JSONObject.d(k: String): Double = if (isNull(k)) 0.0 else optDouble(k, 0.0).let { if (it.isNaN()) 0.0 else it }
fun JSONObject.b(k: String): Boolean = !isNull(k) && optBoolean(k, false)
fun JSONObject.o(k: String): JSONObject? = optJSONObject(k)
fun JSONObject.liste(k: String): List<JSONObject> = optJSONArray(k).objekte()
fun JSONObject.texte(k: String): List<String> = optJSONArray(k).let { a -> if (a == null) emptyList() else (0 until a.length()).map { a.optString(it, "") } }
fun JSONObject.zahlen(k: String): List<Double> = optJSONArray(k).let { a -> if (a == null) emptyList() else (0 until a.length()).map { a.optDouble(it, 0.0) } }

fun JSONArray?.objekte(): List<JSONObject> {
    if (this == null) return emptyList()
    return (0 until length()).mapNotNull { optJSONObject(it) }
}

fun geld(betrag: Double): String = String.format(java.util.Locale.GERMANY, "%,.2f €", betrag)

/** Rang zum Vergleichen von Tarifen (Preis, Download, Upload) – wie im Manager */
fun rangHoeher(a: List<Double>, b: List<Double>?): Boolean {
    if (b == null || b.size < 3 || a.size < 3) return false
    for (n in 0 until 3) {
        if (a[n] > b[n]) return true
        if (a[n] < b[n]) return false
    }
    return false
}
