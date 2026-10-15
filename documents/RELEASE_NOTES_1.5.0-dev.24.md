# QuietWriter 1.5.0-dev.24

De updater-testomgeving combineert nu een extern proces, crashbestendige mapwissel en echte EXE-gezondheidscontrole. De broninstallaties blijven onaangeroerd. Dit is geen productie-updatefunctie.

Technisch: nieuw `update_real_transaction_lab.py`, `real_update_transaction_worker.py` en `test_real_update_transaction.py`; nieuwe subprocess- en rollbacktests.
