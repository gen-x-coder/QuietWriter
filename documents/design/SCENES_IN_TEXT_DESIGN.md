# Scènes in de tekst (1.7)

**Status:** gebouwd in 1.7.0.
**Besluit:** de *n*-de planningscène van een hoofdstuk hoort bij het *n*-de stuk tekst tussen scènebreuken (`***`). Er komt **geen scène-ID in het manuscript** en er is **geen nieuwe syntax**.

## Probleem

Planning en tekst stonden naast elkaar. QuietWriter wist niet welke geplande scène bij welk stuk tekst hoort. Daardoor kon het niet:
- tijdens het schrijven laten zien welke scène je nu schrijft;
- de volgende geplande scène tonen nadat je een scènebreuk zet;
- vanuit "In dit hoofdstuk" naar een scène springen;
- stukken tekst zonder planningscène laten zien (omgekeerd plannen, NEO #148).

## Overwogen

| Optie | Voor | Tegen |
|---|---|---|
| **A. Verborgen ID op de scènebreuk** (`*** <!--qw:scene:…-->`), zoals NEO's `data-sec-id` | Koppeling overleeft verplaatsen en invoegen | Nieuwe syntax in elk hoofdstukbestand. Elke lezer moet de markers negeren: zoeken, spelling, telling, AI, export, DOCX en kopiëren/plakken. Oudere QuietWriter-versies tonen de markers als tekst. NEO-issue #3 (vreemde tekens door een verborgen bladwijzer) laat het risico zien. |
| **B. Anker in Planning** (eerste woorden van het segment) | Manuscript blijft schoon | Planning moet bij elke tekstwijziging opnieuw ankeren of bijwerken: stille schrijfacties in `outline.json` en meer synchronisatieconflicten. Bij herschrijven gaat het fuzzy matchen mis. |
| **C. Volgorde** (scène *n* = segment *n*) | Niets nieuws op schijf. Werkt meteen voor bestaande boeken. Past bij "geen tweede, onafhankelijke hoofdstukvolgorde" (roadmap §9). | Voeg je midden in een hoofdstuk een scène toe, dan schuift de koppeling op totdat je in Planning dezelfde volgorde aanhoudt. |

**Gekozen: C.** Het is eenvoudig, er hoeft niets gemigreerd te worden en het manuscript blijft platte tekst. De zwakte is zichtbaar en makkelijk te herstellen: Outline nummert de scènes per hoofdstuk ("1. Aankomst"), en met **Scène omhoog/omlaag** zet je de volgorde gelijk met de tekst. Blijkt dit in de praktijk niet genoeg, dan kan B er later bij zonder dat er iets aan bestaande boeken verandert.

## Gedrag

Alles is **presentatie of een bewuste actie**. QuietWriter schrijft nooit zelf naar het manuscript, en naar Planning alleen als je op een knop drukt.

- **Regel onder de tekst** (`ManuscriptEditor.scene_hint`, in de ondermarge, buiten het document): "Scène 2 in Planning: Afscheid — Bram vertrekt…". Deze regel volgt de cursor en verschijnt alleen als er bij dat stuk tekst een geplande scène hoort.
- **Volgende in Planning:** eindigt het hoofdstuk op een scènebreuk (met hooguit lege regels erna), dan tekent de editor daaronder de nog niet geschreven scènes. Dat werkt net als de spookalinea's in een leeg hoofdstuk: geschilderd, niet in `QTextDocument`. Zodra je typt, verdwijnen ze. Is er onderaan geen ruimte, dan noemt de regel onder de tekst de volgende scène.
- **In dit hoofdstuk:**
  - scènes worden genummerd;
  - "● Hier schrijf je nu" staat bij de scène waar de cursor is;
  - **Ga naar deze scène** zet de cursor aan het begin van het stuk;
  - bij een scène zonder tekst staat de uitleg "zet een scènebreuk (***)".
- **Niet in Planning:**
  - stukken tekst na de laatste geplande scène staan in het paneel en in Outline, met de eerste woorden;
  - **Toevoegen aan Planning** maakt er planningscènes van, met status *Geschreven* en de eerste woorden als titel;
  - de nieuwe scènes komen direct na de bestaande scènes van dat hoofdstuk, zodat de volgorde gelijk blijft.
- **Instelling:** "Planninghulp in editor: Verbergen" zet de regel onder de tekst en de spookhulp allebei uit.

## Wat zoeken, spelling, telling, export en AI zien

Niets nieuws. De scènehulp staat niet in het document en niet in de bron. Ook Ongedaan maken ziet haar niet.

## Code

- `quietwriter/scene_segments.py`: puur: `chapter_segments`, `map_scenes`, `scenes_for_chapter`.
- `quietwriter/ui/manuscript_editor.py`: `set_planning_scenes`, `segment_at_cursor`, `go_to_segment`, `_tail_ghost_scenes`, `set_scene_hint`.
- `quietwriter/ui/editor_page.py`: `_scene_position_changed` (250 ms uitgesteld), `_jump_to_segment`, `_add_unplanned_scenes`.
- `quietwriter/ui/chapter_context_panel.py` en `quietwriter/ui/planning/outline_page.py`.
- Tests: `tests/current/test_story_170.py`.

## Personages herkennen (zelfde release)

`quietwriter/character_mentions.py` herkent een personage aan de volledige naam, de voornaam (vanaf drie letters, met hoofdletter) en de namen in het nieuwe veld **Ook bekend als**. Herkenning is hoofdlettergevoelig en werkt alleen op hele woorden. "In dit hoofdstuk" toont per personage het aantal keren en "voor het eerst" als het personage in geen eerder hoofdstuk voorkomt. Er wordt niet hernoemd en niet gemarkeerd.

Een naam die bij meer dan één personage hoort, telt voor niemand. Een zelf opgegeven naam wint van een automatische voornaam van een ander personage (`unambiguous_terms`). Een ontbrekend of onleesbaar eerder hoofdstuk maakt "voor het eerst" onbekend in plaats van waar. "Toevoegen aan Planning" is één gedeelde actie (`PlanningPage.add_unplanned_scenes`) die Planning eerst opnieuw van schijf leest. (Review ChatGPT 1.7.0.)

Het veld `aliases` is een nieuw veld in `characters.json`. Daarnaast bewaren `Character` en `Scene` voortaan **onbekende velden** van een nieuwere versie en schrijven ze ongewijzigd terug (`extra`). QuietWriter 1.6 en ouder kennen dat nog niet: wie na 1.7 met zo'n oudere versie een personage opslaat, verliest de bijnamen.
