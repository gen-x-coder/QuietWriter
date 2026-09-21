# Changelog

## 0.8.0 — AI-architectuur en slimme context

- AI-code opgesplitst in aparte modules onder `quietwriter/ai/`.
- Provider-onafhankelijke `AIProvider`-interface toegevoegd.
- Ollama-provider opnieuw opgebouwd bovenop deze interface.
- OpenRouter-provider toegevoegd; te activeren via Instellingen > AI.
- Hoofdmodel, snel achtergrondmodel en optioneel embeddingmodel zijn functioneel van elkaar gescheiden.
- Snel achtergrondmodel blijft standaard lokaal via Ollama, ook wanneer het hoofdmodel later via OpenRouter draait.
- AI-antwoorden worden als Markdown gerenderd: koppen, vet, cursief, lijsten en codeblokken.
- Streaming rendering wordt gebufferd/throttled zodat niet voor ieder token het volledige chatvenster opnieuw wordt opgebouwd.
- Context is zichtbaar in het AI-paneel: persona, selectie, hoofdstuk, sectie, boek en geraadpleegde verhalen.
- Een tekstselectie krijgt automatisch voorrang als AI-context.
- Gesprekken worden per boek opgeslagen in `.quietwriter/ai_chat.json`.
- Nieuwe knop `Nieuw gesprek` wist alleen de AI-conversatie van het huidige boek.
- Verhalen-RAG gebruikt metadata, tags en full-text als eerste lokale selectiestap.
- Het snelle model kan als bibliothecaris de compacte catalogus in batches lezen en relevante verhalen selecteren.
- Optionele Ollama-embeddings kunnen semantisch vergelijkbare verhalen vinden; embeddings worden persistent gecachet in `.cache/story_embeddings.db`.
- De gebruikte verhalen worden zichtbaar onder het AI-antwoord en in `Context bekijken`.
- Grote verhaalteksten en boekcontext worden begrensd om onnodig grote prompts te voorkomen.
- Denk-/reasoning-output blijft tijdelijk zichtbaar tijdens generatie en verdwijnt zodra het echte antwoord begint.
- AI schrijft nooit rechtstreeks in manuscriptbestanden.
- 5 nieuwe regressietests voor providerselectie, gesprekopslag, RAG-metadata en embeddingcache.
- Totaal: 31 automatische tests geslaagd.

## 0.7.2

- Zijpanelen robuust hersteld na inklappen.
- Hoofdstukrijen beter uitgelijnd met sleepgreep rechts.
- Rode spellinghints losgekoppeld van actieve spellingscontrole.
