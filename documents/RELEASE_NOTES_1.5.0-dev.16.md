# QuietWriter 1.5.0-dev.16 — geïntegreerd update-testlab

- Volledige updateketen in een geïsoleerde, niet-uitvoerbare testinstallatie: ondertekend manifest controleren, versiebeleid, ZIP-integriteit, mapwissel en externe gezondheidscontrole.
- Als de nieuwe testversie de gezondheidscontrole niet doorstaat, zet het lab de vorige complete installatie terug.
- De vorige programmamap blijft na een geslaagde update beschikbaar, totdat het definitieve opruimbeleid is geïmplementeerd.
- Extra tests voor ongeldige ondertekening, downgrade, gewijzigde ZIP, foutieve versie en rollback.
- Dit is nog geen productie-updater en de echte QuietWriter.exe wordt niet geïnstalleerd of gestart.
