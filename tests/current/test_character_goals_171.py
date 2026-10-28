from quietwriter.manuscript_text import count_characters
from quietwriter import i18n

def test_korean_discovery():
    assert ('ko', '한국어') in i18n.available_languages()
    assert i18n.set_locale('ko') == 'ko'
    assert i18n.tr('writing_goal.include_spaces') == '공백 포함'
    i18n.set_locale('nl')

def test_character_count_semantics():
    assert count_characters('안녕 세계', include_spaces=True) == 5
    assert count_characters('안녕 세계', include_spaces=False) == 4
    assert count_characters('한글\n문장', include_spaces=False) == 4

def test_markdown_is_not_counted():
    assert count_characters('**Hallo**', include_spaces=False) == 5
