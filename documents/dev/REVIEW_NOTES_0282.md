# Review notes 0.28.2

Lees eerst `TUSSENTIJDS_RAPPORT_0282.md`. Deze release is bewust een UI/storage-grensrelease, geen nieuwe feature.

Belangrijkste reviewvraag: kan **enige** schrijffout nog leiden tot navigeren of afsluiten terwijl dirty gebruikersinvoer alleen in RAM staat?

Tweede reviewvraag: als een open boek extern een toekomstig formaat krijgt, staat lokale tekst aantoonbaar in History **vóór** QuietWriter het incompatibele boek loskoppelt, en blijft het live toekomstige manifest volledig onaangeraakt?

Voer bij voorkeur de twaalf runtimegevallen uit het tussentijds rapport uit en herhaal de relevante failure-injections uit ronde 10.
