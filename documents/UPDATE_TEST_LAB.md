# QuietWriter — lokaal update-testlab (dev.7)

Dit is uitsluitend een testlab en **geen updater voor echte QuietWriter-installaties**. De testserver luistert alleen op `127.0.0.1`; er zijn geen GitHub-releases nodig.

## Twee terminals (in de projectmap)

Terminal 1:

```powershell
python tools/mock_update_server.py
```

Terminal 2:

```powershell
python tools/test_mock_updater.py
python tools/test_mock_updater.py --fault
```

Verwacht: de eerste test toont `Before: 1.5.0` en `After: 1.5.1`, gevolgd door `PASS`. De tweede test toont `Before: 1.5.0`, een gesimuleerde fout, `After: 1.5.0` en `PASS`. Met Ctrl+C stop je de testserver.

De test maakt een tijdelijke map en verwijdert die na afloop. De `QuietWriter.exe` in die map is een **nepbestand**, geen werkende applicatie. De testondertekeningssleutel is vluchtig en wordt niet in QuietWriter vertrouwd. De officiële `update_download.py` blijft uitsluitend officiële HTTPS-GitHub-downloads accepteren. De architectuur van een echte, afzonderlijke Windows-updater en veilige persistentie bij rollback is nog **niet** gerealiseerd.

## Dev.8: portable-updater integration test

Run `python tools/test_windows_portable_updater.py` or add `--fault` to simulate rollback. It targets only temporary, non-executable fixtures. The actual Windows EXE updater, process-exit waiting, trusted signing keys and launch handshake remain unimplemented and must be independently reviewed before production integration.
