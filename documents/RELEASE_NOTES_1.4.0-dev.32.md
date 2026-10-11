# QuietWriter 1.4.0-dev.32 — Eén notitie, één wijziging

Notities mogen van alles bevatten, maar het bewerken van één kaart mag nooit de kaart ernaast raken. QuietWriter controleert daarom extra nauwkeurig of de geselecteerde notitie nog overeenkomt met de bron. Een ongeldige selectie wordt geweigerd in plaats van een ander stuk tekst aan te passen.

Ook een Markdown-kopje zonder titel wordt niet meer als losse notitie getoond. Extra regressietests bewaken het behoud van omliggende tekst, inclusief oudere notities met Windows-regeleinden.

De bestaande opslag in `notes.md` blijft intact. Back-ups en manuscriptopslag zijn niet gewijzigd.
