# Review notes 0.36.7

## Doel
OpenRouter-antwoorden met niet-ASCII-tekens correct als UTF-8 tonen.

## Wijziging
`OpenRouterProvider.stream_chat()` leest SSE-regels als bytes en decodeert die expliciet met UTF-8. Dit voorkomt dat `requests` bij `text/event-stream` zonder charset Latin-1 gebruikt.

## Gericht testen
1. Open OpenRouter-Meelezer.
2. Vraag om een antwoord waarin woorden als `scène`, `één`, `café`, `naïef` en `€` voorkomen.
3. Geen `Ã`, `Â` of vervangtekens mogen zichtbaar zijn.
4. Controleer ook thinking/reasoning-streaming indien het gekozen model dit ondersteunt.
