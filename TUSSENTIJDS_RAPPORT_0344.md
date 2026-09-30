# Tussentijds rapport 0.34.4

0.34.4 is een transparantieslice. De opgeslagen Planning van het actieve hoofdstuk wordt in het AI-contextblok samengevat en in `Context bekijken` exact als preview getoond. Deze tekst wordt nog niet automatisch naar de provider gestuurd.

Technisch is de foutstatus van gerichte Planning-context losgemaakt van zichtbare Nederlandse labels. Planning met UTF-8-BOM wordt via `utf-8-sig` gelezen, zodat een nieuwere Planning-versie ook met BOM correct als toekomstig formaat wordt herkend.

Lokale tests: `tests/current` 175 geslaagd, 11 overgeslagen. Legacy zonder de twee bekende fontresources: 422 geslaagd, 24 overgeslagen, 280 subtests geslaagd.
