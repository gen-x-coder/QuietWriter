# Tussentijds rapport 0.34.9

0.34.9 rondt de expliciete opt-in voor hoofdstukplanning af. De melding heeft een **Begrepen**-actie die `ai_use_chapter_planning=False` opslaat zonder de checkbox tijdelijk aan te zetten.

De instellingencontrole is tolerant voor lichte testdoubles zonder `contains()`. Productgedrag met echte QSettings blijft gelijk. De foutieve `isVisible()`-assertie is vervangen door een controle op de eigen hidden-state van de notice-row.

Lokale standaardrun: 186 geslaagd, 14 overgeslagen (waaronder de nieuwe Qt-runtimecheck). Legacy: 424 geslaagd, 24 overgeslagen, 280 subtests; alleen de twee bekende fontresource-tests falen. De nieuwe Qt-check moet door Claude met echte PySide6 worden uitgevoerd.
