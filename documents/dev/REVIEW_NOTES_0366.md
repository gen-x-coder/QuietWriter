# Review notes 0.36.6

## Doel
OpenRouter-modellen beter bruikbaar maken voor gebruikers die gratis modellen willen kiezen.

## Gewijzigd
- gratis status uit actuele OpenRouter-pricing metadata;
- gratis modellen eerst in de dropdown;
- 🆓-markering naast de bestaande thinking-markering;
- filter “Alleen gratis modellen tonen”;
- voorkeur persistent in Instellingen;
- NL/EN uitleg en regressietests.

## Reviewpunten voor Claude
1. Controleer dat pricing `prompt=0` én `completion=0` correct als gratis geldt en betaalde modellen niet fout-positief worden.
2. Controleer dat `:free` en `openrouter/free` ook zonder complete pricingmetadata als gratis blijven gelden.
3. Controleer dat gratis modellen vóór betaalde modellen staan, maar de provider-volgorde binnen beide groepen behouden blijft.
4. Controleer dat de free-only filter geen betaald opgeslagen model terug in de lijst injecteert.
5. Controleer dat wisselen tussen Ollama/OpenRouter de filter alleen bij OpenRouter toont en de geselecteerde modellen per provider intact houdt.
6. Controleer dat Opslaan/Annuleren de nieuwe voorkeur transactioneel behandelt zoals de overige instellingen.
