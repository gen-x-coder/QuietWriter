import os
import tempfile
from pathlib import Path

import pytest

from quietwriter.spell_engine import WordDictionary


def _write_dic(root: Path, words, *, encoding='utf-8', aff_encoding=None):
    dic = root / 'test.dic'
    payload = str(len(words)) + '\n' + '\n'.join(words) + '\n'
    dic.write_bytes(payload.encode(encoding))
    if aff_encoding:
        (root / 'test.aff').write_bytes(f'SET {aff_encoding}\n'.encode('ascii'))
    return dic


def test_capitalized_words_are_checked_instead_of_blanket_accepted():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = WordDictionary()
        d.load_dic(_write_dic(root, ['deze', 'zin']))
        assert d.known('Deze') is True
        assert d.known('Dees') is False
        assert d.known('Xyzblah') is False
        assert [row[0] for row in d.misspellings('Dees zin. Xyzblah.')] == ['Dees', 'Xyzblah']


def test_plain_dictionary_lookup_remains_case_insensitive():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = WordDictionary()
        d.load_dic(_write_dic(root, ['quietwriter', 'nederlands']))
        assert d.known('QuietWriter') is True
        assert d.known('Nederlands') is True


def test_dic_uses_encoding_declared_by_aff_file():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = WordDictionary()
        dic = _write_dic(
            root,
            ['café', 'crème', 'naïef'],
            encoding='iso-8859-1',
            aff_encoding='ISO8859-1',
        )
        d.load_dic(dic)
        assert {'café', 'crème', 'naïef'} <= d.words
        assert 'caf' not in d.words
        assert 'crme' not in d.words
        assert 'naef' not in d.words
        assert d.known('Café') is True


def test_dic_without_aff_falls_back_to_latin1_without_dropping_bytes():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = WordDictionary()
        dic = _write_dic(root, ['café'], encoding='iso-8859-1')
        d.load_dic(dic)
        assert 'café' in d.words
        assert d.known('Café') is True


def test_global_spell_actions_continue_from_previous_text_offset():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    QtWidgets = pytest.importorskip('PySide6.QtWidgets')
    pytest.importorskip('PySide6.QtGui')
    from quietwriter.ui.spell_panel import SpellPanel

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    class Highlighter:
        def rehighlight(self):
            pass

    class Page:
        def __init__(self, dictionary):
            self.dictionary = dictionary
            self.chapter_title = QtWidgets.QLineEdit('')
            self.editor = QtWidgets.QTextEdit()
            self.editor.setPlainText('fout fout ander laatste')
            self.highlighter = Highlighter()

        def rename_current(self):
            pass

    for action in ('ignore_all', 'ignore_always', 'add_personal'):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = WordDictionary()
            d.load_dic(_write_dic(root, ['goed']))
            page = Page(d)
            panel = SpellPanel(page)
            assert [row[1] for row in panel.rows] == ['fout', 'fout', 'ander', 'laatste']
            panel.index = 1
            panel.show_current()
            getattr(panel, action)()
            assert [row[1] for row in panel.rows] == ['ander', 'laatste']
            assert panel.index == 0
            assert panel.word.text() == 'ander'
            panel.deleteLater()
            page.editor.deleteLater()
            page.chapter_title.deleteLater()
    app.processEvents()
