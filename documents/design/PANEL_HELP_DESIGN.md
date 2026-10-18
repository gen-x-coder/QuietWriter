# QuietWriter: uitleg in de rechterpanelen (ontwerp voor 1.2.9)

**Gebaseerd op:** 1.2.8 (code gelezen: `editor_page.py`, `main_window.py`, alle paneelbestanden, `ai/ui.py`,
`settings_page.py`, `first_run.py`, `themes.py`, de vijf locales).
**Visueel ontwerp:** canvas "QuietWriter Paneeluitleg", met 6 borden:
1. Open punten bij de eerste keer;
2. Open punten na Begrepen;
3. Zoeken;
4. Meelezer;
5. de toestanden van het component in Helder, Nacht en 150%;
6. Instellingen.

**Voor:** ChatGPT (bouw) en Lucas (beslissingen).

---

## 1. Wat het moet doen

Lucas' wens, vertaald naar gedrag:

| # | Gedrag |
|---|---|
| G1 | Elk rechterpaneel (behalve Toevoegen, zie §6) heeft een korte uitleg van 1 tot 3 zinnen. |
| G2 | De eerste keer dat je een paneel opent, staat de uitleg **open**. |
| G3 | Met **Begrepen** klap je de uitleg in. Dat wordt per paneel onthouden. |
| G4 | Een **?-knop** in de titelregel van het paneel klapt de uitleg altijd weer open of dicht. |
| G5 | **Standaardinstellingen herstellen** zet alle uitleg weer open. Dat gaat vanzelf: `settings.clear()` wist de vlaggen. |
| G6 | In Instellingen › Algemeen staat **Alle uitleg weer tonen**. Daarmee zet je alleen de uitleg terug, zonder de rest van je instellingen te verliezen. |
| G7 | Er komen **geen** modale vensters voor uitleg. Het venster bij het eerste open punt verdwijnt. |

## 2. Waarom zo (de ontwerpprincipes)

- **Rust boven veel functies.** De uitleg staat er alleen totdat je hem kent. Daarna blijft er één kleine ?-knop over,
  zonder kleur en zonder rand. Het ingeklapte paneel ziet er dus vrijwel uit zoals nu.
- **Eén visuele grammatica.** Het uitlegblok hergebruikt `softPanel` (`panel2`, `border_subtle`, radius 10).
  **Begrepen** is dezelfde tweede-niveauknop als de bestaande Meelezer-melding, met dezelfde tekst
  (`common.understood`). Er komen geen nieuwe kleuren bij, alleen bestaande tokens.
- **Geen modale vensters voor uitleg.** Het `QMessageBox` uit `_explain_open_points_once` verdwijnt. De uitleg staat
  in het paneel, op de plek waar je hem nodig hebt.
- **Uitleg is geen waarschuwing.** De Meelezer-melding over hoofdstukplanning gaat over privacy (gegevens die je computer
  verlaten). Die blijft een **aparte** melding, met een eigen sleutel, en krijgt in het ontwerp de `warning_soft`-kleur.
  Zo zie je meteen het verschil tussen "zo werkt het" en "let op". Zie bord 4.
- **Toetsenbord eerst.** De ?-knop zit in de tabvolgorde direct na de paneeltitel. Na Begrepen gaat de focus naar de
  ?-knop, dus niet naar het einde van het paneel en ook niet nergens heen.
- **150%.** Het blok heeft geen vaste hoogte. De tekst loopt door, het paneel scrolt, en niets wordt afgekapt. Dat is
  precies de les uit bevinding 1 van ronde 90. Zie bord 5, met het smalste paneel van 300 logische pixels.

## 3. Component: `ui/panel_help.py`

Eén klein bestand en één klasse. Elk paneel gebruikt dezelfde klasse, zodat het gedrag nooit per paneel uiteenloopt.

```python
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..i18n import tr
from ..icon_theme import icon   # bestaande helper


def _key(panel_id: str) -> str:
    return f'help/{panel_id}/dismissed'


class PanelHelp(QWidget):
    """Titelregel met ?-knop plus inklapbaar uitlegblok, voor de rechterpanelen."""

    expandedChanged = Signal(bool)

    def __init__(self, settings, panel_id: str, title: str, text: str, *, extra_title_widgets=(), parent=None):
        super().__init__(parent)
        self.settings = settings
        self.panel_id = panel_id

        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(10)

        row = QHBoxLayout(); row.setSpacing(8)
        self.title = QLabel(title); self.title.setObjectName('sectionTitle')
        row.addWidget(self.title, 1)
        for w in extra_title_widgets:          # bijv. "Nieuw gesprek" in de Meelezer
            row.addWidget(w)
        self.toggle = QPushButton(); self.toggle.setObjectName('panelHelpButton')
        self.toggle.setIcon(icon('help')); self.toggle.setCheckable(True)
        self.toggle.setFixedSize(32, 32)
        name = tr('panel_help.toggle', 'Uitleg over {panel}', panel=title)
        self.toggle.setAccessibleName(name); self.toggle.setToolTip(name)
        self.toggle.toggled.connect(self._on_toggled)
        row.addWidget(self.toggle, 0, Qt.AlignTop)
        root.addLayout(row)

        self.block = QFrame(); self.block.setObjectName('softPanel')
        self.block.setAccessibleName(tr('panel_help.region', 'Uitleg'))
        b = QVBoxLayout(self.block); b.setContentsMargins(14, 12, 14, 12); b.setSpacing(10)
        self.text = QLabel(text); self.text.setWordWrap(True)
        self.text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)   # GEEN vaste minimumhoogte
        b.addWidget(self.text)
        self.ok = QPushButton(tr('common.understood', 'Begrepen')); self.ok.setObjectName('secondaryButton')
        self.ok.clicked.connect(self.dismiss)
        okrow = QHBoxLayout(); okrow.addWidget(self.ok); okrow.addStretch(1)
        b.addLayout(okrow)
        root.addWidget(self.block)

        self.sync_from_settings()

    # --- toestand ---------------------------------------------------------
    def is_dismissed(self) -> bool:
        return self.settings.value(_key(self.panel_id), False, bool)

    def sync_from_settings(self) -> None:
        """Aanroepen bij elke keer dat het paneel opent."""
        self.set_expanded(not self.is_dismissed(), remember=False)

    def set_expanded(self, expanded: bool, *, remember: bool) -> None:
        self.toggle.blockSignals(True); self.toggle.setChecked(expanded); self.toggle.blockSignals(False)
        self.block.setVisible(expanded)
        if remember:
            self.settings.setValue(_key(self.panel_id), not expanded); self.settings.sync()
        self.expandedChanged.emit(expanded)

    def collapse_temporarily(self) -> None:
        """Inklappen zonder te onthouden (gebruikt door de Meelezer, zie §5)."""
        self.set_expanded(False, remember=False)

    def dismiss(self) -> None:
        self.set_expanded(False, remember=True)
        self.toggle.setFocus(Qt.OtherFocusReason)

    def _on_toggled(self, checked: bool) -> None:
        self.set_expanded(checked, remember=True)
        if checked:
            self.ok.setFocus(Qt.OtherFocusReason)

    def retranslate(self, title: str, text: str) -> None:
        self.title.setText(title); self.text.setText(text)
```

**Toestandsregel:** de uitleg staat open als `help/<id>/dismissed` niet `true` is. Er is één bron van waarheid en
er zijn geen andere vlaggen.
- **Begrepen** → `dismissed = true`.
- **?** dichtklikken → `dismissed = true`.
- **?** openklikken → `dismissed = false`. Wie de uitleg zelf weer opent en het paneel sluit, ziet hem de volgende
  keer dus weer. Dat is bewust: het ? is een schakelaar, geen eenmalige blik.

**Waarom `sync_from_settings()` bij elke keer openen:** zo werkt **Alle uitleg weer tonen** meteen, ook voor panelen die
al gebouwd zijn. Je hoeft niets opnieuw op te bouwen of opnieuw te starten.

### QSS (in `themes.py`, alleen tokens)

```css
QPushButton#panelHelpButton { background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 0; color: {muted}; }
QPushButton#panelHelpButton:hover { background: {hover}; }
QPushButton#panelHelpButton:focus { border-color: {focus}; }
QPushButton#panelHelpButton:checked { background: {accent_soft}; border-color: {accent}; }
```

`softPanel` bestaat al. Het icoon `help` is een cirkel met een vraagteken, net zo dun als de andere railiconen
(stroke 1,6–1,7). Het pad staat in het canvasbord. Maak het icoon voor elk thema in de kleur van het thema, zoals de
bestaande iconen.

## 4. Inbouwen per paneel

Elk paneel krijgt een `PanelHelp` als bovenste widget, **in plaats van** de huidige titel-`QLabel`. In
`EditorPage._toggle_right_widget` komt, net vóór `setCurrentWidget`, één regel:

```python
help_widget = getattr(widget, 'panel_help', None)
if help_widget is not None and not closing_same:
    help_widget.sync_from_settings()
```

| Paneel (`panel_id`) | Bestand | Wat verdwijnt | Opmerking |
|---|---|---|---|
| `search` | `search_panel.py` | titel-QLabel | |
| `chapter_context` | `chapter_context_panel.py` | titel-QLabel **en** het vaste intro-label (`chapter_context.intro`) | De uitleg vervangt de intro, zodat er geen dubbele tekst is. De melding over de lege toestand blijft. |
| `open_points` | `open_points_panel.py` | titel-QLabel **en** de vaste intro (`open_points.panel_intro`) | **en** `_explain_open_points_once` plus de aanroep in `add_open_point`. De vlag `open_points/explained` wordt niet meer gelezen. |
| `ai` | `ai/ui.py` | titel-QLabel | "Nieuw gesprek" gaat via `extra_title_widgets`, zodat het ? rechts blijft. De toestemmingsmelding blijft ongewijzigd (zie §5). |
| `spell` | `spell_panel.py` | titel-QLabel | |
| `history` | `history_panel.py` | titel-QLabel | |
| `darlings` | `darlings_actions_panel.py` | titel-QLabel | |
| (Toevoegen) | `insert_panel.py` | **niets** | Zie §6. |

**De focus bij het openen** van een paneel blijft zoals nu (zoekveld, lijst enz.). De uitleg pakt de focus niet af.
Een schermlezer leest het blok wel, omdat het direct onder de titel staat en een toegankelijke naam heeft.

**Volgorde van de tabtoets in elk paneel:** titel-? → (Begrepen, als de uitleg open is) → de rest van het paneel.

## 5. Meelezer: twee speciale regels

1. **De toestemmingsmelding blijft apart.** `chapter_planning_notice_row` houdt haar eigen sleutel en haar eigen
   Begrepen. Advies: geef haar `objectName('noticePanel')` met `warning_soft`/`warning`-randen, zodat je haar niet
   verwart met de uitleg (bord 4). Volgorde: uitleg boven, melding eronder. Beide kun je los wegklikken.
2. **De uitleg klapt tijdelijk in zodra je Context of Snelacties opent.** In `_toggle_context_controls` en
   `_toggle_quick_actions` komt `if checked: self.panel_help.collapse_temporarily()`. Dat wordt **niet** onthouden. Je
   hebt dan aan de uitleg laten zien dat je verder bent, maar je hebt niet bewust op Begrepen geklikt. Bij de volgende
   keer openen staat de uitleg weer open, totdat je Begrepen kiest. Reden: het Meelezer-paneel is het drukste paneel;
   anders duwen uitleg, melding, Context en Snelacties samen het gesprek uit beeld bij 150%.

## 6. Toevoegen krijgt geen uitleg (advies)

Het paneel Toevoegen bestaat al uit drie kaarten, elk met een eigen beschrijving ("Markeer een duidelijke overgang
tussen twee scènes." enz.). Een uitlegblok erboven zou herhalen wat er al staat. Dat botst met "rust boven veel
functies". Het paneel krijgt dus wel dezelfde titelregel (voor de uitlijning), maar **zonder ?-knop**. Geef daarvoor
`PanelHelp` een parameter `text=None`, die de knop en het blok weglaat. Wil Lucas toch overal een ?, dan staat er in §8
een tekst klaar.

## 7. Instellingen › Algemeen

Een nieuwe sectie **Uitleg**, tussen Updates en Opnieuw instellen (bord 6):

```python
self._add_settings_section(gl, tr('settings.section.help', 'Uitleg'))
show_help = QPushButton(tr('settings.help.reset_button', 'Alle uitleg weer tonen'))
show_help.clicked.connect(self._reset_panel_help)
self._add_settings_field(gl, tr('settings.help.label', 'Uitleg in panelen'), show_help,
    tr('settings.help.help', 'Toont de korte uitleg in de panelen van de rechterbalk weer, zoals de eerste keer. Je boeken en instellingen blijven ongewijzigd.'))

def _reset_panel_help(self):
    self.settings.beginGroup('help'); self.settings.remove(''); self.settings.endGroup(); self.settings.sync()
    # toon via de bestaande self.save_feedback (settingsToast), zoals in de opslaan-melding rond regel 972
    self.save_feedback.setText(tr('settings.help.reset_done', 'De uitleg staat weer open in alle panelen.')); self.save_feedback.show()
```

- Dit wordt **direct** uitgevoerd, net als "Nu controleren", en hangt niet af van **Opslaan**. Het is een actie, geen
  instelling.
- Is er een paneel open, dan ziet de gebruiker het effect bij de volgende keer openen (via `sync_from_settings`).
  Ververs het open paneel niet ongevraagd.
- De toestemmingsmelding van de Meelezer wordt hiermee **niet** teruggezet. Dat is een melding, geen uitleg.

**Standaardinstellingen herstellen:** er is niets extra nodig. `settings.clear()` wist ook de groep `help/`. Zet dat wel
in de test (§9).

## 8. Teksten

Toon: **jij/je**, kort, wat het paneel doet en één ding dat je anders zou missen. Maximaal drie zinnen. Knop- en
paneelnamen schrijf je zoals ze in die taal in de app staan (gecontroleerd tegen de locales van 1.2.8). In het Duits en
Frans gebruiken we **Sie/vous** en in het Spaans **tú**, net als de bestaande locales.

**Gecontroleerd in de code**, zodat de teksten niets beloven wat de app niet doet:
- **Negeren** slaat één plek over.
- **Alles negeren** geldt zolang QuietWriter draait.
- **Altijd negeren** is blijvend.
- Er komt één automatische versie per dag waarop je hebt geschreven.
- Snelacties vullen alleen de vraag in. De Meelezer past het manuscript niet aan.

### Nieuwe sleutels

| Sleutel | nl |
|---|---|
| `panel_help.toggle` | Uitleg over {panel} |
| `panel_help.region` | Uitleg |
| `settings.section.help` | Uitleg |
| `settings.help.label` | Uitleg in panelen |
| `settings.help.reset_button` | Alle uitleg weer tonen |
| `settings.help.help` | Toont de korte uitleg in de panelen van de rechterbalk weer, zoals de eerste keer. Je boeken en instellingen blijven ongewijzigd. |
| `settings.help.reset_done` | De uitleg staat weer open in alle panelen. |

| Sleutel | en | de | fr | es |
|---|---|---|---|---|
| `panel_help.toggle` | About {panel} | Erklärung zu {panel} | À propos de {panel} | Acerca de {panel} |
| `panel_help.region` | Explanation | Erklärung | Explication | Explicación |
| `settings.section.help` | Explanations | Erklärungen | Explications | Explicaciones |
| `settings.help.label` | Panel explanations | Erklärungen in Bereichen | Explications des panneaux | Explicaciones de los paneles |
| `settings.help.reset_button` | Show all explanations again | Alle Erklärungen wieder anzeigen | Réafficher toutes les explications | Volver a mostrar todas las explicaciones |
| `settings.help.help` | Shows the short explanations in the right-hand panels again, as on first use. Your books and settings stay as they are. | Zeigt die kurzen Erklärungen in den Bereichen der rechten Leiste wieder an, wie beim ersten Mal. Ihre Bücher und Einstellungen bleiben unverändert. | Réaffiche les courtes explications des panneaux de la barre de droite, comme la première fois. Vos livres et vos paramètres ne changent pas. | Vuelve a mostrar las explicaciones breves de los paneles de la barra derecha, como la primera vez. Tus libros y ajustes no cambian. |
| `settings.help.reset_done` | Explanations are shown again in all panels. | Die Erklärungen werden in allen Bereichen wieder angezeigt. | Les explications sont de nouveau affichées dans tous les panneaux. | Las explicaciones vuelven a mostrarse en todos los paneles. |

### Uitlegteksten (`panel_help.<id>`)

**`panel_help.search`**
- **nl:** Zoek in dit hoofdstuk, deze sectie of het hele boek. Vervang treffers één voor één, of allemaal tegelijk met Alles vervangen.
- **en:** Search this chapter, this section or the whole book. Replace matches one at a time, or all at once with Replace all.
- **de:** Suchen Sie in diesem Kapitel, diesem Abschnitt oder im ganzen Buch. Ersetzen Sie Treffer einzeln oder mit Alle ersetzen auf einmal.
- **fr:** Recherchez dans ce chapitre, cette section ou tout le livre. Remplacez les résultats un par un, ou tous à la fois avec Tout remplacer.
- **es:** Busca en este capítulo, esta sección o todo el libro. Reemplaza los resultados uno a uno, o todos a la vez con Reemplazar todo.

**`panel_help.chapter_context`** (vervangt `chapter_context.intro`)
- **nl:** Hier zie je de scènes en personages die je in Planning aan dit hoofdstuk hebt gekoppeld, zodat je je plan bij de hand hebt tijdens het schrijven. Wijzigen doe je in Planning.
- **en:** Here you see the scenes and characters you linked to this chapter in Planning, so your plan is at hand while you write. To change them, go to Planning.
- **de:** Hier sehen Sie die Szenen und Figuren, die Sie in Planung mit diesem Kapitel verknüpft haben. So haben Sie Ihren Plan beim Schreiben zur Hand. Ändern können Sie sie in Planung.
- **fr:** Vous voyez ici les scènes et les personnages liés à ce chapitre dans Planification, pour garder votre plan sous la main pendant l’écriture. Pour les modifier, passez par Planification.
- **es:** Aquí ves las escenas y los personajes que vinculaste a este capítulo en Planificación, para tener tu plan a mano mientras escribes. Para cambiarlos, ve a Planificación.

**`panel_help.open_points`** (vervangt `open_points.panel_intro` en `open_points.explain_text`)
- **nl:** Markeer woorden of passages die je later nog wilt aanvullen, in plaats van XXX of TODO te typen. QuietWriter houdt ze hier bij en waarschuwt je vóór een export. De markering zelf komt nooit in je export terecht.
- **en:** Mark words or passages you want to fill in later, instead of typing XXX or TODO. QuietWriter keeps track of them here and warns you before an export. The marker itself never ends up in your export.
- **de:** Markieren Sie Wörter oder Passagen, die Sie später ergänzen möchten, statt XXX oder TODO zu tippen. QuietWriter behält sie hier im Blick und warnt Sie vor einem Export. Die Markierung selbst landet nie im Export.
- **fr:** Marquez les mots ou passages à compléter plus tard, au lieu de taper XXX ou TODO. QuietWriter les suit ici et vous avertit avant une exportation. Le marqueur lui-même n’apparaît jamais dans l’export.
- **es:** Marca palabras o pasajes que quieras completar más adelante, en lugar de escribir XXX o TODO. QuietWriter los sigue aquí y te avisa antes de exportar. La marca en sí nunca aparece en la exportación.

**`panel_help.ai`**
- **nl:** Stel een vraag over je tekst, of selecteer een passage en kies een snelactie. Het antwoord verschijnt hier; je manuscript verandert alleen als jij het zelf aanpast. Onder Context zie je wat er wordt meegestuurd.
- **en:** Ask a question about your text, or select a passage and pick a quick action. The answer appears here; your manuscript only changes when you edit it yourself. Under Context you can see what is sent.
- **de:** Stellen Sie eine Frage zu Ihrem Text, oder markieren Sie eine Passage und wählen Sie eine Schnellaktion. Die Antwort erscheint hier; Ihr Manuskript ändert sich nur, wenn Sie es selbst bearbeiten. Unter Kontext sehen Sie, was mitgesendet wird.
- **fr:** Posez une question sur votre texte, ou sélectionnez un passage et choisissez une action rapide. La réponse s’affiche ici ; votre manuscrit ne change que si vous le modifiez vous-même. Sous Contexte, vous voyez ce qui est envoyé.
- **es:** Haz una pregunta sobre tu texto, o selecciona un pasaje y elige una acción rápida. La respuesta aparece aquí; tu manuscrito solo cambia si lo editas tú. En Contexto ves qué se envía.

**`panel_help.spell`**
- **nl:** Loop de onbekende woorden in dit hoofdstuk één voor één langs. Negeren slaat alleen deze plek over; Alles negeren geldt tot je QuietWriter sluit. Altijd negeren en Toevoegen aan woordenboek onthouden het woord blijvend.
- **en:** Go through the unknown words in this chapter one by one. Ignore skips only this spot; Ignore all lasts until you close QuietWriter. Always ignore and Add to dictionary remember the word for good.
- **de:** Gehen Sie die unbekannten Wörter in diesem Kapitel einzeln durch. Ignorieren überspringt nur diese Stelle; Alle ignorieren gilt, bis Sie QuietWriter schließen. Immer ignorieren und Zum Wörterbuch hinzufügen merken sich das Wort dauerhaft.
- **fr:** Parcourez un par un les mots inconnus de ce chapitre. Ignorer ne saute que cet endroit ; Tout ignorer vaut jusqu’à la fermeture de QuietWriter. Toujours ignorer et Ajouter au dictionnaire retiennent le mot définitivement.
- **es:** Revisa una a una las palabras desconocidas de este capítulo. Ignorar solo omite este lugar; Ignorar todo dura hasta que cierres QuietWriter. Ignorar siempre y Añadir al diccionario recuerdan la palabra para siempre.

**`panel_help.history`**
- **nl:** Elke dag dat je schrijft, bewaart QuietWriter automatisch een versie van je boek. Maak zelf een versie vóór een grote wijziging en geef belangrijke versies een ster.
- **en:** Every day you write, QuietWriter automatically keeps a version of your book. Create a version yourself before a big change, and star the versions that matter.
- **de:** An jedem Tag, an dem Sie schreiben, speichert QuietWriter automatisch eine Version Ihres Buchs. Erstellen Sie vor einer großen Änderung selbst eine Version und markieren Sie wichtige Versionen mit einem Stern.
- **fr:** Chaque jour où vous écrivez, QuietWriter conserve automatiquement une version de votre livre. Créez vous-même une version avant un grand changement et ajoutez une étoile aux versions importantes.
- **es:** Cada día que escribes, QuietWriter guarda automáticamente una versión de tu libro. Crea tú una versión antes de un cambio grande y marca con una estrella las versiones importantes.

**`panel_help.darlings`**
- **nl:** Tekst die je schrapt maar niet kwijt wilt, bewaar je hier. Selecteer een passage en kopieer of knip hem naar de Bewaarplaats. Alles wat je bewaart, vind je terug via Bewaarplaats openen.
- **en:** Keep text you cut but don't want to lose here. Select a passage and copy or cut it to Darlings. Everything you keep can be found again via Open Darlings.
- **de:** Text, den Sie streichen, aber nicht verlieren möchten, bewahren Sie hier auf. Markieren Sie eine Passage und kopieren oder schneiden Sie sie nach Darlings aus. Alles Aufbewahrte finden Sie über Darlings öffnen wieder.
- **fr:** Gardez ici le texte que vous supprimez sans vouloir le perdre. Sélectionnez un passage et copiez-le ou coupez-le vers Darlings. Vous retrouvez tout ce que vous gardez via Ouvrir Darlings.
- **es:** Guarda aquí el texto que eliminas pero no quieres perder. Selecciona un pasaje y cópialo o córtalo a Darlings. Todo lo que guardas lo encuentras de nuevo con Abrir Darlings.

**(Alleen als Lucas toch een ? bij Toevoegen wil) `panel_help.insert`**
- **nl:** Voeg op de plek van de cursor een scènebreuk, open punt of afbeelding toe.
- **en:** Add a scene break, open point or image at the cursor.
- **de:** Fügen Sie an der Cursorposition einen Szenenumbruch, einen offenen Punkt oder ein Bild ein.
- **fr:** Ajoutez un saut de scène, un point ouvert ou une image à l’emplacement du curseur.
- **es:** Añade un salto de escena, un punto abierto o una imagen en la posición del cursor.

**Op te ruimen sleutels** (in alle vijf de locales tegelijk, anders klaagt `check_locales.py`):
- `chapter_context.intro`
- `open_points.panel_intro`
- `open_points.explain_title`
- `open_points.explain_text`

## 9. Tests

**Zonder Qt** (`tests/test_panel_help.py`, met een nep-QSettings of een INI-bestand in tmp):
1. Een nieuwe instelling geeft `dismissed` = False voor alle zeven id's.
2. `settings.clear()` (via `request_first_run_reset`) maakt alle `help/*` weer leeg.
3. `_reset_panel_help` wist `help/*`, maar laat andere sleutels staan, zoals `theme`, `export/guided` en de sleutel van
   de Meelezer-melding.
4. Alle `panel_help.*`-sleutels bestaan in alle vijf de locales, en geen enkele tekst is langer dan drie zinnen
   (tel `. `/`? `/`! `).

**Met Qt** (`tests/test_panel_help_qt.py`, met `pytestmark = pytest.mark.qt` en **zonder** `qtbot`):
1. Open elk paneel via `ep.show_*()`. Het uitlegblok moet zichtbaar zijn en `toggle.isChecked()` moet waar zijn.
2. Klik op Begrepen. Het blok verdwijnt, de focus staat op de ?-knop, en de vlag is waar. Na sluiten en weer openen
   blijft het blok verborgen.
3. Klik op ?. Het blok verschijnt en de vlag is onwaar.
4. **Alle uitleg weer tonen**, daarna het paneel openen: het blok is weer zichtbaar, zonder herstart.
5. Meelezer: zet Context aan. De uitleg is verborgen, maar de vlag blijft onwaar.
6. Open punten: `add_open_point()` toont **geen** QMessageBox. Patch `QMessageBox.information` en tel de aanroepen:
   die moeten 0 zijn.
7. **Geometrie bij 150%** (de les uit ronde 90): venster 1024×683 logisch, rechterpaneel op de minimumbreedte van 300,
   en `processEvents()`. Controleer daarna `help.text.height() >= help.text.heightForWidth(help.text.width())` voor
   alle panelen en alle vijf de talen.

## 10. Wat bewust buiten deze release valt

- Uitleg op de **hoofdpagina's** (Planning, Exporteren, enzovoort). Die hebben al een vaste paginakop met uitleg.
- **Een rondleiding** of het aanwijzen van de railknoppen. Dat past niet bij "rust", en de tooltips op de rail bestaan al.
- **Een animatie** van het in- en uitklappen. Dat is overbodig en lastig te testen.

## 11. Beslissingen voor Lucas

| # | Vraag | Advies |
|---|---|---|
| B1 | Toevoegen zonder ?-knop? | **Ja**, de kaarten leggen het al uit (§6). |
| B2 | ? openklikken zet de vlag terug, zodat de uitleg ook bij de volgende keer openen weer openstaat? | **Ja**, het ? is een schakelaar. Het alternatief, de uitleg alleen deze keer tonen, voelt als een knop die "niet onthoudt". |
| B3 | Meelezer-toestemmingsmelding: `warning_soft` geven? | **Ja**, dan is het verschil tussen melding en uitleg in één oogopslag te zien. Dat is een kleine QSS-wijziging. |
| B4 | Begrepen of Dit bericht verbergen? | **Begrepen**. Die tekst bestaat al in alle vijf de talen en is korter, wat helpt bij 150%. |
