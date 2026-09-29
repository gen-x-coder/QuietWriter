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


def _escape_section_body(text: str) -> str:
    """Escape every field line whose visible text could look like a section header."""
    lines = str(text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return '\n'.join(
        ('\\' + line) if line.lstrip('\\').startswith('## ') else line
        for line in lines
    )


def _unescape_section_line(line: str) -> str:
    # Rendering adds exactly one protective backslash, even when the user's
    # literal line already began with one or more backslashes. Remove exactly
    # that one so render -> parse is lossless for ##, \##, \\##, ...
    return line[1:] if line.startswith('\\') and line[1:].lstrip('\\').startswith('## ') else line


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
        if line.startswith('\\') and line.lstrip('\\').startswith('## '):
            if current_title is not None:
                current_lines.append(_unescape_section_line(line))
            else:
                preamble.append(_unescape_section_line(line))
            continue
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
        body = _escape_section_body((profile.get(section.key) or '').strip())
        parts.append(f'## {section.title}\n\n{body}'.rstrip())
    return '\n\n'.join(parts).rstrip() + '\n'


def default_persona_markdown() -> str:
    profile = empty_profile()
    profile['additional'] = 'Beschrijf hier jouw schrijfstijl, of laad in QuietWriter een voorbeeldpersona als startpunt.'
    return render_persona(profile)


EXAMPLE_PERSONAS: dict[str, dict[str, object]] = {
    'van_gastel': {
        'name': 'Chantal van Gastel',
        'subtitle': 'Feelgood · romantiek · herkenbare humor',
        'description': 'Een bewerkbaar feelgood/chicklit-profiel, geïnspireerd op brede genrekenmerken die passen bij het werk waarmee Chantal van Gastel bekend is.',
        'values': {
            'voice_tone': 'Warm, toegankelijk en lichtvoetig, met ruimte voor zelfspot. Emotionele momenten mogen oprecht zijn zonder dat de tekst zwaar of afstandelijk wordt.',
            'narration': 'Blijf dicht bij de hoofdpersoon en haar directe beleving. Laat verwachtingen, twijfel en romantische spanning vooral ontstaan uit wat zij ziet, denkt en verkeerd interpreteert.',
            'language': 'Modern, helder en spreektaalnabij zonder slordig te worden. Kies concrete woorden en herkenbare observaties boven formele of zeer literaire formuleringen.',
            'rhythm': 'Vlot en afwisselend. Gebruik compacte alinea’s en dialoog om tempo te houden; vertraag bewust bij emotionele omslagpunten en romantische spanning.',
            'description': 'Beschrijf selectief en herkenbaar. Details over kleding, plekken, werk en dagelijkse routines mogen karakter en sfeer ondersteunen, maar nooit de scène stilzetten.',
            'dialogue': 'Levendig, natuurlijk en vaak humoristisch. Laat aantrekkingskracht, irritatie en onzekerheid ook via subtekst en timing werken, niet alleen via uitgesproken gevoelens.',
            'emotion_intimacy': 'Emotie en romantiek staan duidelijk in beeld. Bouw intimiteit op vanuit vertrouwen, spanning en kwetsbaarheid; explicietheid mag per verhaal verschillen en moet altijd bij personages en toon passen.',
            'scenes_pacing': 'Scènes moeten iets veranderen in relatie, verwachting of zelfbeeld. Wissel romantische ontwikkeling af met werk, vriendschap, familie en praktische problemen zodat het verhaal breder blijft dan alleen de liefdeslijn.',
            'editorial': 'Bewaak geloofwaardige chemie, herkenbare motivatie en een goede balans tussen humor en emotionele ernst. Signaleer misverstanden die alleen bestaan omdat personages onnatuurlijk informatie achterhouden.',
            'avoid': 'Vermijd geforceerde quirky formuleringen, permanente zelfspot, clichés zonder eigen draai en romantische oplossingen die niet uit eerdere keuzes of groei voortkomen.',
            'examples': '',
            'additional': 'Dit profiel gebruikt alleen algemene feelgood- en vertelkenmerken als vertrekpunt. Maak het nadrukkelijk je eigen stem en kopieer geen bestaande tekst of herkenbare formuleringen van een auteur.',
        },
    },
    'noort': {
        'name': 'Saskia Noort',
        'subtitle': 'Thriller · psychologische spanning · hedendaagse relaties',
        'description': 'Een bewerkbaar thrillerprofiel met psychologische druk, herkenbare personages en een eigentijdse setting.',
        'values': {
            'voice_tone': 'Direct, scherp en onrustig wanneer de spanning stijgt. De wereld voelt herkenbaar en dichtbij, waardoor dreiging juist in alledaagse situaties kan binnenkomen.',
            'narration': 'Blijf dicht bij het perspectief van één of enkele personages en doseer wat zij weten. Laat onzekerheid ontstaan uit beperkte informatie, tegenstrijdige interpretaties en relaties onder druk.',
            'language': 'Concreet, modern en efficiënt. Gebruik precieze sociale en fysieke observaties; vermijd lange abstracte bespiegelingen wanneer de scène spanning of confrontatie nodig heeft.',
            'rhythm': 'Vlotte hoofdstukken met duidelijke versnellingen. Kortere zinnen en alinea’s mogen spanning verhogen, maar gebruik langere passages waar observatie of psychologische twijfel belangrijk is.',
            'description': 'Kies details die status, relaties, dreiging of tijdgeest zichtbaar maken. Een gewone woning, straat, vakantieplek of vriendengroep mag juist door kleine afwijkingen onveilig gaan voelen.',
            'dialogue': 'Direct en geloofwaardig, met onderliggende irritatie, jaloezie, wantrouwen of geheimen. Personages hoeven niet alles te zeggen wat ze denken; conflicten mogen in bijzinnen en stiltes zitten.',
            'emotion_intimacy': 'Emotie is lichamelijk en psychologisch merkbaar. Relaties, seksualiteit, schaamte, jaloezie en loyaliteit kunnen bronnen van spanning zijn; beschrijf intensiteit functioneel en niet als los effect.',
            'scenes_pacing': 'Laat vrijwel iedere scène informatie, verdenking of relationele druk verschuiven. Eindig hoofdstukken regelmatig met een concrete nieuwe vraag, ontdekking of dreiging zonder elk hoofdstuk kunstmatig als cliffhanger te laten voelen.',
            'editorial': 'Controleer causaliteit, geloofwaardige motieven en timing van onthullingen. Bewaak dat de lezer voldoende aanwijzingen krijgt en dat twists achteraf logisch terug te lezen zijn.',
            'avoid': 'Vermijd toevallige reddingen, schurken zonder menselijk motief, misleiding door informatie te verzwijgen die het perspectiefpersonage gewoon weet en dreiging die alleen uit expliciete waarschuwingen bestaat.',
            'examples': '',
            'additional': 'Dit is een algemeen Nederlands thrillerprofiel en geen opdracht om bestaande boeken of specifieke formuleringen te imiteren.',
        },
    },
    'slee': {
        'name': 'Carry Slee',
        'subtitle': 'Jeugd/tiener · herkenbare problemen · directe emotie',
        'description': 'Een bewerkbaar profiel voor kinder- en tienerfictie met herkenbare relaties, duidelijke inzet en een toegankelijke vertelstem.',
        'values': {
            'voice_tone': 'Toegankelijk, betrokken en direct. Neem emoties en problemen van jonge personages serieus zonder belerend of kinderachtig te worden.',
            'narration': 'Blijf dicht bij wat het jonge perspectiefpersonage begrijpt, vreest en hoopt. Volwassen context mag aanwezig zijn, maar het verhaal wordt beleefd vanuit de relevantie voor de jongere hoofdpersoon.',
            'language': 'Helder en leeftijdsadequaat. Gebruik natuurlijke woorden en zinsbouw, met eigentijdse spreektaal waar dat geloofwaardig is. Moeilijke onderwerpen hoeven niet met moeilijke taal te worden verteld.',
            'rhythm': 'Vlot, met overzichtelijke hoofdstukken en duidelijke scène-doelen. Wissel spanning en problemen af met humor, vriendschap en momenten van opluchting.',
            'description': 'Concreet en functioneel. School, thuis, vrienden, sport en sociale situaties worden vooral beschreven via wat voor het personage op dat moment belangrijk of opvallend is.',
            'dialogue': 'Natuurlijk en direct. Verschillen tussen vrienden, ouders, leraren en leeftijdsgenoten moeten hoorbaar zijn zonder karikatuur. Laat conflicten ook ontstaan uit groepsdruk, schaamte en loyaliteit.',
            'emotion_intimacy': 'Emoties mogen duidelijk benoemd of voelbaar gemaakt worden. Verliefdheid en lichamelijkheid worden afgestemd op doelgroep en leeftijd; veiligheid, grenzen en geloofwaardige ontwikkeling gaan voor spektakel.',
            'scenes_pacing': 'Elke scène brengt een probleem, keuze, relatie of ontdekking verder. Houd de inzet concreet en persoonlijk, zodat grotere thema’s via het leven van de personages begrijpelijk worden.',
            'editorial': 'Controleer leeftijdsgeloofwaardigheid, helderheid en emotionele logica. Signaleer volwassen uitleg die een jong personage niet vanzelf zou formuleren en oplossingen waarbij volwassenen alle problemen overnemen.',
            'avoid': 'Vermijd moraliserende slotzinnen, kinderen die praten als beleidsmakers, hippe jongerentaal die geforceerd voelt en zware thema’s die alleen als les worden gebruikt.',
            'examples': '',
            'additional': 'Dit profiel is een generiek vertrekpunt voor jeugd- en tienerfictie. Pas doelgroep, leeftijd en explicietheid altijd aan het concrete boek aan.',
        },
    },
}
