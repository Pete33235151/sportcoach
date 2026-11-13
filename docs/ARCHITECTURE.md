# SportCoach Architektur und Roadmap

## Komponenten

- `integrations/garmin.py`: Offizieller Personal-API-Leser; optionaler inoffizieller Garmin-Connect-Writer strikt getrennt
- `services/recovery.py`: persönlich normierte Signale, Gewichtungen, fehlende Daten, Schmerz-Guardrail
- `services/load.py`: 7/28-Tage-Last, EWMA ATL/CTL, TSB; kein Verletzungsrisiko-Modell
- `services/planning.py`: 7-Tage-Planvorschau, Schwimmen dienstags, konservative Intensität
- `services/analysis.py`: aerobe Entkopplung aus echten Sample-Streams (Adapter noch auszubauen)
- `main.py`: FastAPI, idempotente Speicherung, Audit, explizit bestätigte Schreibvorgänge
- `frontend`: Responsive PWA, reine SVG-Trends, keine externen Gesundheitsdaten-Skripte

## Release-Gates

- **A Demo:** Endpunkte, PWA, Tests; ohne Garmin-Zugang verwendbar
- **B Garmin Live Read:** Personal API Schlüssel, 28-Tage-Feldvalidierung, fehlende Felder, Uhrensync prüfen
- **C FIT:** Download ZIP, sichere ZIP-Validierung, `fitdecode` Records, realistische Laufanalyse
- **D Trainingskalender:** Workout-Typen pace/distance/interval; Dry-run Preview, echte Uhrentest-Einheit
- **E Automatisierung:** gesicherter immer-laufender Host, Scheduler, Benachrichtigungen, Backoffs
- **F iOS Release:** PWA über HTTPS; Native iOS App optional, falls Background-Features benötigt

**Sicherheitsregel:** Keine automatischen Garmin-Kalender-Änderungen ohne explizite Nutzerentscheidung und reversible Updates. Bei deutlichen Schmerzen bzw. mechanischer Gelenkblockade kein intensives Lauftraining vorschlagen.
