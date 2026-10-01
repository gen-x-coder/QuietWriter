import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ReviewDataIntegrity0215Tests(unittest.TestCase):
    def source(self, relative):
        return (ROOT / relative).read_text(encoding='utf-8')

    def test_text_prompt_is_quietwriter_owned_and_localized(self):
        source = self.source('quietwriter/ui/dialogs.py')
        self.assertNotIn('QInputDialog,', source)
        self.assertNotIn(' QInputDialog', source.split('from ..i18n import tr', 1)[0])
        self.assertIn('QDialogButtonBox.Save | QDialogButtonBox.Cancel', source)
        self.assertIn("tr('common.save', 'Opslaan')", source)
        self.assertIn("tr('common.cancel', 'Annuleren')", source)

    def test_chapter_context_menu_exposes_delete(self):
        source = self.source('quietwriter/ui/editor_page.py')
        self.assertIn("delete_action = menu.addAction(tr('common.delete', 'Verwijderen'))", source)
        self.assertIn('self.delete_chapter(chapter_id)', source)
        self.assertIn('def delete_chapter(self, chapter_id: str):', source)

    def test_publication_same_book_does_not_reset_pending_item(self):
        source = self.source('quietwriter/ui/publication/publication_editor.py')
        self.assertIn('if self.book is book:', source)
        self.assertIn('return True', source)
        self.assertIn('if self.book and self.save_pending() is False:', source)

    def test_character_collect_uses_candidate_copy(self):
        source = self.source('quietwriter/ui/planning/characters_page.py')
        self.assertIn('c = copy.deepcopy(self.character)', source)
        self.assertIn("result = self.owner.persist_characters(candidate)", source)
        self.assertIn("if result == 'failed':", source)
        self.assertIn("if result == 'disk':", source)
        self.assertIn('if not self.owner.remove_character_from_scenes(cid):', source)

    def test_outline_rolls_back_failed_add_edit_and_shows_orphans(self):
        source = self.source('quietwriter/ui/planning/outline_page.py')
        self.assertIn("tr('planning.outline.orphaned', 'Verweesde scènes')", source)
        self.assertGreaterEqual(source.count('before=copy.deepcopy(self.scenes)'), 2)
        self.assertGreaterEqual(source.count("if result == 'failed': self.scenes=before"), 2)

    def test_planning_pending_includes_character_draft(self):
        source = self.source('quietwriter/ui/planning/planning_page.py')
        self.assertIn('if self.characters_page.save_pending() is False:', source)
        characters = self.source('quietwriter/ui/planning/characters_page.py')
        self.assertIn('def save_pending(self):', characters)
        self.assertIn("tr('common.dont_save', 'Niet opslaan')", characters)

    def test_book_delete_is_guarded_before_trash_move(self):
        details = self.source('quietwriter/ui/book_details.py')
        main = self.source('quietwriter/ui/main_window.py')
        self.assertIn('self.before_delete(self.book) is False', details)
        self.assertIn('before_delete=self._prepare_book_delete', main)
        self.assertIn('if self.planning_page.save_pending() is False:', main)
        self.assertIn('if self.editor_page.save() is False:', main)

    def test_character_relation_label_uses_precomputed_translation(self):
        source = self.source('quietwriter/ui/planning/characters_page.py')
        self.assertIn("unknown_label = tr('planning.characters.unknown', 'Onbekend personage')", source)
        self.assertNotIn("names.get(relation.target_id, tr('planning.characters.unknown'", source)

    def test_characters_page_parses_as_project_python_312(self):
        source = self.source('quietwriter/ui/planning/characters_page.py')
        ast.parse(source, feature_version=(3, 12))


if __name__ == '__main__':
    unittest.main()
