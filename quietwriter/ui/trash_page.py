from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from .dialogs import confirm
from ..i18n import tr


class TrashPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 34, 42, 34)
        top = QHBoxLayout()
        title = QLabel(tr('trash.title', 'Prullenbak'))
        title.setObjectName('title')
        self.restore_btn = QPushButton(tr('trash.restore', 'Herstellen'))
        self.restore_btn.setObjectName('primaryButton')
        self.restore_btn.clicked.connect(self.restore_selected)
        self.delete_btn = QPushButton(tr('trash.delete_selected', 'Selectie definitief verwijderen'))
        self.delete_btn.setObjectName('dangerButton')
        self.delete_btn.clicked.connect(self.delete_selected)
        self.empty_btn = QPushButton(tr('trash.empty_button', 'Prullenbak legen'))
        self.empty_btn.setObjectName('dangerButton')
        self.empty_btn.clicked.connect(self.empty_trash)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.restore_btn)
        top.addWidget(self.delete_btn)
        top.addWidget(self.empty_btn)

        info = QLabel(tr(
            'trash.info',
            'Selecteer één of meer boeken, hoofdstukken of fragmenten. Definitief verwijderen kan niet ongedaan worden gemaakt.',
        ))
        info.setObjectName('muted')
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.ExtendedSelection)
        self.list.itemSelectionChanged.connect(self._update_actions)
        self.list.itemActivated.connect(lambda _item: self.restore_selected())
        self.empty = QLabel(tr('trash.empty', 'De prullenbak is leeg.'))
        self.empty.setObjectName('muted')
        self.empty.setAlignment(Qt.AlignCenter)
        root.addLayout(top)
        root.addWidget(info)
        root.addSpacing(10)
        root.addWidget(self.empty)
        root.addWidget(self.list, 1)
        self.refresh()

    def refresh(self):
        rows = []
        demo_mode = bool(getattr(self.main, 'start', None) and self.main.start.demo_mode_enabled())
        for row in self.main.library.list_trashed_books():
            if demo_mode and row.get('book_id') and row.get('book_id') not in self.main.library.shelves.visible_book_ids([row.get('book_id')], demo_mode=True):
                continue
            rows.append({
                'kind': 'book',
                'path': str(row['path']),
                'book_id': row.get('book_id', ''),
                'deleted': row['deleted'],
                'title': row['title'],
            })
        for row in self.main.library.list_trashed_chapters():
            if demo_mode and row.get('book_id') and row.get('book_id') not in self.main.library.shelves.visible_book_ids([row.get('book_id')], demo_mode=True):
                continue
            rows.append({
                'kind': 'chapter',
                'path': str(row['path']),
                'book_id': row.get('book_id', ''),
                'deleted': row['deleted'],
                'title': row['title'],
                'book_title': row.get('book_title', ''),
                'book_available': bool(row.get('book_available')),
            })
        for path, fragment in self.main.darlings_page.store.list_trashed():
            if demo_mode and fragment.source_book_id and fragment.source_book_id not in self.main.library.shelves.visible_book_ids([fragment.source_book_id], demo_mode=True):
                continue
            rows.append({
                'kind': 'fragment', 'path': str(path), 'deleted': path.stat().st_mtime,
                'title': self.main.darlings_page.display_name(fragment),
            })
        rows.sort(key=lambda row: row['deleted'], reverse=True)

        self.list.clear()
        for row in rows:
            dt = datetime.fromtimestamp(row['deleted']).strftime('%d-%m-%Y %H:%M')
            if row['kind'] == 'book':
                label = tr('trash.row_book', 'Boek · {title}   ·   verwijderd {date}', title=row['title'], date=dt)
            elif row['kind'] == 'fragment':
                label = tr('trash.row_fragment', 'Fragment · {title}   ·   verwijderd {date}', title=row['title'], date=dt)
            else:
                label = tr(
                    'trash.row_chapter',
                    'Hoofdstuk · {title}   ·   {book}   ·   verwijderd {date}',
                    title=row['title'], book=row.get('book_title') or row.get('book_id') or '?', date=dt,
                )
                if not row.get('book_available'):
                    label += tr('trash.book_not_active_suffix', '   ·   boek staat niet in de boekenkast')
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, row)
            self.list.addItem(item)

        self.empty.setVisible(not rows)
        self.list.setVisible(bool(rows))
        self.empty_btn.setEnabled(bool(rows))
        self._update_actions()

    def _update_actions(self):
        has_selection = bool(self.list.selectedItems())
        self.restore_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def selected_entries(self):
        return [dict(item.data(Qt.UserRole) or {}) for item in self.list.selectedItems()]

    def _refresh_active_book_after_chapter_restore(self, book_id: str):
        editor_page = self.main.editor_page
        if not editor_page.book or editor_page.book.id != book_id:
            return
        current_id = editor_page.chapter.id if editor_page.chapter else None
        editor_page._rebuild_word_count_cache()
        if current_id:
            editor_page.populate_tree(after=lambda cid=current_id: editor_page.select_tree_chapter(cid))
        else:
            editor_page.populate_tree()

    def restore_selected(self):
        entries = self.selected_entries()
        if not entries:
            QMessageBox.information(
                self, tr('trash.title', 'Prullenbak'),
                tr('trash.select_first', 'Selecteer eerst één of meer boeken, hoofdstukken of fragmenten.'),
            )
            return

        errors = []
        # Restore books first. This allows a book + one of its deleted chapters
        # to be selected and restored in a single action.
        for entry in sorted(entries, key=lambda row: 0 if row.get('kind') == 'book' else 1):
            path = Path(entry.get('path', ''))
            try:
                if entry.get('kind') == 'chapter':
                    active = self.main.editor_page.book
                    active_book = active if active and active.id == entry.get('book_id') else None
                    self.main.library.restore_trashed_chapter(path, book=active_book)
                    if active_book is not None:
                        self._refresh_active_book_after_chapter_restore(active_book.id)
                elif entry.get('kind') == 'fragment':
                    self.main.darlings_page.store.restore(path)
                    self.main.darlings_page.refresh()
                else:
                    self.main.library.restore_trashed_book(path)
            except Exception as exc:
                errors.append(f"{entry.get('title') or path.name}: {exc}")

        self.main.start.refresh()
        self.refresh()
        if errors:
            QMessageBox.warning(
                self,
                tr('trash.restore_error_title', 'Herstellen'),
                tr('trash.partial_restore_error', 'Niet alles kon worden hersteld:\n{errors}', errors='\n'.join(errors)),
            )

    def delete_selected(self):
        entries = self.selected_entries()
        if not entries:
            QMessageBox.information(
                self, tr('trash.title', 'Prullenbak'),
                tr('trash.select_first', 'Selecteer eerst één of meer boeken, hoofdstukken of fragmenten.'),
            )
            return
        if not confirm(
            self,
            tr('trash.delete_title', 'Definitief verwijderen'),
            tr('trash.delete_confirm', 'Wil je {count} geselecteerde item(s) definitief verwijderen?', count=len(entries)),
        ):
            return

        errors = []
        for entry in entries:
            path = Path(entry.get('path', ''))
            try:
                if entry.get('kind') == 'chapter':
                    self.main.library.permanently_delete_trashed_chapter(path)
                elif entry.get('kind') == 'fragment':
                    self.main.darlings_page.store.permanently_delete(path)
                else:
                    self.main.library.permanently_delete_trashed_book(path)
            except Exception as exc:
                errors.append(f"{entry.get('title') or path.name}: {exc}")
        self.refresh()
        if errors:
            QMessageBox.warning(
                self,
                tr('trash.delete_error_title', 'Definitief verwijderen'),
                tr('trash.partial_delete_error', 'Niet alles kon definitief worden verwijderd:\n{errors}', errors='\n'.join(errors)),
            )

    def empty_trash(self):
        if not confirm(
            self,
            tr('trash.empty_title', 'Prullenbak legen'),
            tr('trash.empty_confirm', 'Wil je alle boeken, hoofdstukken en fragmenten in de prullenbak definitief verwijderen?'),
        ):
            return
        try:
            self.main.library.empty_trash()
            for path, _fragment in self.main.darlings_page.store.list_trashed():
                self.main.darlings_page.store.permanently_delete(path)
        except Exception as exc:
            QMessageBox.warning(
                self,
                tr('trash.empty_error_title', 'Prullenbak legen'),
                tr('trash.empty_error', 'Niet alles kon definitief worden verwijderd.\n\n{error}', error=exc),
            )
        finally:
            self.refresh()
