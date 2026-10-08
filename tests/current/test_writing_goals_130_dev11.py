from pathlib import Path

from quietwriter.storage import Library


def test_restore_keeps_live_writing_goal_and_deadline(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Doelboek')
    book.metadata['writing_goal_words'] = 60000
    book.metadata['writing_goal_date'] = '2027-03-01'
    lib.save_manifest(book)
    version = lib.create_version(book, kind='manual')

    # Change the current intention after the snapshot was made.
    book.metadata['writing_goal_words'] = 80000
    book.metadata['writing_goal_date'] = '2027-04-15'
    lib.save_manifest(book)

    restored = lib.restore_version(book, version['id'])
    assert restored.metadata['writing_goal_words'] == 80000
    assert restored.metadata['writing_goal_date'] == '2027-04-15'


def test_goal_fields_are_plain_book_metadata_and_therefore_package_data(tmp_path):
    lib = Library(tmp_path / 'workspace')
    book = lib.create_book('Doelboek')
    book.metadata['writing_goal_words'] = 75000
    book.metadata['writing_goal_date'] = '2027-06-30'
    lib.save_manifest(book)
    loaded = lib.load_book(book.path)
    assert loaded.metadata['writing_goal_words'] == 75000
    assert loaded.metadata['writing_goal_date'] == '2027-06-30'
