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

    def test_font_preview_does_not_repolish_application_for_every_font_change(self):
        source = SETTINGS.read_text(encoding="utf-8")
        start = source.index("    def _preview_appearance(self, *_):")
        end = source.index("    def restore_preview(self):", start)
        block = source[start:end]
        self.assertIn("if theme != self._preview_theme", block)
        self.assertIn("win.apply_writing_font(font, size)", block)
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
        self.assertIn("b.setAutoExclusive(True)", source)
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
        self.assertIn('self.pages = QStackedWidget()', block)
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


if __name__ == "__main__":
    unittest.main()
