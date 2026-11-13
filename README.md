# SportCoach · privates Trainingscockpit

Mobile-first, browserbasierter Sportcoach für Garmin Forerunner 255 und iPhone. Der Quellcode hier ist eine **eigenständig testbare Referenzimplementierung**. Es handelt sich **nicht um eine vollständig im Garmin-Livekonto validierte oder produktionsreife App**.

## Bereits nutzbar (Demo)

- Responsive Dashboard mit Installierbarkeit als Progressive Web App (PWA), HRV/Schlaf/Ruhepuls/Stress/Body Battery und Trends
- Regelbasierte Recovery-Bewertung 0–100 mit persönlichen Baselines, fehlende-Daten-Warnung und Erklärungen
- Trainingsbelastung (7/28 Tage, ATL/CTL, Formindikator) und einfacher Aerobic-Decoupling-Analyzer
- Konservative 7-Tage-Vorschau für Laufen, Radfahren, Schwimmen, Mobilität; Swimming-Kurs dienstags
- Tages-Check-in mit Schmerz-/Blockadesignal und vorsichtigen Schutzregeln
- Lokale Planübernahme nur nach Bestätigung, Audit-Log, wiederholbarer Import
- Offizieller Garmin-Personal-API-Leseadapter als optionale Bibliothek
- *Getrennt* davon optionaler, inoffizieller und standardmäßig ausgeschalteter Garmin-Workout-Upload
- Automatisierbarer Pull-Import während der Server läuft (nicht iPhone-Hintergrund-App)
- Datenexport, SQLite, Docker, CI, Tests

## Windows / VS Code starten

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1
```

Öffne `http://127.0.0.1:8000` oder `http://127.0.0.1:8000/docs`.

**Windows-Antivirus:** Nutze nach Überprüfung deiner Python-Installation `python -m uvicorn`, statt unüberprüfte `.exe`-Dateien freizugeben. Installiere nur Dependencies aus vertrauenswürdigen Quellen.

### Garmin Personal API aktivieren

1. Garmin Connect im Browser öffnen → Einstellungen → **Personal API Key** erstellen.
2. Paket installieren: `.\.venv\Scripts\python.exe -m pip install -e ".[garmin,dev]"`.
3. In der **nicht versionierten** `.env` setzen:

```env
SPORTCOACH_DEMO_MODE=false
SPORTCOACH_DATABASE_URL=sqlite:///./sportcoach-real.sqlite3
SPORTCOACH_GARMIN_PERSONAL_API_KEY=HIER_NUR_LOKAL_EINFUEGEN
SPORTCOACH_AUTO_SYNC=true
SPORTCOACH_SYNC_INTERVAL_MINUTES=180
```

4. App neu starten; `POST /api/garmin/sync` aufrufen oder den Sync-Button im Dashboard nutzen.

**Achtung:** Der tatsächliche Personal-API-Payload muss mit deiner Forerunner 255 überprüft werden. Abweichende Garmin-Feldnamen können dazu führen, dass Werte als fehlend erscheinen. Nicht mit Demo-Werten auffüllen. Die offizielle Personal API ist **read-only** und liefert laut Swagger nicht alle Garmin-Connect-UI-Kennzahlen (z. B. kein dokumentierter Training-Readiness-Endpoint).

### Garmin Workout Upload (experimentell)

Die dritte Bibliothek `python-garminconnect` bietet `upload_running_workout` und `schedule_workout`. Es ist eine **inoffizielle** Schnittstelle, die jederzeit abbrechen kann. Login/MFA muss gegebenenfalls einmalig außerhalb der Web-App erfolgen. Führe keinen Live-Schreibvorgang aus, bevor Du das Konto/Workout-Format getestet hast.

Nur wenn du dies bewusst willst, in `.env` konfigurieren:

```env
SPORTCOACH_ENABLE_GARMIN_WRITE=true
SPORTCOACH_GARMIN_EMAIL=...
SPORTCOACH_GARMIN_PASSWORD=...
SPORTCOACH_GARMIN_TOKEN_DIR=.garmin-tokens
```

Jeder Workout-Upload benötigt zusätzlich eine **einzelne ausdrückliche Bestätigung**. Vorerst sind nur simple zeitbasierte Laufworkouts implementiert; genaue Pace-Intervalle aus der Beschreibung werden noch **nicht** als solche kodiert. Beim unklaren Fehler unbedingt erst Garmin Connect prüfen: Es könnte bereits ein Workout erstellt worden sein.

### iPhone

Die Web-App lässt sich unter HTTPS im Safari-Browser über **Teilen → Zum Home-Bildschirm** hinzufügen. Sie benötigt weiterhin einen laufenden Backend-Server. Der iPhone-Browser allein kann nicht dauerhaft im Hintergrund die Garmin-Daten abfragen. Für Zugriff von unterwegs: **nur nach Einrichtung von HTTPS, Netzwerkschutz und zuverlässiger Authentifizierung**. Starte den Entwicklungsserver nicht ungeschützt mit `--host 0.0.0.0`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Architektur

`Garmin Personal API (offiziell, GET)` → `normalisierte Health-/Activity-Daten` → `SQLite` → `Recovery / Load / Planning` → `FastAPI` → `PWA`

`Bestätigter lokaler Workout-Plan` → `Opt-in GarminConnectWriter (inoffiziell)` → `Garmin Connect Kalender` → `Forerunner 255 nach Synchronisierung`

## Einschränkungen vor produktiver Nutzung

- **Nicht als Medizin-/Verletzungsprognose nutzen.** Es sind heuristische Trainingsindikatoren; Gelenkblockaden/Schmerzen gesondert abklären.
- Recovery-Gewichte und Load-Fallbacks noch nicht gegen individuelle Trainingsdaten validiert.
- Kein vollständiger FIT-Sample-Import; der Analyzer existiert, muss noch mit echten FIT-Daten versorgt werden.
- Keine OAuth-Benutzerverwaltung, keine über das Internet sichere Single-User-Authentifizierung. `SPORTCOACH_ACCESS_TOKEN` schützt API-Endpunkte per Header, die PWA setzt diesen derzeit nicht: nur lokal/geschützt betreiben.
- Kein vollautomatisches Anpassen bereits synchronisierter Garmin-Kalendereinträge; kein gefährliches Auto-Overwrite.
- Garmin Personal API Keys verfallen je nach gewählter Dauer; erneuern.
- Kein durchgehender iPhone-/Watch-End-to-End-Livetest erfolgt.
- Wenn deine bisherige VS-Code-Version schon existiert: **erst Git-Historie/Backup und Diff erstellen, nicht blind überschreiben.**

Siehe [Recherche](docs/RESEARCH.md) und [Architektur](docs/ARCHITECTURE.md).