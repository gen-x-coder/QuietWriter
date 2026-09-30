import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PublicationUiRegressionTests(unittest.TestCase):
    def test_changed_signal_adapters_discard_widget_payloads(self):
        publication_dir = ROOT / 'quietwriter' / 'ui' / 'publication'
        sources = '\n'.join(path.read_text(encoding='utf-8') for path in publication_dir.glob('*.py'))
        # A zero-argument custom Signal must never be connected directly to a
        # Qt signal such as textEdited(str), toggled(bool) or currentTextChanged(str).
        self.assertNotIn('.connect(self.changed.emit)', sources)
        self.assertIn('lambda *_: self.changed.emit()', sources)

    def test_add_flyout_does_not_keep_deleted_qt_wrapper(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
        self.assertNotIn('self._add_flyout', source)
        self.assertIn('QFrame(self, Qt.Popup | Qt.FramelessWindowHint)', source)
        self.assertIn('Qt.WA_DeleteOnClose', source)

    def test_publication_structure_has_three_collapsible_groups(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
        self.assertIn("make_group(tr('editor.tree.front', 'Voorwerk'), 'front', editable=True)", source)
        self.assertIn("make_group(tr('editor.tree.book', 'Boek'), 'body')", source)
        self.assertIn("make_group(tr('editor.tree.back', 'Achterwerk'), 'back', editable=True)", source)
        self.assertIn('ChildIndicatorPolicy.ShowIndicator', source)
        self.assertIn("('manuscript_group', kind)", source)
        tree_source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_tree.py').read_text(encoding='utf-8')
        self.assertIn('setRootIsDecorated(True)', tree_source)
        self.assertIn('setItemsExpandable(True)', tree_source)

    def test_publication_groups_are_always_visible(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'editor_page.py').read_text(encoding='utf-8')
        self.assertNotIn('has_publication_structure', source)
        self.assertIn("make_group(tr('editor.tree.front', 'Voorwerk'), 'front', editable=True)", source)
        self.assertIn("make_group(tr('editor.tree.book', 'Boek'), 'body')", source)
        self.assertIn("make_group(tr('editor.tree.back', 'Achterwerk'), 'back', editable=True)", source)

    def test_contents_page_uses_explicit_radio_styling_and_top_aligned_preview(self):
        page_source = (ROOT / 'quietwriter' / 'ui' / 'publication' / 'contents_page.py').read_text(encoding='utf-8')
        theme_source = (ROOT / 'quietwriter' / 'themes.py').read_text(encoding='utf-8')
        self.assertIn("setObjectName('publicationRadio')", page_source)
        self.assertIn('Qt.AlignLeft | Qt.AlignTop', page_source)
        self.assertIn('QRadioButton#publicationRadio::indicator:checked', theme_source)


try:
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.publication.copyright_page import CopyrightPage
    from quietwriter.ui.publication.publication_editor import SimpleStructuredPage
    HAVE_QT = True
except Exception:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, 'PySide6 is niet beschikbaar in deze testomgeving')
class PublicationQtSignalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_copyright_changed_accepts_payload_signals(self):
        page = CopyrightPage()
        calls = []
        page.changed.connect(lambda: calls.append(True))
        page.author.textEdited.emit('Auteur')
        page.edition.currentTextChanged.emit('Tweede editie')
        first_cb = next(iter(page.clauses.values()))[0]
        first_cb.toggled.emit(True)
        self.assertEqual(len(calls), 3)

    def test_simple_structured_page_changed_accepts_text_payload(self):
        page = SimpleStructuredPage('Test', [('title', 'Titel')])
        calls = []
        page.changed.connect(lambda: calls.append(True))
        page._edits['title'].textEdited.emit('Nieuwe titel')
        self.assertEqual(calls, [True])


if __name__ == '__main__':
    unittest.main()
