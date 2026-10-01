# Review notes 0.36.9

## Doel
De schaal voor de globale tekstbreedte één stap ruimer maken en een vijfde uiterste stand toevoegen, zonder manuscript- of exportgedrag te wijzigen.

## Te controleren
- Editor en Instellingen tonen in deze volgorde: Extra smal, Smal, Normaal, Breed, Extra breed.
- Visuele mapping is 720 / 850 / 1000 / 1180 / 1360 px; deze waarden zijn intern en worden niet aan gebruikers getoond.
- Normaal is nu even breed als Breed in 0.36.8.
- Extra breed is zichtbaar ruimer dan de oude maximale stand.
- De instelling blijft globaal per DEV/PROD-profiel en niet per boek.
- Wijzigen maakt het manuscript niet inhoudelijk dirty en verandert export niet.
- Een bestaande opgeslagen waarde `normal` blijft semantisch `normal` en gebruikt dus de nieuwe ruimere standaard.
- Nederlandse en Engelse labels zijn volledig vertaald.
