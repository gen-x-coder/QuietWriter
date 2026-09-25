from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_image_card_click_only_selects():
    src = read('quietwriter/ui/image_block_card.py')
    method = src[src.index('    def mousePressEvent'):]
    assert 'self.selected.emit(self.block_number)' in method
    # The card itself must not open edit; editing is explicit through button/Enter.
    assert 'self.editRequested.emit(self.block_number)' not in method.split('    def ', 1)[0]


def test_editor_reserves_real_image_block_height_and_uses_document_geometry():
    src = read('quietwriter/ui/manuscript_editor.py')
    assert 'IMAGE_BLOCK_HEIGHT' in src
    assert "elif kind == 'image':" in src
    assert 'QTextBlockFormat.MinimumHeight' in src
    assert 'blockBoundingRect(block)' in src
    assert 'cursorRect(cursor)' in src  # only used to derive viewport translation


def test_image_markdown_is_hidden_and_protected():
    hi = read('quietwriter/ui/presentation_highlighter.py')
    editor = read('quietwriter/ui/manuscript_editor.py')
    assert "fmt.setFontPointSize(1.0)" in hi
    assert "self.selection_intersects_image()" in editor
    assert 'def insertFromMimeData' in editor
    assert 'def dropEvent' in editor
    assert 'def cut(self)' in editor
    assert "self.imageEditRequested.emit(current_image)" in editor
    assert "self.imageDeleteRequested.emit(current_image)" in editor


def test_insert_widget_has_real_edit_mode():
    src = read('quietwriter/ui/image_insert_widget.py')
    assert 'editRequested = Signal(str, str, str, str, str, bool, bool)' in src
    assert 'def set_edit_mode' in src
    assert "tr('insert.image.replace', 'Afbeelding vervangen…')" in src
    assert "tr('common.save', 'Opslaan')" in src


def test_editor_page_uses_localized_confirmation_and_media_store():
    src = read('quietwriter/ui/editor_page.py')
    assert 'self.editor.imageEditRequested.connect(self._open_image_editor)' in src
    assert 'self.editor.imageDeleteRequested.connect(self._delete_image_block)' in src
    assert 'image_block.delete_confirm' in src
    assert re.search(r"if not confirm\(\s*self,", src)
    assert 'self.media_store.import_image(self.book, Path(source_path))' in src


def test_new_image_block_locale_keys_exist_in_both_languages():
    keys = {
        'image_block.edit', 'image_block.delete', 'image_block.delete_confirm',
        'image_block.protected_title', 'insert.image.edit_title',
        'insert.image.edit_description', 'insert.image.replace', 'insert.image.updated',
    }
    for locale in ('nl.json', 'en.json'):
        data = json.loads(read(f'quietwriter/locales/{locale}'))
        assert keys <= data.keys()
