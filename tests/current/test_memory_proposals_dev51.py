from quietwriter.ai.memory_suggestions import extract_memory_suggestions, visible_stream_text


def test_proposal_roundtrip():
    text = 'Dit is mijn analyse.\n[[QW_MEMORY|canon]]Mara woont in Delft.[[/QW_MEMORY]]'
    visible, proposals = extract_memory_suggestions(text)
    assert visible == 'Dit is mijn analyse.'
    assert len(proposals) == 1
    assert proposals[0].section_key == 'canon'
    assert proposals[0].text == 'Mara woont in Delft.'


def test_whitespace_and_case_tolerance():
    response = 'Antwoord.\n[[ qw_memory | decisions ]] Verteller is Mara. [[ /qw_memory ]]'
    visible, proposals = extract_memory_suggestions(response)
    assert visible == 'Antwoord.'
    assert [(p.section_key, p.text) for p in proposals] == [('decisions', 'Verteller is Mara.')]


def test_invalid_is_hidden():
    source = '[[QW_MEMORY|fake]]Onbekend[[/QW_MEMORY]]'
    assert extract_memory_suggestions(source) == ('', [])


def test_at_most_two_proposals():
    s = 'A' + ''.join(f'[[QW_MEMORY|canon]]Feit {i}[[/QW_MEMORY]]' for i in range(3))
    text, proposals = extract_memory_suggestions(s)
    assert len(proposals) == 2
    assert 'Feit 2' not in text


def test_streaming_tag_never_flashes():
    full = 'Dit is het antwoord.\n[[QW_MEMORY|canon]]Onthoud dit[[/QW_MEMORY]]'
    for n in range(len(full) + 1):
        visible = visible_stream_text(full[:n])
        assert '[[' not in visible
    assert visible_stream_text('Een normale [link]') == 'Een normale [link]'
