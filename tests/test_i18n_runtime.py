from quietwriter.i18n import current_locale, set_locale, tr


def test_process_locale_switches_translations_and_falls_back_safely():
    original = current_locale()
    try:
        assert set_locale('en') == 'en'
        assert tr('common.save') == 'Save'
        assert set_locale('nl_NL') == 'nl'
        assert tr('common.save') == 'Opslaan'
        assert set_locale('does-not-exist') == 'nl'
    finally:
        set_locale(original)
