# QuietWriter 0.8.0

QuietWriter is een lokale Python-desktopapp voor het schrijven van boeken en verhalen. Manuscripten blijven gewone Markdown-bestanden. De applicatie combineert een rustige editor met versiegeschiedenis, spellingscontrole en een modulaire AI-laag.

## Installeren

Python 3.12 of nieuwer wordt aanbevolen.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## AI

Open **Instellingen > AI**. QuietWriter ondersteunt nu een provider-onafhankelijke AI-laag.

### Ollama

Ollama blijft de standaard. QuietWriter controleert bij het opstarten of Ollama bereikbaar is en haalt de lokale modellen op. Je kunt afzonderlijk kiezen voor:

- **Schrijf- en analysemodel** — het grotere model voor schrijven, feedback en analyse;
- **Snel achtergrondmodel** — een klein lokaal model dat als bibliothecaris kan werken;
- **Embeddingmodel (optioneel)** — bijvoorbeeld een lokaal embeddingmodel voor semantische verhaalzoekopdrachten.

### OpenRouter

Kies **OpenRouter** als AI-provider, vul een API-key in en klik op **Modellen ophalen**. De rest van QuietWriter blijft dezelfde AI-functies gebruiken; providerdetails zitten volledig achter de provider-interface.

Het snelle achtergrondmodel blijft standaard lokaal via Ollama. Daardoor kun je later bijvoorbeeld een groot OpenRouter-model voor analyse gebruiken en een klein lokaal Ollama-model voor bibliotheektaken.

## AI-context

De schrijverpersona uit `persona/schrijver.md` wordt altijd toegevoegd.

Daarbovenop kun je als context kiezen:

- huidig hoofdstuk;
- huidige sectie;
- hele boek;
- verhalenbibliotheek.

Als je tekst in de editor selecteert, krijgt die selectie automatisch voorrang. In het AI-paneel laat **Context bekijken** zien welke context is gebruikt en welke oude verhalen zijn geraadpleegd.

## Verhalenbibliotheek en RAG

Bij **Verhalenbibliotheek** gebruikt QuietWriter meerdere lagen:

1. lokale full-text search en metadata;
2. tags krijgen extra gewicht;
3. het snelle achtergrondmodel kan een compacte catalogus van alle verhalen in batches beoordelen;
4. als een embeddingmodel is gekozen, worden semantisch vergelijkbare verhalen meegenomen;
5. alleen de meest relevante verhalen gaan als volledige context naar het hoofdmodel.

Embeddingvectors worden gecachet in:

```text
.cache/story_embeddings.db
```

Als een verhaal wijzigt, wordt de oude embedding automatisch ongeldig door de gewijzigde bestandsdatum.

## AI-gesprekken

Gesprekken worden per boek opgeslagen in:

```text
books/<boek>/.quietwriter/ai_chat.json
```

Daarmee blijft de chat bij het boek horen. **Nieuw gesprek** leegt die conversatie. Alleen de recente conversatie wordt opnieuw naar het model gestuurd; manuscriptcontext wordt bij iedere opdracht opnieuw opgebouwd zodat die niet veroudert.

AI-antwoorden worden als Markdown weergegeven, inclusief koppen, vet, cursief, lijsten en codeblokken. De AI verandert nooit zelfstandig je manuscript.

## Werkmap

Standaard:

```text
C:\Users\<naam>\QuietWriter
```

Belangrijke mappen:

```text
QuietWriter/
├── books/
├── stories/
├── boekomslagen/
├── persona/
│   └── schrijver.md
├── archive/
├── trash/
├── dictionaries/
└── .cache/
```

## Spellingscontrole

QuietWriter bundelt bewust geen woordenboeken. Het zoekt automatisch in de werkmap en in gangbare installaties van ONLYOFFICE, LibreOffice en OpenOffice. Alle gevonden Hunspell-talen worden getoond met een leesbare naam.

De editor toont rode spellinghints. Het rechter spellingspaneel biedt stap-voor-stap wijzigen, negeren, alles negeren, altijd negeren en toevoegen aan het persoonlijke woordenboek.

## Versiegeschiedenis

Via het klok-icoon zijn automatische dagarchieven en handmatige versies zichtbaar. Oude versies kunnen alleen-lezen worden bekeken, met ster worden gemarkeerd en veilig worden hersteld. Vóór herstel maakt QuietWriter automatisch een veiligheidsversie van de huidige toestand.

## Tests

```powershell
python -m unittest discover -s tests -v
```

0.8.0 bevat **31 automatische tests**, onder andere voor drag-and-drop, Dropbox/Windows file locks, versieherstel, woordenboeken, spellingsengine, AI-providerselectie, gesprekopslag, metadata-RAG en embeddingcache.

Zie `ROADMAP.md` voor de volgende iteraties.
