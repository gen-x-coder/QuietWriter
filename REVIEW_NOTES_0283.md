# Review notes 0.28.3

Deze release sluit uitsluitend de twee resterende UI-randgevallen uit de runtime-review van 0.28.2.

## Te reviewen
- `MainWindow.preserve_local_and_close_future_book`: snapshot moet vóór detach komen; bij snapshotfailure geen detach.
- Planning/Boekprofiel/Boekgeheugen: `FutureBookFormatError` moet via die centrale route gaan en exacte lokale invoer bewaren.
- Boekdetails: `save()` is boolean; pending form state blokkeert navigatie/boekenplank/close bij mislukte save.
- Future-format Boekdetails gebruikt recovery-state en mag het live toekomstige manifest niet schrijven.

Zie `TUSSENTIJDS_RAPPORT_0283.md` voor tien runtimegevallen. Als deze groen zijn, is 0.28.x afgesloten en kan 0.29.0 Integriteit & Herstel-UI starten.
