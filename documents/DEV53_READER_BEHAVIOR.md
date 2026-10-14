# QuietWriter dev.53 — Meelezer: canon, geheugen en betrouwbaar taalgebruik

## Doel
De auteur blijft eigenaar van de fictieve wereld. De Meelezer mag adviseren, maar kan nooit zelfstandig het Boekgeheugen aanpassen. De knop **Onthouden** (sinds dev.52) blijft de betrouwbare opslagroute.

## Nieuw
- Systeemprompt: een expliciet door de auteur gegeven nieuw wereldfeit is canon, ook als het manuscript dat feit nog niet vermeldt. Wel concrete tegenstrijdigheden rapporteren.
- Onderscheid tussen auteurcanon, manuscript en vermoedens; beknopte antwoorden op korte feiten.
- Verbod op de claim dat de Meelezer zelf iets blijvend heeft opgeslagen of onthouden.
- Aanvullende applicatiecontrole in `quietwriter/ai/response_guard.py`: enkele herkenbare onterechte opslagclaims worden na het antwoord vervangen door een instructie om **Onthouden** te gebruiken. Dit is een vangnet, geen algemene semantische waarheidscontrole.
- Regressietests voor de Pip-casus, promptcontract en de `APP_NAME`-opstartregressie.

## Bewuste beperkingen
- De controle grijpt alleen in bij duidelijk herkenbare Nederlandse opslagclaims; niet bij alle mogelijke formuleringen, talen of passages. Tijdens het streamen kan de oorspronkelijke tekst kort zichtbaar zijn; de uiteindelijke chattekst wordt wel gecontroleerd.
- Het model mag nog steeds voorstellen formuleren in de bestaande `QW_MEMORY`-syntax. Opslag vereist altijd een expliciete gebruikersactie en schijfcontrole.
- Voor de nieuwe gedragsregels zijn daadwerkelijke Windows- en OpenRouter/Ollama-praktijktests nodig.

## Acceptatietests
1. Vertel: `Nieuw feit: Pip heeft geen haar.` Verwacht een kort antwoord zonder te eisen dat het al in de tekst staat.
2. Vertel: `Onthoud dit.` Verwacht geen bewering dat het reeds opgeslagen is; gebruik de knop **Onthouden**.
3. Klik **Onthouden**, bevestig canonfeit, sluit boek en open opnieuw: feit staat in Boekgeheugen.
4. Vraag naar inconsistenties in een manuscriptpassage: Meelezer vergelijkt auteurcanon en tekst.
5. Herhaal met `openrouter/free` (wisselende modellen) en een vast gekozen model.
6. Start vanuit uitgepakte bron met `python main.py` en controleer de versie.
