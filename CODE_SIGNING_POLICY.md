# Release-integriteit

QuietWriter gebruikt **geen Authenticode-certificaat en geen SignPath**. Windows kan daarom een waarschuwing over een onbekende uitgever tonen.

## Hoe je weet dat een download echt is
- Officiële releases staan alleen op https://github.com/gen-x-coder/QuietWriter/releases.
- Bij iedere portable zip hoort een `.sha256`-bestand. Controleer het met:
  `Get-FileHash QuietWriter-windows-portable.zip -Algorithm SHA256`
- De build is reproduceerbaar beschreven in `build_exe.cmd` en `documents/RELEASE_PROCESS.md` (vaste Python- en pip-versies, bootloader uit bron, geen UPX).

## Bijwerken vanuit de app (vanaf 1.5.1)
QuietWriter gebruikt [Velopack](https://velopack.io) om zichzelf bij te werken:
- de updatefeed (`releases.win.json`) en het pakket komen alleen uit de GitHub-releases van `gen-x-coder/QuietWriter`, via HTTPS;
- Velopack controleert de SHA-256 van het pakket tegen de feed voordat het iets toepast;
- bijwerken gebeurt alleen na een expliciete keuze van de gebruiker, en pas nadat QuietWriter normaal is afgesloten en alles heeft opgeslagen;
- alleen de programmamap wordt vervangen; boeken, instellingen en logs staan daarbuiten.

**Grens van dit model:** de echtheid van een update hangt af van de beveiliging van het GitHub-account en de releasepagina. Er is geen aparte publisher-handtekening. De eerder ontworpen eigen Ed25519-keten (1.5.0-dev) is niet in gebruik genomen; zie `documents/HISTORY_AND_LESSONS.md`. Als QuietWriter ooit een codesigning-certificaat krijgt, kan Velopack daarmee signeren (`vpk pack --signParams`).
