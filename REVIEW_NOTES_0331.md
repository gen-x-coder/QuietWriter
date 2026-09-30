# QuietWriter 0.33.1 — reviewinstructies

0.33.1 is de afsluitende correctiebuild voor 0.33. Geen nieuwe subsystemen of AI-logica.

## Verplicht
1. Draai de volledige suite met echte PySide6. Bekend: alleen de twee fontresource-tests mogen falen.
2. Rail op 700, 720 en 768 px, uitgeklapt: Menu bovenaan vast; PROGRAMMA onderaan zichtbaar zonder scrollen; alleen middengebied scrollt. Instellingen en Prullenbak moeten direct bereikbaar blijven.
3. Rail ingeklapt met boek open, AI aan en Geavanceerd aan: geen groepskoppen; subtiele separators tussen BIBLIOTHEEK / HUIDIG BOEK / AI-CONTEXT / PROGRAMMA. Geen separator voor een verborgen groep.
4. Zet AI uit en Geavanceerd uit, zowel preview als commit. Controleer dat separators/groepen meteen logisch volgen en de 0.33.0 side-effectscheiding intact blijft.
5. Controleer met het echte stylesheet dat de nav-scrollbar circa 5 px blijft en labels niet afbreken.
6. Lees de uitleg boven Schrijverspersona, Boekprofiel en Boekgeheugen. Deze moet eerlijk zeggen dat de context bij iedere AI-vraag naar de gekozen provider gaat; bij een externe provider verlaten de gegevens de computer. Boekprofiel moet de voorrangsregel t.o.v. Persona benoemen.
7. Herhaal de 0.33.0 railmatrix en de 0.32 smoke-regressie.

## Specifieke testfixes
- `test_rail_runtime_0330.py` laadt nu `stylesheet('Helder')` voordat scrollbarbreedte wordt gemeten.
- `test_settings_runtime_0322.py` controleert AI-CONTEXT/Integriteit in plaats van verwijderde 0.32-velden.

Als dit groen is, 0.33 sluiten en doorgaan met 0.34 Planning tijdens schrijven.
