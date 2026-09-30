from quietwriter.ai.prompting import build_system_prompt


def test_system_prompt_keeps_automatic_chapter_planning_separate_from_manual_selection():
    prompt = build_system_prompt(
        persona='Persona',
        book_profile='Profiel',
        book_memory='Geheugen',
        planning_text='# Geselecteerde scène\nHANDMATIG_UNIEK',
        chapter_planning_text='# Planning van dit hoofdstuk\nAUTOMATISCH_UNIEK',
        context_label='Huidig hoofdstuk',
        context_text='MANUSCRIPT_UNIEK',
    )
    assert 'PLANNING VAN HET HUIDIGE HOOFDSTUK' in prompt
    assert 'AUTOMATISCH_UNIEK' in prompt
    assert 'GESELECTEERDE PLANNINGCONTEXT' in prompt
    assert 'HANDMATIG_UNIEK' in prompt
    assert prompt.index('PLANNING VAN HET HUIDIGE HOOFDSTUK') < prompt.index('GESELECTEERDE PLANNINGCONTEXT')


def test_system_prompt_omits_chapter_planning_when_toggle_supplies_no_text():
    prompt = build_system_prompt(
        persona='Persona', book_profile='Profiel', book_memory='Geheugen',
        planning_text='', chapter_planning_text='',
        context_label='Huidig hoofdstuk', context_text='Tekst',
    )
    assert 'PLANNING VAN HET HUIDIGE HOOFDSTUK' in prompt
    assert '[niet meegestuurd]' in prompt
    assert 'Gebruik de opgeslagen Planning van het huidige hoofdstuk als aanvullend plan' not in prompt
