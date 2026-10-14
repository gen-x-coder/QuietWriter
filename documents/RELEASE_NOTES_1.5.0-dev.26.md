# QuietWriter 1.5.0-dev.26

Deze ontwikkelversie voegt een zelfstandig bouwbare updater-test-EXE toe. Deze werkt **alleen** op expliciet gemarkeerde, tijdelijke testmappen; nooit op jouw normale QuietWriter-installatie. De Windows-locktest verdraagt een korte vertraging in het vrijgeven van een kernel-lock na een geforceerde processtop. Er is nog geen productie-updater geactiveerd.

## Windows-test

1. `python -m pytest -q tests/current/test_updater_lab_dev26.py tests/current/test_real_transaction_dev25.py tests/current/test_real_transaction_dev24.py`
2. Optioneel: `tools\build_updater_lab.cmd` om `release\updater-lab\QuietWriterUpdaterLab.exe` te maken.
3. Gebruik de EXE **niet** op een echte installatie. Het programma is alleen een testworker.
