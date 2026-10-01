# Tussentijds rapport 0.34.8

## Wijziging
- Nieuwe hoofdstukplanning is nu expliciete opt-in voor gebruikers die de instelling nog niet hebben.
- Default van `ai_use_chapter_planning` is `False` bij ontbrekende instelling.
- Het AI-contextpaneel toont dan een rustige toelichting; bij eerste bewuste toggle verdwijnt die toelichting.
- Bestaande expliciete `True`/`False`-keuzes blijven onaangeroerd.
- Geen lengtegrens of truncatie toegevoegd.

## Tests lokaal
- current: 185 passed, 13 skipped.
- legacy (zonder bekende fontresource-test): 422 passed, 24 skipped, 280 subtests passed.
