# Reviewoverdracht QuietWriter 1.4.0-dev.37

Bron: Claude's `QUIETWRITER_REVIEW_1_4_0_DEV36_CLAUDE.md`.

## Belangrijkste verificaties

- N1: `vrow36.py` opnieuw uitvoeren; één geregistreerde, incomplete versie mag nooit alle andere versies verbergen. Herstel van onvolledige versies moet worden geweigerd.
- N2: `aichat36.py` opnieuw uitvoeren; een pakket zonder AI-chat bewaart lokale `.quietwriter/ai_chat.json` maar herstelt `ai/boekprofiel.md` uit de back-up.
- K1: `partialleft36.py` en back-upkern controleren; verborgen `.partial`-archieven mogen nooit in de back-up komen. Het automatisch opruimen van verweesde partials is nog niet geïmplementeerd.
- K3: `spexit36.py` met echte PySide6 controleren, met meerdere lopende suggesties en afsluiten. `RuntimeError` bij late signalen is afgevangen.
- K5: geblokkeerde boeken mogen geen misleidende back-upmapfout tonen.

## Bekende beperkingen en vervolg

Echte Windows, OneDrive/Dropbox, tests met stroomuitval en 2GB-grenzen zijn niet uitgevoerd. Volledige Qt-suite moet door Claude worden gedraaid. Openstaande kleine punten blijven in de onafhankelijke review staan.
