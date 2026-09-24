from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonaSection:
    key: str
    title: str
    help: str


SECTIONS = (
    PersonaSection('voice_tone', 'Stem & toon', 'Hoe moet de tekst voelen? Denk aan directheid, warmte, afstand, humor, donkerte of sensualiteit.'),
    PersonaSection('narration', 'Vertelstijl', 'Perspectief, verteltijd, vertelafstand en hoeveel de verteller uitlegt of juist laat zien.'),
    PersonaSection('language', 'Taal & woordkeuze', 'Woordenschat, concreet of abstract taalgebruik, jargon, explicietheid en terugkerende voorkeuren.'),
    PersonaSection('rhythm', 'Zinnen & ritme', 'Zinslengte, cadans, afwisseling, fragmenten, alinearitme en tempo.'),
    PersonaSection('description', 'Beschrijving & zintuigen', 'Hoeveel detail je gebruikt voor omgeving, uiterlijk, lichaam, geluid, geur, aanraking en andere zintuigen.'),
    PersonaSection('dialogue', 'Dialoog & interactie', 'Hoe personages spreken, hoeveel subtekst je gebruikt en hoe dialoog, handeling en gedachten elkaar afwisselen.'),
    PersonaSection('emotion_intimacy', 'Emotie, spanning & intimiteit', 'Hoe expliciet of impliciet je emotie, conflict, romantiek, lichamelijkheid, intimiteit en geweld behandelt.'),
    PersonaSection('scenes_pacing', 'Scènes & verteltempo', 'Hoe scènes beginnen en eindigen, informatie wordt gedoseerd en spanning, rust en overgangen worden opgebouwd.'),
    PersonaSection('editorial', 'Redactionele voorkeuren', 'Waar AI op moet letten bij feedback of herschrijven en welke ingrepen het juist niet automatisch moet doen.'),
    PersonaSection('avoid', 'Vermijden', 'Clichés, woorden, formuleringen, verteltrucs en AI-gewoonten die niet bij jouw stijl passen.'),
    PersonaSection('examples', 'Voorbeeldteksten', 'Korte eigen fragmenten of beschrijvingen van passages die jouw gewenste stijl goed vertegenwoordigen.'),
    PersonaSection('additional', 'Aanvullende instructies', 'Vrije instructies die niet goed in de andere onderdelen passen. Oude vrije persona-inhoud wordt hier zonder verlies bewaard.'),
)

_SECTION_BY_TITLE = {s.title.casefold(): s for s in SECTIONS}


def empty_profile() -> dict[str, str]:
    return {section.key: '' for section in SECTIONS}


def parse_persona(markdown: str) -> dict[str, str]:
    """Parse the human-readable persona Markdown without losing legacy content."""
    source = (markdown or '').replace('\r\n', '\n').replace('\r', '\n')
    profile = empty_profile()
    lines = source.split('\n')
    found_known = False
    preamble: list[str] = []
    unknown: list[str] = []
    current_key: str | None = None
    current_title: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_title, current_lines, found_known
        if current_title is None:
            return
        body = '\n'.join(current_lines).strip()
        if current_key is not None:
            found_known = True
            profile[current_key] = body
        else:
            block = f'## {current_title}'
            if body:
                block += f'\n\n{body}'
            unknown.append(block)
        current_key = None
        current_title = None
        current_lines = []

    for line in lines:
        if line.startswith('## '):
            flush()
            title = line[3:].strip()
            section = _SECTION_BY_TITLE.get(title.casefold())
            current_key = section.key if section else None
            current_title = title
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)
        else:
            # Ignore only our canonical H1. Everything else is user content.
            if line.strip().casefold() not in {'# schrijverspersona', '# schrijversprofiel'}:
                preamble.append(line)
    flush()

    if not found_known:
        # A legacy free-form persona is preserved byte-for-content (apart from
        # newline normalization) in the catch-all field until the user saves.
        profile['additional'] = source.strip()
        return profile

    extras = []
    preamble_text = '\n'.join(preamble).strip()
    if preamble_text:
        extras.append(preamble_text)
    extras.extend(unknown)
    if extras:
        existing = profile['additional'].strip()
        combined = '\n\n'.join(extras)
        profile['additional'] = '\n\n'.join(p for p in (existing, combined) if p).strip()
    return profile


def render_persona(profile: dict[str, str]) -> str:
    parts = ['# Schrijverspersona']
    for section in SECTIONS:
        body = (profile.get(section.key) or '').strip()
        parts.append(f'## {section.title}\n\n{body}'.rstrip())
    return '\n\n'.join(parts).rstrip() + '\n'


def default_persona_markdown() -> str:
    profile = empty_profile()
    profile['additional'] = 'Beschrijf hier jouw schrijfstijl, of laad in QuietWriter een voorbeeldpersona als startpunt.'
    return render_persona(profile)


EXAMPLE_PERSONAS: dict[str, dict[str, object]] = {
    'austen': {
        'name': 'Jane Austen',
        'subtitle': 'Sociale observatie · ironie · scherpe dialoog',
        'description': 'Een startprofiel geïnspireerd op brede kenmerken die vaak met Austens proza worden geassocieerd.',
        'values': {
            'voice_tone': 'Elegant, beheerst en licht ironisch. Humor ontstaat vooral uit sociale observatie en het verschil tussen wat personages zeggen, bedoelen en van zichzelf geloven.',
            'narration': 'Dicht bij de personages, maar met genoeg vertelafstand om hun zelfbeeld subtiel te relativeren. Laat oordeel vaak ontstaan uit observatie in plaats van expliciete uitleg.',
            'language': 'Precies en helder. Formeel wanneer de sociale context dat vraagt, maar vermijd opgeblazen formuleringen. Kies woorden die karakter en klasse impliciet zichtbaar maken.',
            'rhythm': 'Overwegend vloeiende volzinnen met afwisseling tussen beschouwing en levendige dialoog. Gebruik korte zinnen spaarzaam voor nadruk of komische timing.',
            'description': 'Selectief. Beschrijf vooral details die iets zeggen over status, smaak, gedrag of onderlinge verhoudingen; geen uitgebreide decorbeschrijving zonder functie.',
            'dialogue': 'Dialoog draagt sociale spanning. Personages zeggen zelden alles rechtstreeks. Gebruik beleefdheid, omwegen en kleine woordkeuzes om machtsverschillen en gevoelens zichtbaar te maken.',
            'emotion_intimacy': 'Emoties zijn duidelijk aanwezig maar meestal beheerst en indirect. Romantiek groeit uit gedrag, misverstanden, observatie en keuzes; intimiteit hoeft niet expliciet te worden beschreven.',
            'scenes_pacing': 'Laat scènes draaien om ontmoetingen, keuzes, informatie en veranderende onderlinge verhoudingen. Bouw spanning via verwachtingen en sociale consequenties.',
            'editorial': 'Bewaak ironie en subtekst. Leg niet uit wat een scène al laat zien. Geef feedback op sociale logica, karakterconsistentie en dialoog die te letterlijk wordt.',
            'avoid': 'Vermijd melodrama, uitleggerige moraal, moderne spreektaal zonder reden en alwetende toelichtingen die de ironie wegnemen.',
            'examples': '',
            'additional': 'Dit is een bewerkbaar voorbeeldprofiel, geen opdracht om een auteur letterlijk te imiteren. Pas het aan tot het jouw eigen stem ondersteunt.',
        },
    },
    'doyle': {
        'name': 'Arthur Conan Doyle',
        'subtitle': 'Observatie · mysterie · heldere voortgang',
        'description': 'Een startprofiel voor helder, plotgedreven proza met sterke observatie en gecontroleerde informatie.',
        'values': {
            'voice_tone': 'Helder, zelfverzekerd en nieuwsgierig. De tekst nodigt de lezer uit om mee te kijken en mee te redeneren zonder alle antwoorden vooraf weg te geven.',
            'narration': 'Werk bij voorkeur vanuit een waarnemer die niet alles weet. Laat cruciale informatie zichtbaar zijn, maar geef betekenis en verbanden gedoseerd prijs.',
            'language': 'Concreet en precies. Gebruik specifieke voorwerpen, gedragingen en omstandigheden in plaats van vage kwalificaties. Technische termen alleen wanneer ze werkelijk helpen.',
            'rhythm': 'Functioneel ritme: rustige observatie wordt afgewisseld met korte versnellingen bij ontdekkingen, confrontaties en gevaar.',
            'description': 'Details hebben een doel. Beschrijf kenmerken die sfeer, karakter of bewijs leveren. Laat opvallende kleine feiten later betekenis kunnen krijgen.',
            'dialogue': 'Dialoog brengt informatie, conflict of redenering vooruit. Geef personages herkenbare manieren van spreken, maar vermijd lange infodumps die onnatuurlijk klinken.',
            'emotion_intimacy': 'Emotie blijft meestal onder controle en wordt zichtbaar via reacties, loyaliteit, nervositeit en keuzes. Spanning komt eerder uit onzekerheid en dreiging dan uit overdrijving.',
            'scenes_pacing': 'Iedere scène moet een vraag openen, informatie toevoegen of de situatie veranderen. Wissel onderzoek, reconstructie en actie af en bewaar belangrijke verklaringen tot ze verdiend zijn.',
            'editorial': 'Controleer causaliteit en eerlijkheid van aanwijzingen. Signaleer toevallige oplossingen, informatie die te laat wordt geïntroduceerd en observaties zonder functie.',
            'avoid': 'Vermijd mysterie door informatie kunstmatig achter te houden die de verteller logisch gezien al zou noemen. Vermijd ook decoratieve details die op een aanwijzing lijken maar nergens toe dienen.',
            'examples': '',
            'additional': 'Dit is een bewerkbaar voorbeeldprofiel op basis van algemene vertelkenmerken, bedoeld als vertrekpunt voor een eigen stijl.',
        },
    },
    'woolf': {
        'name': 'Virginia Woolf',
        'subtitle': 'Innerlijke waarneming · associatie · ritme',
        'description': 'Een startprofiel voor introspectief proza waarin waarneming, herinnering en gedachten soepel in elkaar overlopen.',
        'values': {
            'voice_tone': 'Intiem, aandachtig en gevoelig voor kleine verschuivingen in stemming en waarneming. De toon mag tegelijk helder en dromerig zijn.',
            'narration': 'Beweeg dicht langs gedachten en zintuiglijke indrukken. Overgangen tussen buitenwereld, herinnering en innerlijke reactie mogen associatief verlopen zolang de lezer houvast houdt.',
            'language': 'Beeldend maar precies. Laat concrete waarnemingen abstracte gedachten oproepen. Herhaling van woorden of motieven mag ritmisch en betekenisvol zijn.',
            'rhythm': 'Varieer sterk in zinslengte. Lange meanderende zinnen mogen een gedachtebeweging volgen; korte zinnen markeren plotseling inzicht, verlies of fysieke werkelijkheid.',
            'description': 'Zintuiglijke details zijn vaak toegangspoorten tot herinnering of emotie. Beschrijf niet alleen wat iets is, maar ook wat de waarneming in het personage losmaakt.',
            'dialogue': 'Gesproken taal is één laag naast gedachten, stiltes en observaties. Het verschil tussen wat iemand zegt en innerlijk ervaart mag nadrukkelijk aanwezig zijn.',
            'emotion_intimacy': 'Emotie hoeft niet benoemd te worden wanneer ritme, associatie en zintuiglijke waarneming haar voelbaar maken. Intimiteit kan vooral in aandacht en innerlijke nabijheid liggen.',
            'scenes_pacing': 'Chronologische actie mag tijdelijk vertragen voor waarneming of herinnering. Houd wel een herkenbare fysieke of emotionele lijn die de passage bijeenhoudt.',
            'editorial': 'Bewaak dat associatieve passages betekenis en richting houden. Signaleer poëtische formuleringen die alleen versieren en geen waarneming, emotie of gedachte verdiepen.',
            'avoid': 'Vermijd uitleg achteraf van beelden die al werken, generieke lyriek en lange abstracte passages zonder concrete zintuiglijke verankering.',
            'examples': '',
            'additional': 'Dit voorbeeld is geïnspireerd op algemene modernistische kenmerken en is bedoeld om verder te personaliseren.',
        },
    },
}
