# QuietWriter vertalen

## Voor vertalers (geen technische kennis nodig)
1. Open **Instellingen → Vertalingen**.
2. Kies links een taal die je kent (standaard Engels). Kies rechts je eigen taal, of **Nieuwe taal…** en vul de naam en een code van twee letters in (`it`, `pt`, `pl`…).
3. Dubbelklik in de rechterkolom om een tekst te vertalen. Met *Alleen wat nog ontbreekt of een fout heeft* zie je wat er nog te doen is.
4. Woorden tussen accolades, zoals `{count}` of `{title}`, zijn **plekken**: daar zet QuietWriter later een getal of naam neer. Neem ze precies over, ook als ze in jouw taal op een andere plek in de zin staan. Een fout wordt rood.
5. **Vertaling opslaan** bewaart je werk in je werkmap (`translations/<code>.json`). Herstart QuietWriter en kies je taal bij **Algemeen → Programmataal**. Wat nog niet vertaald is, verschijnt in het Engels.
6. **Exporteren…** maakt één bestand, bijvoorbeeld `quietwriter-it.json`. Mail dat naar de maker. Met **Importeren…** laad je zo'n bestand weer in.

Verbeter je een meegeleverde taal (bijvoorbeeld Duits), dan bewaart QuietWriter alleen wat je veranderde. Latere verbeteringen in QuietWriter zelf komen dan gewoon door.

## Voor de maker
- Een ontvangen bestand opnemen: `python tools/merge_translation.py quietwriter-it.json`. Teksten met kapotte plekken worden overgeslagen en gemeld.
- Een nieuwe taal meeleveren: daarna de code toevoegen aan `i18n.BUILTIN_CODES`, `tools/check_locales.py` (CODES) en de taallijst in Instellingen (Algemeen). Draai `python tools/check_locales.py`.
- Meervoudsvormen kent QuietWriter nog niet: teksten gebruiken "scène(s)". Dat is bewust eenvoudig gehouden.
