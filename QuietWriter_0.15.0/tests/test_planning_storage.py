import json
import tempfile
import unittest
from pathlib import Path

from quietwriter.planning_models import Character, Relation, Scene
from quietwriter.planning_storage import PlanningStore
from quietwriter.revisions import ExternalModificationError
from quietwriter.storage import Library


class PlanningStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.library = Library(Path(self.tmp.name))
        self.book = self.library.create_book('Testboek')
        self.library.track_book(self.book)
        self.store = PlanningStore(self.library)

    def tearDown(self):
        self.tmp.cleanup()

    def test_character_roundtrip_preserves_structured_ai_fields_and_relations(self):
        jan = Character(name='Jan', role='hoofdpersoon', personality='rustig', motivation='zijn zoon beschermen', voice='kort en direct')
        kees = Character(name='Kees', role='zoon')
        jan.relations.append(Relation(target_id=kees.id, type='vader van', inverse_type='zoon van'))
        self.store.save_characters(self.book, [jan, kees])
        loaded = self.store.load_characters(self.book)
        self.assertEqual(loaded[0].personality, 'rustig')
        self.assertEqual(loaded[0].motivation, 'zijn zoon beschermen')
        self.assertEqual(loaded[0].voice, 'kort en direct')
        self.assertEqual(loaded[0].relations[0].target_id, kees.id)

    def test_scene_roundtrip_uses_ids_not_names(self):
        char = Character(name='Bertha')
        scene = Scene(title='Ontmoeting', chapter_id=self.book.sections[0].chapters[0].id, character_ids=[char.id], location='Delft')
        self.store.save_scenes(self.book, [scene])
        loaded = self.store.load_scenes(self.book)[0]
        self.assertEqual(loaded.character_ids, [char.id])
        self.assertEqual(loaded.chapter_id, self.book.sections[0].chapters[0].id)

    def test_notes_are_plain_markdown(self):
        text = '# Idee\n\n**Belangrijk** en vrij geschreven.'
        self.store.save_notes(self.book, text)
        self.assertEqual(self.store.load_notes(self.book), text)

    def test_external_planning_change_is_detected_before_overwrite(self):
        self.store.save_notes(self.book, 'eerste versie')
        path = self.book.path / 'planning' / 'notes.md'
        path.write_text('extern gewijzigd', encoding='utf-8')
        with self.assertRaises(ExternalModificationError):
            self.store.save_notes(self.book, 'lokale wijziging')
        self.assertEqual(path.read_text(encoding='utf-8'), 'extern gewijzigd')

    def test_local_planning_recovery_snapshot_can_override_one_planning_file(self):
        self.store.save_notes(self.book, 'diskversie')
        version = self.library.create_version_with_file_overrides(
            self.book, {'planning/notes.md': 'lokale nog niet opgeslagen versie'}, kind='conflict_local'
        )
        snap = Path(version['path']) / 'planning' / 'notes.md'
        self.assertEqual(snap.read_text(encoding='utf-8'), 'lokale nog niet opgeslagen versie')
        self.assertEqual((self.book.path / 'planning' / 'notes.md').read_text(encoding='utf-8'), 'diskversie')

    def test_planning_files_are_part_of_book_revision_even_before_they_exist(self):
        rev = self.library.capture_revision(self.book)
        self.assertIn('planning/characters.json', rev.files)
        self.assertIn('planning/outline.json', rev.files)
        self.assertIn('planning/notes.md', rev.files)
        self.assertIsNone(rev.files['planning/notes.md'])


if __name__ == '__main__':
    unittest.main()
