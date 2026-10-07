# QuietWriter 1.2.6

Deze onderhoudsrelease corrigeert de visuele regressie uit 1.2.5 waarbij verborgen open-puntmarkeringen omliggende manuscripttekst konden laten overlappen.

- Open-puntmarkeringen hebben nu een eigen verborgen stijl.
- De samendrukking gebruikt de werkelijke tekenbreedte van het kleine markerfont in plaats van een vaste negatieve afstand.
- Gewone verborgen Markdown-syntax, waaronder `**` voor vet, wordt hierdoor niet langer mee samengedrukt.

De bestaande bescherming rond Open punten, schone exports en clipboardgedrag uit 1.2.5 blijft ongewijzigd.
