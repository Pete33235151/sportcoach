# SportCoach in ein privates GitHub-Repository übertragen

Diese ZIP ist ein **neues, eigenständiges Projekt**. Falls du bereits einen lokalen MVP hast, **zuerst sichern** und nur nach einem Vergleich zusammenführen.

1. Auf https://github.com/new ein neues Repository namens `sportcoach` erstellen. Empfehlung: **Private**. Kein README über GitHub initialisieren (dieses Projekt hat eines).
2. ZIP in einen *neuen* Ordner entpacken und diesen in VS Code öffnen.
3. In VS Code Terminal (PowerShell) bei installiertem Git:

```powershell
git init
git add .
git commit -m "SportCoach PWA MVP mit Garmin Personal API"
git branch -M main
git remote add origin https://github.com/DEIN-GITHUB-NAME/sportcoach.git
git push -u origin main
```

4. Unbedingt vor dem Push `git status` kontrollieren. **Niemals `.env`, Garmin-Passwörter, API-Keys, Token-Dateien, FIT-Dateien oder Gesundheitsdaten committen.**
5. Anschließend kann die verbundene GitHub-App Änderungen als Branch + Pull Request direkt ins Repository schreiben.

Bei bereits bestehendem SportCoach-Repo: `git init` nicht ausführen und keine Dateien blind überschreiben. Zuerst lokal `git status`, `git diff` und ggf. eine Sicherheitskopie erstellen.
