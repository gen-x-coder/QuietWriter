# Dev.52 — Handmatig onthouden in de Meelezer

De Meelezer heeft onderaan bij **Context** en **Snelacties** een knop **Onthouden**.
Die opent een eigen venster met een bewerkbare tekst en de vijf bestaande categorieën van Boekgeheugen. Standaard verschijnt het laatste **eigen** bericht van de schrijver (zonder `Nieuw feit:`-prefix), nooit een door de AI geclaimd feit. De standaardcategorie is **Canon & feiten**. Zowel tekst als categorie zijn vóór het opslaan te veranderen.

De actie is volledig lokaal en stuurt niets naar Ollama of OpenRouter. Pas bij bevestiging gebruikt QuietWriter dezelfde `BookMemoryPage.add_suggestion()` als de bestaande goedkeuringskaarten. Die schrijft naar `ai/memory.md` en leest dit opnieuw vanaf schijf ter controle. Bij succes verschijnt een lokale chatmelding; bij een fout verschijnt een melding zonder onterechte succesclaim. De bestaande AI-geheugenvoorstellen blijven beschikbaar, maar zijn niet noodzakelijk om iets vast te leggen.

De knop staat bewust **niet** in de compacte bovenste balk met Pop-out, Bewaren en Gesprekken: deze mag niet opnieuw afbreken bij smalle rechterpanelen. Er is geen los geheugenbestand per gesprek; de inhoud hoort bij het actieve boek.

## Acceptatietest op Windows

1. Open boek Pip, ga naar Meelezer en klik **Onthouden** zonder eerst iets te vragen. Vul `Pip heeft geen haar` in, kies Canon & feiten, sla op.
2. Controleer de zichtbare succesmelding en inhoud van **Boekgeheugen**. Heropen het boek, controleer dezelfde regel.
3. Vraag iets aan de Meelezer, klik **Onthouden**: de laatste **eigen** vraag staat klaar; bewerk die tot een canonfeit.
4. Annuleer het venster en controleer dat niets is toegevoegd.
5. Probeer een lege tekst (de knop Onthouden is uitgeschakeld), hetzelfde feit nogmaals (geen dubbele opslag), en wissel van boek om boekisolatie te controleren.
6. Schakel OpenRouter uit en probeer opnieuw: lokale opslag moet blijven werken.

De Qt-weergave vereist handmatige Windows-acceptatie. In de ontwikkelomgeving zijn de bestaande Meelezer-tests en de Python-syntax gecontroleerd.
