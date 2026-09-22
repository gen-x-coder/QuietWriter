# Changelog

## 0.14.0 — Veilige externe wijzigingen
- Nieuwe optimistic-concurrencylaag in `quietwriter/revisions.py`; geen lockfiles, sessieprotocol of Dropbox-specifieke code.
- Elk geopend boek krijgt in-memory revisions van `book.json` en alle hoofdstukbestanden op basis van bestandsgrootte + SHA-256. `mtime` wordt alleen diagnostisch bewaard en beslist nooit over een conflict.
- Vlak vóór iedere bewaakte schrijfactie controleert de storage-laag de volledige bekende boekstaat. Een externe wijziging wordt nooit stilletjes overschreven.
- Extern toegevoegde/verwijderde hoofdstukbestanden worden eveneens als wijziging gedetecteerd.
- Tijdelijke lees-/sync-locks zijn een aparte verificatiefout; autosave bewaart de tekst in geheugen en probeert later opnieuw in plaats van dit als inhoudsconflict te behandelen.
- Bij een echt conflict pauzeert autosave en kiest de gebruiker tussen **Mijn versie gebruiken** en **Versie op schijf gebruiken**.
- Beide conflictkeuzes maken vooraf automatisch een versie in de bestaande versiegeschiedenis (`conflict_external` of `conflict_local`).
- **Mijn versie gebruiken** laadt eerst de actuele schijfversie en legt alleen het huidige in-memory hoofdstuk daaroverheen, zodat andere externe wijzigingen behouden blijven.
- **Versie op schijf gebruiken** bewaart de lokale in-memory staat eerst als herstelversie en laadt daarna opnieuw van schijf.
- Structurele schrijfacties (manifest, hoofdstukken, secties, verplaatsen, verwijderen en herstel) gebruiken dezelfde revision-guard.
- Nieuwe regressietests voor happy path, externe hoofdstuk-/manifestwijzigingen, identieke inhoud met andere mtime, extern toegevoegde bestanden, pre-mutation guards en lokale recovery snapshots.


## 0.13.5
- Venstergeometrie wordt nu als expliciete normale `QRect` opgeslagen in plaats van via Qt's opaque `saveGeometry()`-blob.
- Opstarten op een andere computer, monitor, resolutie of DPI valideert en begrenst de opgeslagen positie en afmetingen vóór het native Windows-venster wordt aangepast.
- Een venster dat buiten alle huidige schermen valt, verhuist veilig naar het primaire scherm.
- Gemaximaliseerde status wordt los van de normale venstergeometrie bewaard.
- De oude `geometry`-instelling wordt bewust niet meer hersteld; daarmee kan een ongeldige oude geometry geen Windows `setGeometry`-waarschuwing meer veroorzaken.

## 0.13.4 — Opmaakstabiliteit en Windows font-rendering
- Scènebreuken (`***`) zijn nu beschermd tegen alle inline- en blokopmaakacties.
- Andere inline stijlen worden nooit meer in een backtick-codespan geïnjecteerd; code blijft letterlijk en ongewijzigd.
- De gedeelde `is_scene_break_line()`-helper voorkomt dat editorweergave en Markdowntransformaties verschillende definities gebruiken.
- Dode/verwarrende triple-star-parserlogica is vereenvoudigd.
- De verborgen-markertekst gebruikt niet langer een extreem 0,1-punts font of `fontStretch(1)`. Dit vermijdt een waarschijnlijke DirectWrite-trigger achter `QWindowsFontEngineDirectWrite::addGlyphsToPath: GetGlyphRunOutline failed` op Windows.
- Nieuwe gedrags-tests voor scene-break-integriteit, code-span-bescherming, multi-line style state, toolbar-state, undo en Qt runtime-opmaak.

## 0.13.3 — Samengestelde opmaak en toolbar-status
- Inline opmaak wordt nu samengesteld in plaats van elkaar te overschrijven: vet, cursief, onderstrepen, doorhalen en code kunnen betrouwbaar gecombineerd worden.
- De selectie-toolbar toont actief welke stijlen op de volledige selectie van toepassing zijn.
- Een gemengde selectie (bijvoorbeeld enkele cursieve woorden in gewone tekst) kan met één klik volledig cursief worden gemaakt en met een tweede klik volledig naar normaal worden teruggezet.
- Markdown-markeringen worden semantisch genormaliseerd bij toggelen, zodat combinaties zoals vet+cursief geen zichtbare of kapotte markers achterlaten.
- Nieuwe regressietests voor gecombineerde stijlen en gemengde selecties.


## 0.13.2
- Schrijfopmaak opnieuw opgebouwd als echte presentatie-laag boven platte Markdown.
- Markdownmarkeringen voor vet, cursief, onderstrepen, doorhalen, code, koppen, citaten en lijsten worden visueel ingeklapt in plaats van als witte tekens met normale breedte weergegeven.
- Dezelfde highlighter combineert manuscriptopmaak en spellingsonderstreping zodat beide stijlen elkaar niet overschrijven.
- Opsommingen, nummering en citaten krijgen een eigen visuele marker terwijl de Markdownbron intact blijft.
- Opmaaktoolbar heeft circa dubbel zo grote bedieningselementen en duidelijkere typografische iconen.

## 0.13.1 — PySide6 compatibiliteit

- Opgelost: startup-crash op sommige PySide6 6.x-versies bij `QTextBlockFormat.setLineHeight()`.
- De line-height modus wordt nu expliciet genormaliseerd naar de onderliggende integerwaarde en de hoogte naar `float`, conform de bindingsignature op oudere én nieuwere PySide6-versies.
- Geen functionele of visuele wijzigingen aan de manuscriptstijl.

## 0.13.0 — Schrijfopmaak en manuscriptstijl

- Nieuwe selectie-toolbar die na één seconde verschijnt bij geselecteerde tekst.
- Opmaakacties: normale alinea, tussenkop, opsomming, genummerde lijst, citaat, code, vet, cursief, onderstrepen en doorhalen.
- Opmaak blijft opgeslagen als leesbare Markdown/HTML-markup; de editor blijft een plain-text bron bewaren.
- Markdownmarkeringen worden in de schrijfruimte subtiel verborgen terwijl de opmaak visueel wordt weergegeven.
- Sneltoetsen voor vet (Ctrl+B), cursief (Ctrl+I), onderstrepen (Ctrl+U) en doorhalen (Ctrl+Shift+S).
- `***` blijft de bron voor scènebreuken, maar wordt visueel weergegeven als een rustige horizontale divider met drie punten.
- Manuscriptalinea's krijgen automatische eerste-regel-inspringing voor opeenvolgende alinea's; de eerste alinea, tekst na een lege regel, tussenkop, citaat of scènebreuk begint links.
- Nieuwe onafhankelijke manuscriptinstellingen: regelafstand, inspringing, ruimte na alinea en slimme typografische aanhalingstekens.
- Rechte dubbele quotes die tijdens typen worden ingevoerd kunnen automatisch als “slimme” quotes worden geplaatst.
- Opmaak- en manuscriptlogica is modulair opgesplitst in `manuscript_markup.py`, `manuscript_editor.py` en `selection_toolbar.py`.
- Extra regressietests voor Markdown-opmaak, lijsten, tussenkoppen, quotes en UI-architectuur.

## 0.12.1

Zie eerdere release voor de technische UI-refactor en reviewfixes.
