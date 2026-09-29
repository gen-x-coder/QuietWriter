# Tussentijds rapport 0.29.4

## Doel

0.29.4 sluit reviewronde 17 af zonder de scope van Integriteit & Herstel uit te breiden.

## Wijzigingen

### Publicatie versus hoofdstukcorruptie
`_chapter_corrupt` is uitsluitend een manuscriptstatus. `_set_publication_context()` wist de vlag en `save()` behandelt PublicationEditor/PublicationSetup vóór de hoofdstukguard. Daardoor kan een eerder bekeken beschadigd hoofdstuk een save van Voorwerk of Achterwerk niet meer stil overslaan. `close_book()` wist de vlag eveneens.

### Zoeken en vervangen
`collect_search_matches()` vangt `UnicodeDecodeError` per niet-actief hoofdstuk af, slaat alleen dat hoofdstuk over en meldt het aantal. `replace_all_matches()` doet hetzelfde tijdens de write-pass. Het corrupte bestand wordt nooit aangeraakt.

### Dupliceren
`Library.duplicate_chapter()` gebruikt nu dezelfde UTF-8-broncontrole als normale writes. Een corrupt bronhoofdstuk geeft `CorruptSourceError`; de UI vertaalt dit naar een herstelmelding.

## Bewuste grens
De transactionele/all-or-nothing herbouw van `adopt_active_book()` blijft voor 0.30.0. Deze patch verandert die architectuur niet.

## Volgende stap na groen runtimeonderzoek
0.30.0 Editor polish: eerst transactionele adoptie, daarna autosave altijd aan/instelling verwijderen, woordtelling verduidelijken en samen met Claude het spellingsontwerp onderzoeken vóór implementatie.
