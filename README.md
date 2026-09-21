# QuietWriter

QuietWriter is een lokale Python/PySide6-schrijfomgeving met boeken, secties, hoofdstukken, Markdown-opslag, versiegeschiedenis, spellingscontrole en een modulaire AI-assistent.

## Starten

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py main.py
```

## Markdown import

Op de boekenplank kies je **Importeren…** en selecteer je een `.md`-bestand. QuietWriter leest eenvoudige frontmatter zoals `title`, `description`, `meta`, `intro`, `tags`, `author`, `image`, `date` en `published`. Onbekende velden worden bewaard.

Een top-level kop wordt een hoofdstuk:

```markdown
# Hoofdstuk 1
Tekst...

# Hoofdstuk 2
Tekst...
```

Zonder `#`-kop wordt het hele bestand één hoofdstuk.

## Markdown export

Open **Boekdetails** en kies **Exporteren…**. QuietWriter schrijft één `.md`-bestand met frontmatter en alle hoofdstukken. Secties worden als onzichtbare Markdown/HTML-comments opgeslagen zodat QuietWriter ze bij herimport kan herstellen zonder dat ze op een website zichtbaar hoeven te worden.

## Scènebreuk

Gebruik de **+** knop in de rechter werkbalk en kies **Scènebreuk**. QuietWriter voegt dan een Markdown-scènebreuk toe:

```markdown
***
```

De scènebreuk blijft dus ook buiten QuietWriter gewone, leesbare Markdown.
