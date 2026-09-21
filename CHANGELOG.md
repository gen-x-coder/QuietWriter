# Changelog

## 0.9.0

- Markdown import/export is nu een eigen module en ondersteunt een volledige round-trip.
- Import leest frontmatter, bewaart onbekende metadata en maakt van `# Titel` afzonderlijke hoofdstukken.
- Een Markdown-bestand zonder hoofdstukkoppen wordt als één hoofdstuk geïmporteerd.
- QuietWriter-secties worden bij export als onzichtbare HTML-comments bewaard en bij herimport hersteld.
- Export schrijft titel, slug, descriptions, intro, tags, auteur, image-pad en overige metadata terug naar frontmatter.
- Export is beschikbaar via Boekdetails en vraagt om bevestiging bij overschrijven.
- Nieuw + pictogram in de rechter werkbalk met de actie `Scènebreuk`.
- Scènebreuk voegt `***` op een eigen regel tussen tekstblokken in.
- Sneltoets voor scènebreuk: Ctrl+Shift+Enter.
- Nieuwe regressietests voor Markdown round-trip en scènebreuken.
