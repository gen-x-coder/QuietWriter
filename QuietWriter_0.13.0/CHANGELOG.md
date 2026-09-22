# Changelog

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
