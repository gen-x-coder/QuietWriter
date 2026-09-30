# REVIEW_NOTES_0348 — Claude reviewronde 44

Doel: bevestig dat hoofdstukplanning na een update expliciete opt-in is en dat bestaand 0.34.7-gedrag verder gelijk blijft.

1. Volledige `current`-suite met echte PySide6; daarna `legacy` op de bekende basislijn.
2. Start met een schone QSettings zonder `ai_use_chapter_planning`:
   - boek openen met bruikbare hoofdstukplanning;
   - checkbox is actief maar **niet aangevinkt**;
   - rustige melding is zichtbaar en noemt dat externe providers gegevens buiten de computer ontvangen;
   - nep-provider: hoofdstukplanning staat niet in de systeemprompt.
3. Vink aan:
   - melding verdwijnt;
   - instelling wordt `True`;
   - exacte hoofdstukplanning staat onder `PLANNING VAN HET HUIDIGE HOOFDSTUK`;
   - herstart: checkbox blijft aan, melding blijft weg.
4. Zet uit:
   - instelling wordt `False`;
   - herstart: checkbox blijft uit, melding blijft weg;
   - handmatige `Planning-context…` blijft onafhankelijk werken.
5. Bestaande 0.34.7-instelling `True` vooraf zetten:
   - geen migratieprompt/notice;
   - checkbox blijft aan zoals voorheen.
6. Geen scènes / kapotte Planning / nieuwere Planning:
   - checkbox uitgeschakeld;
   - opgeslagen voorkeur niet gewijzigd;
   - AI-vraag gaat door zonder hoofdstukplanning;
   - na herstel komt de checkbox weer beschikbaar met dezelfde voorkeur.
7. Controleer dat er geen truncatie is toegevoegd: preview en prompt bevatten dezelfde volledige hoofdstukplanning als 0.34.7.

Visueel voor Lucas: alleen beoordelen of de nieuwe uitleg rustig genoeg is en duidelijk maakt dat deze nieuwe context standaard uit staat.
