"""Erzeugt die verschleierte Manager-Adresse für die Mitglieder-App (data/Speicher.kt, Konstante A).

Aufruf: python3 adresse_verschleiern.py https://manager.wlan-im-garten.de
Hinweis: Verschleiern ist keine Verschlüsselung – es verhindert nur, dass die Adresse als Klartext in der APK steht.
"""
import sys

K = [0x5A, 0x13, 0xC7, 0x2E, 0x91, 0x44, 0xB8, 0x6D]
adresse = (sys.argv[1] if len(sys.argv) > 1 else "https://manager.wlan-im-garten.de").strip().rstrip("/")
if not adresse.startswith("https://"):
    sys.exit("Bitte eine Adresse mit https:// angeben – die App erlaubt nur verschlüsselte Verbindungen.")
print("private val A = intArrayOf(" + ", ".join(str(b ^ K[i % len(K)]) for i, b in enumerate(adresse.encode())) + ")")
