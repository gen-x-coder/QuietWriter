# Changelog

## 0.5.0

- Windows/Qt-fontwaarschuwing defensief opgelost door een geldige applicatiefontgrootte te forceren.
- **Boek importeren** op de boekenplank: kies een Markdown-bestand via de bestandsbrowser; frontmatter wordt overgenomen en `# Hoofdstuktitel` wordt als hoofdstuk geïmporteerd.
- Nieuwe **Prullenbak** in het linkermenu. Verwijderen van een boek verplaatst het voortaan naar de prullenbak.
- In de prullenbak kunnen één of meer geselecteerde boeken worden hersteld of definitief verwijderd; de hele prullenbak kan ook in één keer worden geleegd.
- Boekomslag kan in Boekdetails worden verwijderd, waarna automatisch de standaardomslag wordt gebruikt.
- Boekenplank kan sorteren op laatst gebruikt, titel A–Z, titel Z–A en aantal woorden. Standaard is **Laatst gebruikt**.
- Openen en opslaan actualiseert de activiteit van een boek voor de standaardsortering.
- Dagarchief kijkt voortaan naar hoofdstukbestanden en blijft daardoor correct werken wanneer alleen metadata of laatste-open-tijd wordt bijgewerkt.

## 0.4.0

- Boekenplank toont echte omslagafbeeldingen in vaste verhouding 1:1,6; boektitel blijft dynamische tekst en maakt geen deel uit van de afbeelding.
- Nieuwe map `boekomslagen/`. Omslagen worden standaard gezocht op de slug van het boek.
- Ondersteuning voor `default-cover.jpg`, `default-cover.jpeg`, `default-cover.png` of `default-cover.webp` als standaardomslag; zonder bestand gebruikt QuietWriter een rustige ingebouwde fallback.
- Nieuwe knop **Details** op ieder boek en **Boekdetails** in de linkernavigatie zolang een boek geopend is.
- Boekdetails ondersteunt titel, slug, korte beschrijving, meta/SEO-beschrijving, intro boven het verhaal, tags, auteur en boekomslag.
- Boekomslagselectie valideert portretverhouding ongeveer 1:1,6 en minimaal 1024 pixels op de lange zijde.
- Boek verwijderen vanuit Boekdetails met expliciete waarschuwing.
- Instelling **Afbeeldingspad in metadata** met `{slug}` placeholder, standaard `/{slug}.jpg`; QuietWriter kent geen domeinnaam of website-adres.
- Zoekvelden op Boekenplank, Verhalen en manuscript hebben nu een ingebouwde wis-knop.
- Duidelijke melding wanneer een zoekopdracht geen resultaten oplevert.
- Boekenplank doorzoekt nu ook slug, beschrijvingen, tags en auteur in plaats van alleen de titel.
- Verhalenparser exposeert de bestaande velden `description`, `meta`, `intro`, `author` en afbeeldingsvelden consequenter.

## 0.3.0

- Nieuwe boekenplank als echt startscherm met boekkaarten, zoekveld en woordtelling.
- Linkernavigatie is contextgevoelig: Boekenplank sluit een geopend boek; Manuscript blijft beschikbaar zolang het boek geladen is.
- Hamburgerknop klapt de linkernavigatie uit en toont beschrijvende teksten; de stand wordt onthouden.
- Nieuwe Verhalen-weergave voor Markdown-bestanden in `stories/`.
- Verhalenmetadata (`title`, `description`, `synopsis`, `meta`, `intro`, `tags` en overige velden) wordt gelezen uit frontmatter.
- Top-level Markdownkoppen (`# Hoofdstuktitel`) worden in oude verhalen als hoofdstukken herkend.
- Verhalen kunnen op titel, tags en inhoud worden gezocht en als rustige leesweergave worden geopend.
- De editor heeft nu een sobere bovenbalk met undo/redo en de boektitel.
- Rechter gereedschapsbalk blijft alleen bij het manuscript zichtbaar en gebruikt grotere iconen.
- Meegeleverde, opgeschoonde `schrijver.md` op basis van de oude schrijfwijzer; vanuit Persona kan deze geladen worden.
