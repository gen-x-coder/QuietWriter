# QuietWriter 1.2.29 — Markdown via het neutrale documentmodel

Deze ontwikkelversie rondt de Markdown-kant van de nieuwe documentarchitectuur af. Externe Markdown wordt niet meer rechtstreeks als QuietWriter-bron opgeslagen, maar eerst als neutrale documentsemantiek gelezen en daarna centraal geserialiseerd.

## Belangrijkste wijzigingen

- Markdown-import gebruikt `ImportDocument` en dezelfde serializergrens als DOCX.
- Import is transactioneel: geen half geïmporteerde boeken bij een fout.
- Gewrapte Markdownproza wordt volgens normale Markdownregels één alinea.
- Markdown hard breaks worden QuietWriter soft breaks.
- Publieke Markdown-export zet tussen QuietWriter-alinea's lege regels, zodat CommonMark-renderers ze niet samenvoegen.
- Soft breaks worden correct als Markdown hard break geëxporteerd.

Er verandert niets stil aan bestaande QuietWriter-boeken.
