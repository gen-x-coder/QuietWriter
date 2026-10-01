# Tussentijds rapport 0.35.0

0.35.0 start de route naar 1.0 zonder nieuwe productfeatures.

## Uitgevoerd

- Definitieve logo-assets opgenomen in de package.
- Multi-size `.ico` ingesteld als applicatie- en hoofdvenstericoon.
- Windows AppUserModelID toegevoegd zodat de taakbalk QuietWriter als eigen app groepeert.
- Woordmerk toegevoegd aan splash en Over, thema-afhankelijk gerenderd.
- Crashlog verhuisd van de gebruikerswerkmap naar lokale appdata per computer.
- Qt `qWarning`/`qCritical`/andere Qt-berichten worden naar hetzelfde log gespiegeld.
- Onverwerkte Python- en threadexceptions kunnen via een thread-safe Qt-bridge een niet-modale foutmelding tonen met `Logbestand openen`.
- CI-workflow toegevoegd voor Ubuntu + Windows met current/legacy en Qt-deelruns.
- First-run contract voor 0.36 vastgelegd.
- Vertaalnulmeting vastgelegd: 74 gebruikte `tr()`-sleutels ontbreken nog expliciet in de locale-bestanden; de daadwerkelijke herstelpass volgt in 0.35.x.
- `PLAN_1_0.md` toegevoegd als release-afbakening.

## Bewuste keuze in fouttekst

De melding zegt niet `Je werk is opgeslagen`, omdat een onverwachte exception dat niet altijd kan garanderen. De gebruiker krijgt daarom de feitelijk veilige tekst dat de fout is gelogd en dat de laatste wijziging gecontroleerd moet worden.

## Lokaal getest

- `python -m compileall -q quietwriter tests`: groen.
- bron-/metadata-/brandingtests: groen.
- Echte PySide6 runtime is in deze omgeving niet beschikbaar en staat daarom expliciet als verplichte Claude-run in `REVIEW_NOTES_0350.md`.
