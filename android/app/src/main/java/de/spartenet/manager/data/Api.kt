package de.spartenet.manager.data

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

/** Fehler vom Manager (Text aus {"fehler": …}) oder von der Verbindung */
class ApiFehler(
    val code: Int,
    message: String,
    val zweiterFaktor: Boolean = false,
) : Exception(message) {
    val abgemeldet: Boolean get() = code == 401 && !zweiterFaktor
}

/** Datei-Antwort (z. B. Rechnung als PDF) */
class Datei(val daten: ByteArray, val typ: String, val name: String)

/**
 * Schlanker Client für die SparteNet-Manager-Schnittstelle.
 * Jede Anfrage trägt „Authorization: Bearer sna_…“ – der Manager prüft damit dieselben Rechte wie in der Oberfläche.
 * Der Schlüssel wird nie protokolliert und nie in Fehlermeldungen ausgegeben.
 */
class Api(basis: String, @Volatile var token: String?) {

    val basis: String = normalisieren(basis)

    val unverschluesselt: Boolean get() = basis.startsWith("http://")

    suspend fun get(pfad: String, parameter: Map<String, String> = emptyMap()): JSONObject =
        anfrage("GET", pfad + abfrage(parameter), null)

    suspend fun post(pfad: String, body: JSONObject = JSONObject()): JSONObject =
        anfrage("POST", pfad, body)

    suspend fun datei(pfad: String, parameter: Map<String, String> = emptyMap()): Datei = withContext(Dispatchers.IO) {
        val c = verbinden("GET", pfad + abfrage(parameter))
        try {
            val code = c.responseCode
            if (code !in 200..299) throw fehlerAus(code, lesen(c, false))
            val typ = c.contentType ?: "application/octet-stream"
            val dispo = c.getHeaderField("Content-Disposition") ?: ""
            val name = Regex("filename=\"?([^\";]+)\"?").find(dispo)?.groupValues?.get(1) ?: "Datei"
            Datei(c.inputStream.use { it.readBytes() }, typ, name)
        } catch (e: ApiFehler) {
            throw e
        } catch (e: IOException) {
            throw verbindungsFehler(e)
        } finally {
            c.disconnect()
        }
    }

    /** Anmeldung – liefert die Antwort mit „token“ oder wirft ApiFehler (zweiterFaktor = true, wenn ein Code fehlt/falsch ist) */
    suspend fun anmelden(benutzer: String, passwort: String, code: String, geraet: String, merken: String? = null): JSONObject {
        val body = JSONObject()
            .put("benutzer", benutzer)
            .put("passwort", passwort)
            .put("geraet", geraet)
        if (code.isNotBlank()) body.put("code", code.trim())
        if (!merken.isNullOrEmpty()) body.put("merken", merken)
        val a = anfrage("POST", "/api/v1/app/anmelden", body, mitToken = false)
        if (!a.optBoolean("ok") || a.s("token").isEmpty()) {
            throw ApiFehler(401, a.s("fehler").ifEmpty { "Anmeldung fehlgeschlagen." }, a.optBoolean("zweiter_faktor"))
        }
        return a
    }

    private suspend fun anfrage(methode: String, pfad: String, body: JSONObject?, mitToken: Boolean = true): JSONObject =
        withContext(Dispatchers.IO) {
            val c = verbinden(methode, pfad, mitToken)
            try {
                if (body != null) {
                    val roh = body.toString().toByteArray(Charsets.UTF_8)
                    c.doOutput = true
                    c.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                    c.setFixedLengthStreamingMode(roh.size)
                    c.outputStream.use { it.write(roh) }
                }
                val code = c.responseCode
                val text = lesen(c, code in 200..299)
                if (code !in 200..299) throw fehlerAus(code, text)
                if (text.isBlank()) JSONObject() else try {
                    JSONObject(text)
                } catch (e: Exception) {
                    throw ApiFehler(code, "Unerwartete Antwort vom Server – ist die Adresse richtig (SparteNet Manager ab 5.0)?")
                }
            } catch (e: ApiFehler) {
                throw e
            } catch (e: IOException) {
                throw verbindungsFehler(e)
            } finally {
                c.disconnect()
            }
        }

    private fun verbinden(methode: String, pfad: String, mitToken: Boolean = true): HttpURLConnection {
        val c = URL(basis + pfad).openConnection() as HttpURLConnection
        c.requestMethod = methode
        c.connectTimeout = 15_000
        c.readTimeout = 60_000
        c.instanceFollowRedirects = false
        c.useCaches = false
        c.setRequestProperty("Accept", "application/json")
        c.setRequestProperty("User-Agent", "SparteNet-Android/1.0")
        val t = token
        if (mitToken && t != null) c.setRequestProperty("Authorization", "Bearer $t")
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
            403 -> "Für diese Funktion fehlt Ihrem Konto das Recht."
            404 -> "Nicht gefunden – ist der Manager aktuell (ab Version 5.0)?"
            429 -> "Zu viele Versuche – bitte kurz warten."
            in 300..399 -> "Der Server leitet um – bitte die Adresse mit https:// eintragen."
            else -> "Fehler $code vom Server."
        }
        return ApiFehler(code, meldung, j?.optBoolean("zweiter_faktor") == true)
    }

    private fun verbindungsFehler(e: IOException): ApiFehler = ApiFehler(
        0, when (e) {
            is UnknownHostException -> "Server nicht gefunden – Adresse prüfen."
            is SocketTimeoutException -> "Der Server antwortet nicht (Zeitüberschreitung)."
            is SSLException -> "Sichere Verbindung fehlgeschlagen (Zertifikat prüfen)."
            else -> "Keine Verbindung zum Manager: ${e.javaClass.simpleName}"
        }
    )

    companion object {
        fun normalisieren(adresse: String): String {
            var a = adresse.trim().trimEnd('/')
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

// ---- kleine JSON-Helfer (org.json liefert bei null sonst den Text "null") ----------------------------------
fun JSONObject.s(k: String): String = if (isNull(k)) "" else optString(k, "")
fun JSONObject.i(k: String, standard: Int = 0): Int = if (isNull(k)) standard else optInt(k, standard)
fun JSONObject.d(k: String): Double = if (isNull(k)) 0.0 else optDouble(k, 0.0).let { if (it.isNaN()) 0.0 else it }
fun JSONObject.o(k: String): JSONObject = optJSONObject(k) ?: JSONObject()
fun JSONObject.liste(k: String): List<JSONObject> = optJSONArray(k).objekte()
fun JSONObject.texte(k: String): List<String> = optJSONArray(k).texte()

fun JSONArray?.objekte(): List<JSONObject> {
    if (this == null) return emptyList()
    return (0 until length()).mapNotNull { optJSONObject(it) }
}

fun JSONArray?.texte(): List<String> {
    if (this == null) return emptyList()
    return (0 until length()).map { if (isNull(it)) "" else optString(it, "") }
}

fun JSONObject.textMap(k: String): LinkedHashMap<String, String> {
    val m = LinkedHashMap<String, String>()
    val o = optJSONObject(k) ?: return m
    for (key in o.keys()) m[key] = o.s(key)
    return m
}

fun geld(betrag: Double): String = String.format(java.util.Locale.GERMANY, "%,.2f €", betrag)
