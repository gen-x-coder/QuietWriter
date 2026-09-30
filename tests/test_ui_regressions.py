import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "quietwriter" / "app.py"
MAIN = ROOT / "quietwriter" / "ui" / "main_window.py"
EDITOR = ROOT / "quietwriter" / "ui" / "editor_page.py"
SETTINGS = ROOT / "quietwriter" / "ui" / "settings_page.py"
BOOK_DETAILS = ROOT / "quietwriter" / "ui" / "book_details.py"
THEMES = ROOT / "quietwriter" / "themes.py"


class UIRegressionTests(unittest.TestCase):
    def test_mainwindow_init_does_not_shadow_translation_function(self):
        tree = ast.parse(MAIN.read_text(encoding="utf-8"))
        main_cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "MainWindow")
        init = next(n for n in main_cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        assigned = set()
        for node in ast.walk(init):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        assigned.add(target.id)
            elif isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                assigned.add(node.target.id)
        self.assertNotIn("tr", assigned, "MainWindow.__init__ must not shadow imported tr()")

    def test_application_font_has_explicit_positive_point_size(self):
        self.assertIn("QFont('Segoe UI', 10)", APP.read_text(encoding="utf-8"))

    def test_qspinbox_is_imported_for_settings_font_size(self):
        source = SETTINGS.read_text(encoding="utf-8")
        self.assertIn("QSpinBox", source.split("from .. import APP_NAME", 1)[0])
        self.assertIn("self.editor_font_size = QSpinBox()", source)

    def test_loaded_chapter_reapplies_saved_writing_font(self):
        source = EDITOR.read_text(encoding="utf-8")
        self.assertIn("self.editor.apply_typography(WritingTypography.from_settings(self.main.settings))", source)

    def test_font_preview_stays_local_and_does_not_touch_manuscript_undo(self):
        source = SETTINGS.read_text(encoding="utf-8")
        start = source.index("    def _preview_appearance(self, *_):")
        end = source.index("    def restore_preview(self):", start)
        block = source[start:end]
        self.assertIn("if theme != self._preview_theme", block)
        self.assertNotIn("apply_writing_font", block)
        self.assertNotIn("apply_manuscript_style", block)
        self.assertIn("self.editor_font.currentTextChanged.connect(self._update_font_preview)", source)
        self.assertIn("self.editor_font_size.valueChanged.connect(self._update_font_preview)", source)
        self.assertNotIn("stylesheet(theme, font)", block)

    def test_left_nav_animation_uses_real_qt_animation_group(self):
        source = MAIN.read_text(encoding="utf-8")
        self.assertIn("self._nav_animation = QParallelAnimationGroup(self)", source)
        self.assertNotIn("self._nav_animation = QParallelAnimationGroup,", source)

    def test_contents_edge_tab_is_overlayed_above_splitter_children(self):
        source = EDITOR.read_text(encoding="utf-8")
        self.assertIn("self.contents_edge_button = QPushButton(self)", source)
        self.assertIn("def _position_contents_edge_button(self):", source)
        self.assertIn("self.contents_edge_button.raise_()", source)

    def test_left_nav_buttons_are_exclusive_navigation_not_toggles(self):
        source = MAIN.read_text(encoding="utf-8")
        self.assertIn("self.nav_selection_group = QButtonGroup(self)", source)
        self.assertIn("self.nav_selection_group.setExclusive(True)", source)
        self.assertIn("self.nav_selection_group.addButton(b)", source)
        self.assertNotIn("b.setAutoExclusive(True)", source)
        self.assertNotIn("self.stories", source)
        self.assertNotIn("StoryBrowser", source)
        self.assertIn("if self.stack.currentWidget() is self.persona:", source)
        self.assertIn("if self.stack.currentWidget() is self.trash:", source)

    def test_contents_edge_tab_is_created_after_splitter_and_has_square_left_edge(self):
        source = EDITOR.read_text(encoding="utf-8")
        splitter_add = source.index("root.addWidget(self.left_split)")
        tab_create = source.index("self.contents_edge_button = QPushButton(self)")
        self.assertGreater(tab_create, splitter_add)
        theme_source = THEMES.read_text(encoding="utf-8")
        self.assertIn("border-top-left-radius: 0px", theme_source)
        self.assertIn("border-bottom-left-radius: 0px", theme_source)

    def test_icons_are_rendered_from_theme_tokens_not_svg_currentcolor(self):
        icon_source = (ROOT / 'quietwriter' / 'icon_theme.py').read_text(encoding='utf-8')
        self.assertIn("theme['muted']", icon_source)
        self.assertIn("theme['accent']", icon_source)
        self.assertIn("theme['disabled']", icon_source)
        self.assertIn('currentColor', icon_source)

    def test_theme_switch_refreshes_icons_and_ai_rich_content(self):
        main_source = MAIN.read_text(encoding='utf-8')
        ai_source = (ROOT / 'quietwriter' / 'ai' / 'ui.py').read_text(encoding='utf-8')
        self.assertIn('self._refresh_theme_icons(theme_name)', main_source)
        self.assertIn('self.editor_page.ai.apply_theme(theme_name)', main_source)
        self.assertIn('def apply_theme(self, theme_name: str):', ai_source)
        self.assertIn('background:{theme["panel"]}', ai_source)

    def test_markdown_renderer_returns_body_fragment_not_nested_html_document(self):
        ai_source = (ROOT / 'quietwriter' / 'ai' / 'ui.py').read_text(encoding='utf-8')
        self.assertIn("re.search(r'<body[^>]*>(.*)</body>'", ai_source)


    def test_refactor_cleanup_uses_direct_signal_declarations(self):
        bookshelf = (ROOT / 'quietwriter' / 'ui' / 'bookshelf.py').read_text(encoding='utf-8')
        search = (ROOT / 'quietwriter' / 'ui' / 'search_panel.py').read_text(encoding='utf-8')
        self.assertNotIn("__import__('PySide6.QtCore').QtCore.Signal", bookshelf)
        self.assertNotIn("__import__('PySide6.QtCore').QtCore.Signal", search)
        self.assertIn('opened = Signal(object)', bookshelf)
        self.assertIn('open_match = Signal(object)', search)

    def test_word_count_updates_do_not_read_every_chapter_on_each_keystroke(self):
        source = EDITOR.read_text(encoding='utf-8')
        start = source.index('    def update_counts(self, saved=False):')
        end = source.index('    def add_menu(self):', start)
        block = source[start:end]
        self.assertNotIn('read_chapter(', block)
        self.assertIn('_chapter_word_counts', block)
        self.assertIn('def _rebuild_word_count_cache(self):', source)

    def test_book_export_uses_pending_cover_state(self):
        source = BOOK_DETAILS.read_text(encoding='utf-8')
        self.assertIn('def _current_cover_for_metadata(self):', source)
        self.assertIn("if self.pending_cover == '__REMOVE__':", source)
        self.assertIn('image_ref = self._image_ref_for(slug)', source)

    def test_history_computes_today_label_once_per_refresh(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'history_panel.py').read_text(encoding='utf-8')
        self.assertIn('today_label = self._format_stamp(datetime.now().isoformat())[0]', source)
        self.assertIn("group = tr('history.today', 'Vandaag') if date_label == today_label else date_label", source)


class PageArchitectureTests(unittest.TestCase):
    def test_story_subsystem_is_removed(self):
        source = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'quietwriter').rglob('*.py'))
        storage = (ROOT / 'quietwriter' / 'storage.py').read_text(encoding='utf-8')
        self.assertNotIn('StoryIndex', source)
        self.assertNotIn('StoryBrowser', source)
        self.assertNotIn('stories_dir', storage)
        self.assertFalse((ROOT / 'quietwriter' / 'story_index.py').exists())

    def test_details_and_settings_are_pages(self):
        self.assertIn('class BookDetailsPage(QWidget):', BOOK_DETAILS.read_text(encoding='utf-8'))
        self.assertIn('class SettingsPage(QWidget):', SETTINGS.read_text(encoding='utf-8'))
        all_ui = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'quietwriter' / 'ui').glob('*.py'))
        self.assertNotIn('class BookDetailsDialog', all_ui)
        self.assertNotIn('class SettingsDialog', all_ui)


class SettingsNavigationArchitectureTests(unittest.TestCase):
    def test_settings_use_left_navigation_and_stacked_pages(self):
        source = SETTINGS.read_text(encoding='utf-8')
        block = source[source.index('class SettingsPage(QWidget):'):source.index('    def _preview_appearance', source.index('class SettingsPage(QWidget):'))]
        self.assertIn("nav.setObjectName('settingsSidebar')", block)
        self.assertIn('self.pages = CurrentPageStack()', block)
        self.assertIn("button.setObjectName('settingsNavButton')", block)
        self.assertNotIn('self.tabs = QTabWidget()', block)


class UIModuleArchitectureTests(unittest.TestCase):
    def test_app_module_is_only_bootstrap(self):
        source = APP.read_text(encoding='utf-8')
        self.assertNotIn('class MainWindow', source)
        self.assertIn('from .ui.main_window import MainWindow', source)
        self.assertLess(len(source.splitlines()), 100)

    def test_large_ui_components_live_in_separate_modules(self):
        expected = {
            'main_window.py': 'class MainWindow',
            'bookshelf.py': 'class StartPage',
            'book_details.py': 'class BookDetailsPage',
            'settings_page.py': 'class SettingsPage',
            'persona_page.py': 'class PersonaPage',
            'trash_page.py': 'class TrashPage',
            'editor_page.py': 'class EditorPage',
            'manuscript_tree.py': 'class ManuscriptTree',
            'search_panel.py': 'class SearchPanel',
            'spell_panel.py': 'class SpellPanel',
            'history_panel.py': 'class HistoryPanel',
        }
        ui = ROOT / 'quietwriter' / 'ui'
        for filename, marker in expected.items():
            path = ui / filename
            self.assertTrue(path.exists(), filename)
            self.assertIn(marker, path.read_text(encoding='utf-8'))


class ManuscriptFormattingArchitectureTests(unittest.TestCase):
    def test_editor_keeps_plain_markdown_source(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
        self.assertIn('self.setAcceptRichText(False)', source)
        self.assertIn('SelectionToolbar()', source)
        self.assertIn('self._selection_timer.setInterval(1000)', source)
        highlighter = (ROOT / 'quietwriter' / 'ui' / 'presentation_highlighter.py').read_text(encoding='utf-8')
        self.assertIn("if kind == 'scene':", highlighter)
        self.assertIn('fmt.setFontPointSize(1.0)', highlighter)
        self.assertNotIn('fmt.setFontStretch(1)', highlighter)
        self.assertNotIn('_marker_selection', source)

    def test_selection_toolbar_is_separate_ui_module(self):
        path = ROOT / 'quietwriter' / 'ui' / 'selection_toolbar.py'
        self.assertTrue(path.exists())
        source = path.read_text(encoding='utf-8')
        self.assertIn('class SelectionToolbar(QFrame):', source)
        self.assertIn("('bold', 'B'", source)
        self.assertIn("('underline', 'U'", source)


    def test_markdown_presentation_is_non_destructive_and_shared_with_spelling(self):
        highlighter = (ROOT / 'quietwriter' / 'ui' / 'presentation_highlighter.py').read_text(encoding='utf-8')
        editor = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
        editor_page = EDITOR.read_text(encoding='utf-8')
        self.assertIn('class ManuscriptHighlighter(QSyntaxHighlighter):', highlighter)
        self.assertIn('self.presentation_highlighter = ManuscriptHighlighter(self)', editor)
        self.assertIn('self.highlighter = self.editor.presentation_highlighter', editor_page)
        self.assertIn('self._apply_spelling(mask_image_paths(text), marker_ranges)', highlighter)
        self.assertFalse((ROOT / 'quietwriter' / 'spellcheck.py').exists())

    def test_selection_toolbar_uses_large_format_controls(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'selection_toolbar.py').read_text(encoding='utf-8')
        self.assertIn('btn.setFixedSize(44, 42)', source)
        self.assertIn('font.setPointSize(17', source)

    def test_manuscript_style_settings_are_independent(self):
        source = SETTINGS.read_text(encoding='utf-8')
        for key in ('manuscript_line_spacing', 'manuscript_indent', 'manuscript_paragraph_spacing', 'smart_quotes'):
            self.assertIn(key, source)
        self.assertIn('apply_manuscript_style', MAIN.read_text(encoding='utf-8'))

    def test_editor_owns_plain_enter_and_preserves_blank_block_height(self):
        source = (ROOT / 'quietwriter' / 'ui' / 'manuscript_editor.py').read_text(encoding='utf-8')
        self.assertIn('cursor.insertBlock()', source)
        self.assertIn('Qt.Key_Return, Qt.Key_Enter', source)
        self.assertIn('QTextBlockFormat.MinimumHeight', source)
        self.assertIn('QFontMetricsF(self.document().defaultFont()).lineSpacing()', source)


if __name__ == "__main__":
    unittest.main()


def test_selection_toolbar_buttons_are_checkable_and_receive_states():
    from pathlib import Path
    source = Path('quietwriter/ui/selection_toolbar.py').read_text(encoding='utf-8')
    assert 'btn.setCheckable(True)' in source
    assert 'def set_states' in source


def test_highlighter_composes_styles_before_hiding_markers():
    from pathlib import Path
    source = Path('quietwriter/ui/presentation_highlighter.py').read_text(encoding='utf-8')
    assert 'def _composed_format' in source
    assert "if 'bold' in styles" in source
    assert "if 'italic' in styles" in source
