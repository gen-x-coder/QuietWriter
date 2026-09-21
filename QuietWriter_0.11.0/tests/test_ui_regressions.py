import ast
import unittest
from pathlib import Path


class UIRegressionTests(unittest.TestCase):
    def test_mainwindow_init_does_not_shadow_translation_function(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        tree = ast.parse(app_path.read_text(encoding="utf-8"))
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
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        self.assertIn("QFont('Segoe UI', 10)", source)

    def test_qspinbox_is_imported_for_settings_font_size(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        self.assertIn("QSpinBox", source.split("from . import APP_NAME", 1)[0])
        self.assertIn("self.editor_font_size = QSpinBox()", source)

    def test_loaded_chapter_reapplies_saved_writing_font(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        self.assertIn("self.editor.apply_typography(WritingTypography.from_settings(self.main.settings))", source)
        self.assertIn("WritingTypography.from_settings(self.main.settings)", source)

    def test_font_preview_does_not_repolish_application_for_every_font_change(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        start = source.index("    def _preview_appearance(self, *_):")
        end = source.index("    def restore_preview(self):", start)
        block = source[start:end]
        self.assertIn("if theme != self._preview_theme", block)
        self.assertIn("win.apply_writing_font(font, size)", block)
        self.assertNotIn("stylesheet(theme, font)", block)


    def test_left_nav_animation_uses_real_qt_animation_group(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        self.assertIn("self._nav_animation = QParallelAnimationGroup(self)", source)
        self.assertNotIn("self._nav_animation = QParallelAnimationGroup,", source)

    def test_contents_edge_tab_is_overlayed_above_splitter_children(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        self.assertIn("self.contents_edge_button = QPushButton(self)", source)
        self.assertIn("def _position_contents_edge_button(self):", source)
        self.assertIn("self.contents_edge_button.raise_()", source)


    def test_left_nav_buttons_are_exclusive_navigation_not_toggles(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        source = app_path.read_text(encoding="utf-8")
        self.assertIn("b.setAutoExclusive(True)", source)
        self.assertNotIn("self.stories", source)
        self.assertNotIn("StoryBrowser", source)
        self.assertIn("if self.stack.currentWidget() is self.persona:", source)
        self.assertIn("if self.stack.currentWidget() is self.trash:", source)

    def test_contents_edge_tab_is_created_after_splitter_and_has_square_left_edge(self):
        app_path = Path(__file__).resolve().parents[1] / "quietwriter" / "app.py"
        theme_path = Path(__file__).resolve().parents[1] / "quietwriter" / "themes.py"
        source = app_path.read_text(encoding="utf-8")
        splitter_add = source.index("root.addWidget(self.left_split)")
        tab_create = source.index("self.contents_edge_button = QPushButton(self)")
        self.assertGreater(tab_create, splitter_add)
        theme_source = theme_path.read_text(encoding="utf-8")
        self.assertIn("border-top-left-radius: 0px", theme_source)
        self.assertIn("border-bottom-left-radius: 0px", theme_source)

    def test_icons_are_rendered_from_theme_tokens_not_svg_currentcolor(self):
        root = Path(__file__).resolve().parents[1]
        icon_source = (root / 'quietwriter' / 'icon_theme.py').read_text(encoding='utf-8')
        self.assertIn("theme['muted']", icon_source)
        self.assertIn("theme['accent']", icon_source)
        self.assertIn("theme['disabled']", icon_source)
        self.assertIn('currentColor', icon_source)

    def test_theme_switch_refreshes_icons_and_ai_rich_content(self):
        root = Path(__file__).resolve().parents[1]
        app_source = (root / 'quietwriter' / 'app.py').read_text(encoding='utf-8')
        ai_source = (root / 'quietwriter' / 'ai' / 'ui.py').read_text(encoding='utf-8')
        self.assertIn('self._refresh_theme_icons(theme_name)', app_source)
        self.assertIn('self.editor_page.ai.apply_theme(theme_name)', app_source)
        self.assertIn('def apply_theme(self, theme_name: str):', ai_source)
        self.assertIn('background:{theme["panel"]}', ai_source)

    def test_markdown_renderer_returns_body_fragment_not_nested_html_document(self):
        root = Path(__file__).resolve().parents[1]
        ai_source = (root / 'quietwriter' / 'ai' / 'ui.py').read_text(encoding='utf-8')
        self.assertIn("re.search(r'<body[^>]*>(.*)</body>'", ai_source)


if __name__ == "__main__":
    unittest.main()

class PageArchitectureTests(unittest.TestCase):
    def test_story_subsystem_is_removed(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / 'quietwriter' / 'app.py').read_text(encoding='utf-8')
        storage = (root / 'quietwriter' / 'storage.py').read_text(encoding='utf-8')
        self.assertNotIn('StoryIndex', source)
        self.assertNotIn('StoryBrowser', source)
        self.assertNotIn('stories_dir', storage)
        self.assertFalse((root / 'quietwriter' / 'story_index.py').exists())

    def test_details_and_settings_are_pages(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / 'quietwriter' / 'app.py').read_text(encoding='utf-8')
        self.assertIn('class BookDetailsPage(QWidget):', source)
        self.assertIn('class SettingsPage(QWidget):', source)
        self.assertNotIn('class BookDetailsDialog', source)
        self.assertNotIn('class SettingsDialog', source)
