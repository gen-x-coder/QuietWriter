# Release-integriteit (zonder SignPath)

QuietWriter gebruikt **geen Authenticode-/SignPath-dienst** in de actieve distributieketen.
Windows kan daardoor waarschuwingen over onbekende uitgevers tonen.

Voor toekomstige in-app-updates gebruiken we een offline beheerde Ed25519-
releasehandtekening plus SHA-256-controles van de exacte ZIP en bestanden.
De openbare sleutel moet vastgezet worden in een gereviewde release; de
privésleutel mag nooit in broncode, CI of distributie-ZIP terechtkomen.

**Status dev.32-review:** er is nog geen productiesleutel. Automatische installatie
is uitgeschakeld, ook bij een proefmarker. Releases via GitHub blijven handmatig.
Een lokaal inventarisbestand bewijst nooit op zichzelf de herkomst van software.
