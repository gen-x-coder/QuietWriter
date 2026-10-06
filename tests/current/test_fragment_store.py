import tempfile
import unittest
from pathlib import Path

from quietwriter.fragment_store import (
    FragmentExternalModificationError,
    FragmentFormatError,
    FragmentStore,
    FutureFragmentFormatError,
)
from quietwriter.storage import CorruptSourceError


class FragmentStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = FragmentStore(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_roundtrip_preserves_markdown_and_complex_anchor_text(self):
        text = '**Vet** en *cursief*.\n\n***\n\nHarde\u00a0spatie.'
        fragment = self.store.create(
            text,
            source_book_id='book-1',
            source_book_title='Boek: "Een"',
            source_chapter_id='chapter-1',
            source_chapter_title='Hoofdstuk 1',
            source_before='Hij zei: "kom mee".\nTweede regel.',
            source_after="Daarna: 'stilte'.",
            title='Alternatieve ontmoeting',
            note='Later misschien gebruiken',
            tags=['dialoog', 'Later', 'dialoog'],
            fragment_id='fragment-1',
            created_at='2026-10-04T20:00:00+02:00',
        )
        loaded = self.store.load(fragment.id)
        self.assertEqual(loaded.text, text)
        self.assertEqual(loaded.source_before, 'Hij zei: "kom mee".\nTweede regel.')
        self.assertEqual(loaded.source_after, "Daarna: 'stilte'.")
        self.assertEqual(loaded.tags, ('dialoog', 'Later'))

    def test_one_fragment_per_file_and_no_monolithic_index(self):
        first = self.store.create('eerste', fragment_id='one')
        second = self.store.create('tweede', fragment_id='two')
        self.assertTrue(self.store.path_for(first.id).is_file())
        self.assertTrue(self.store.path_for(second.id).is_file())
        self.assertFalse((self.root / 'fragments.json').exists())

    def test_search_matches_title_note_tags_text_and_source(self):
        self.store.create('Een vergeten sleutel.', title='Scène', tags=['mysterie'], fragment_id='a')
        self.store.create('Andere tekst', note='Op het station', source_book_title='Nachttrein', fragment_id='b')
        self.assertEqual([f.id for f in self.store.search('sleutel')], ['a'])
        self.assertEqual([f.id for f in self.store.search('station')], ['b'])
        self.assertEqual([f.id for f in self.store.search(tag='MYSTERIE')], ['a'])
        self.assertEqual([f.id for f in self.store.search('nachttrein')], ['b'])

    def test_metadata_update_never_changes_fragment_text(self):
        fragment = self.store.create('**exacte** bron', fragment_id='one')
        updated = self.store.update_metadata(fragment.id, expected_revision=fragment.revision, title='Nieuwe titel', tags=['x'])
        self.assertEqual(updated.text, '**exacte** bron')
        self.assertEqual(updated.title, 'Nieuwe titel')
        self.assertEqual(updated.tags, ('x',))

    def test_delete_is_recoverable_via_fragment_trash(self):
        fragment = self.store.create('bewaar mij', fragment_id='one')
        trash_path = self.store.move_to_trash(fragment.id)
        self.assertFalse(self.store.path_for(fragment.id).exists())
        self.assertTrue(trash_path.exists())
        restored = self.store.restore(trash_path)
        self.assertEqual(restored.text, 'bewaar mij')
        self.assertTrue(self.store.path_for(fragment.id).exists())

    def test_restore_refuses_to_overwrite_live_fragment(self):
        fragment = self.store.create('oud', fragment_id='one')
        trash_path = self.store.move_to_trash(fragment.id)
        self.store.create('nieuw', fragment_id='one')
        with self.assertRaises(FileExistsError):
            self.store.restore(trash_path)
        self.assertEqual(self.store.load('one').text, 'nieuw')
        self.assertTrue(trash_path.exists())

    def test_corrupt_utf8_fails_closed(self):
        path = self.store.path_for('broken')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'---\nid: broken\n---\n\xff')
        with self.assertRaises(CorruptSourceError):
            self.store.load('broken')

    def test_future_schema_is_refused(self):
        path = self.store.path_for('future')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '---\nfragment_schema_version: 999\nid: "future"\ncreated_at: "now"\ntags_json: []\n---\n\ntekst',
            encoding='utf-8',
        )
        with self.assertRaises(FutureFragmentFormatError):
            self.store.load('future')

    def test_filename_and_internal_id_must_match(self):
        path = self.store.path_for('file-id')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '---\nfragment_schema_version: 1\nid: "other-id"\ncreated_at: "now"\ntags_json: []\n---\n\ntekst',
            encoding='utf-8',
        )
        with self.assertRaises(FragmentFormatError):
            self.store.load('file-id')

    def test_empty_fragment_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.create('')


    def test_list_skips_bad_files_and_reports_them(self):
        self.store.create('goed', fragment_id='good')
        self.store.fragments_dir.mkdir(parents=True, exist_ok=True)
        (self.store.fragments_dir / 'notitie.md').write_text('geen fragment', encoding='utf-8')
        (self.store.fragments_dir / 'broken.md').write_bytes(b'\xff')
        items = self.store.list_fragments()
        self.assertEqual([item.id for item in items], ['good'])
        self.assertEqual(len(self.store.last_list_errors), 2)

    def test_search_still_works_when_one_fragment_file_is_bad(self):
        self.store.create('gezochte tekst', fragment_id='good')
        self.store.fragments_dir.mkdir(parents=True, exist_ok=True)
        (self.store.fragments_dir / 'conflicted-copy.md').write_text('los bestand', encoding='utf-8')
        self.assertEqual([item.id for item in self.store.search('gezochte')], ['good'])
        self.assertEqual(len(self.store.last_list_errors), 1)

    def test_roundtrip_preserves_leading_and_trailing_blank_lines(self):
        text = '\n\nEen hele alinea.\n\n'
        created = self.store.create(text, fragment_id='spacing')
        self.assertEqual(created.text, text)
        self.assertEqual(self.store.load('spacing').text, text)

    def test_metadata_update_rejects_stale_revision(self):
        original = self.store.create('tekst', fragment_id='one')
        laptop = self.store.update_metadata(
            'one', title='Titel van laptop', note='notitie laptop', expected_revision=original.revision
        )
        with self.assertRaises(FragmentExternalModificationError):
            self.store.update_metadata(
                'one', title='Titel van desktop', note='', expected_revision=original.revision
            )
        self.assertEqual(self.store.load('one').title, 'Titel van laptop')
        self.assertEqual(self.store.load('one').note, 'notitie laptop')
        self.assertIsNotNone(laptop.revision)

    def test_invalid_fragment_id_cannot_escape_workspace(self):
        with self.assertRaises(FragmentFormatError):
            self.store.create('tekst', fragment_id='../../naast')
        self.assertFalse((self.root.parent / 'naast.md').exists())

    def test_restore_rejects_invalid_internal_id_before_move(self):
        self.store.trash_dir.mkdir(parents=True, exist_ok=True)
        path = self.store.trash_dir / 'evil.md'
        path.write_text(
            '---\nfragment_schema_version: 1\nid: "../../../buiten"\ncreated_at: "2026-10-04T18:00:00Z"\ntags_json: []\n---\n\ntekst',
            encoding='utf-8',
        )
        with self.assertRaises(FragmentFormatError):
            self.store.restore(path)
        self.assertTrue(path.exists())

    def test_sorting_uses_instants_not_iso_text_around_dst(self):
        self.store.create('winter', fragment_id='w', created_at='2026-10-25T02:15:00+01:00')
        self.store.create('summer', fragment_id='z', created_at='2026-10-25T02:45:00+02:00')
        self.store.create('latest', fragment_id='l', created_at='2026-10-25T02:30:00+01:00')
        self.assertEqual([f.id for f in self.store.list_fragments()], ['l', 'w', 'z'])

    def test_constructing_store_does_not_create_directories(self):
        other_root = self.root / 'fresh'
        FragmentStore(other_root)
        self.assertFalse((other_root / 'fragments').exists())
        self.assertFalse((other_root / 'trash' / 'fragments').exists())

    def test_bad_trash_file_is_skipped_and_reported(self):
        fragment = self.store.create('goed', fragment_id='good')
        self.store.move_to_trash(fragment.id)
        (self.store.trash_dir / 'bad.md').write_bytes(b'\xff')
        items = self.store.list_trashed()
        self.assertEqual([fragment.id for _, fragment in items], ['good'])
        self.assertEqual(len(self.store.last_trash_list_errors), 1)


if __name__ == '__main__':
    unittest.main()


def test_update_metadata_requires_expected_revision(tmp_path):
    store = FragmentStore(tmp_path)
    fragment = store.create('tekst')
    try:
        store.update_metadata(fragment.id, title='mag niet stil')
    except TypeError:
        pass
    else:
        raise AssertionError('expected_revision moet verplicht zijn')
