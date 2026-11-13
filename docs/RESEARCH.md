# Repository- und API-Recherche (13.11.2026)

Stand der öffentlichen Quellen; Features können sich ändern. Wir binden keinen fremden Code durch Copy/Paste ein.

| Projekt / Dienst | Lizenz/API | Passende Funktionen | Empfehlung |
|---|---|---|---|
| [Garmin Connect Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/) | Offizielle persönliche API, nur GET; Key mit Ablauf | HRV, Sleep, Body Battery, Daily Summaries, Aktivitäten, FIT-Downloads | **Primärer Leseweg für privaten SportCoach** |
| [Garmin connect-personal-api-python](https://github.com/garmin/connect-personal-api-python) | Apache-2.0 | Auth Token Caching, read-only Requests, CLI | **Direkt als Bibliothek** |
| [cyberjunky/python-garminconnect](https://github.com/cyberjunky/python-garminconnect) | MIT, inoffiziell | Health, Calendar, strukturierte Workouts, Schedule/Push | Optionaler Writer, standardmäßig aus |
| [ching-kuo/garmin-py](https://github.com/ching-kuo/garmin-py) | MIT | coach_snapshot, preview/apply, reconciliation, MCP | Architekturvorlage; nicht als Basis-Fork |
| [404i/coach](https://github.com/404i/coach) | MIT Kern, GarminDB GPLv2-Unterbau | Recovery Rules, adaptive Goals, Garmin Sync, Safety | Ideen prüfen, keinen fremden Code kopieren |
| [Intervals.icu](https://www.intervals.icu/features/open-api/) | Hostingplattform, Open REST API | Aktivitäten, Wellness, Plan-Workouts, Webhooks, API Keys | Starke Alternative/optionaler Training-Kalender |
| [sagarmehta1/running-coach](https://github.com/sagarmehta1/running-coach) | Lizenz einzeln prüfen | Garmin SQLite, Laufanalyse, Intervals.icu Builder | Ideen/Analysemodell, kleiner experimenteller Stand |
| [fitdecode](https://github.com/polyvertex/fitdecode) | MIT | FIT-Record Decoder | Für Detailanalyse anschließen |
| [Garmin Daily Suggested Workouts](https://www8.garmin.com/manuals/webhelp/GUID-676967A0-1B23-4384-9BC9-76F3D643F1C8/EN-US/GUID-1F857C7A-31A2-46AF-A639-2C3F5ECC3AF1.html) | Garmin-eigen | Tägliche trainings-/erholungsabhängige Vorschläge auf FR255 | Kostenloser Benchmark, bereits ohne App nutzbar |
| [Runna](https://support.runna.com/en/articles/6169639-using-your-garmin-watch-with-runna) | Dienst, proprietär | Laufpläne, bi-direktionale Garmin-Synchronisierung | Alternative ohne Eigenentwicklung |
| [Athletica](https://support.athletica.ai/hc/en-us/articles/23513848128923-How-to-Get-Your-Athletica-Workouts-To-Sync-With-Garmin) | Dienst, proprietär | Adaptive Multisport-Workouts, Garmin-Upload | Alternative, insbesondere Triathlon |
| [FitTrackee](https://codeberg.org/SamR1/FitTrackee) | GPLv3 | Self-hosted Aktivitätstracking, GPX | Kein kompletter Coach; nicht als Backend-Basis |
| [TrainingPeaks Garmin Sync](https://support.garmin.com/en-US/?faq=jnm4aY5LM880wNP6LWm1n8) | Plattformintegration | Strukturierte Workouts → Garmin | Kommerzielle Alternative, API-Zugang genehmigungspflichtig |
| [RUNALYZE](https://runalyze.com/help/article/how-to-import-activities-and-health-data?_locale=en) | Dienst | Umfangreiche Trainingsanalysen, Garmin-Sync in Leserichtung | Für Benchmarks interessant, kein Workout Writer |

## Wichtige Korrektur gegenüber früheren Plänen

- Garmin **Personal API** existiert nun für persönliche Nutzerdaten; keine Anmeldung zum Business Program nötig, aber **kein Workout-Write** (Swagger: GET).
- Business **Starter** und **Enterprise** existieren; der Garmin-API-Überblick nennt Training API auch für Starter, einzelne Unterseiten haben noch Enterprise-Hinweise. Berechtigung individuell prüfen.
- Für die Forerunner 255 geht ein geplantes Workout nach Garmin-Connect-Synchronisation auf die Uhr; der Upload an Garmin Connect ist nicht automatisch gleichbedeutend mit Empfang auf der Uhr.
- Diese Referenzimplementierung ersetzt nicht automatisch deine bereits lokal erstellte erste MVP-Version.

## Quellen

- https://developer.garmin.com/gc-developer-program/overview/
- https://developer.garmin.com/gc-developer-program/personal/swagger-docs/
- https://support.garmin.com/en-US/?faq=HfTwLfw1Gn2A7WS1GdAMH8
- https://github.com/garmin/connect-personal-api-python
- https://github.com/cyberjunky/python-garminconnect
- https://github.com/ching-kuo/garmin-py
- https://github.com/404i/coach
- https://www.intervals.icu/features/open-api/
- https://www8.garmin.com/manuals/webhelp/GUID-676967A0-1B23-4384-9BC9-76F3D643F1C8/DE-DE/GUID-D6E80F0C-F319-47D1-AF95-0884F3386635.html

- https://support.garmin.com/en-GB/?faq=oYknGZ910l1pfBNzkDHX6A
- https://support.runna.com/en/articles/6169639-using-your-garmin-watch-with-runna
- https://support.athletica.ai/hc/en-us/articles/23513848128923-How-to-Get-Your-Athletica-Workouts-To-Sync-With-Garmin
