# QuietWriter 1.5.0-dev.25

Geïsoleerde updaterproeven hebben nu procesbrede vergrendeling voor mapwissel, herstel en afronden. Bij herstel wordt een gecontroleerde kandidaat bewaard; gemanipuleerde bestanden worden geweigerd. De updatefunctie voor echte installaties blijft uitgeschakeld.

Tests: `python -m pytest -q tests/current/test_real_transaction_dev25.py tests/current/test_real_transaction_dev24.py`.
