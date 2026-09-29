from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from ..i18n import tr
from ..media.manager import MediaCleanupError, MediaManager
from ..revisions import ExternalModificationError
from .dialogs import confirm


def _size_label(value: int) -> str:
    value = max(0, int(value or 0))
    if value < 1024:
        return f'{value} B'
    if value < 1024 * 1024:
        return f'{value / 1024:.1f} KB'
    return f'{value / (1024 * 1024):.1f} MB'


class MediaManagerPage(QWidget):
    """Text-first book media inventory and conservative cleanup UI.

    This page intentionally has no thumbnail gallery or image editor. The first
    media-manager iteration is about deterministic inventory/integrity/cleanup
    behaviour that can be regression-tested independently from rendering.
    """

    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.book = None
        self.manager = MediaManager(main.library)
        self.inventory = None

        root = QVBoxLayout(self)
        root.setContentsMargins(42, 34, 42, 34)
        root.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel(tr('media_manager.title', 'Media'))
        title.setObjectName('title')
        self.refresh_button = QPushButton(tr('media_manager.refresh', 'Vernieuwen'))
        self.refresh_button.setObjectName('secondaryButton')
        self.refresh_button.clicked.connect(self.refresh)
        self.cleanup_button = QPushButton(tr('media_manager.cleanup', 'Ongebruikte opruimen'))
        self.cleanup_button.setObjectName('secondaryButton')
        self.cleanup_button.clicked.connect(self.cleanup_unused)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.refresh_button)
        top.addWidget(self.cleanup_button)
        root.addLayout(top)

        self.subtitle = QLabel(tr(
            'media_manager.subtitle',
            'Controleer boekafbeeldingen, gebruik en integriteit. Opruimen maakt altijd eerst een herstelpunt in Versiegeschiedenis.'
        ))
        self.subtitle.setObjectName('muted')
        self.subtitle.setWordWrap(True)
        root.addWidget(self.subtitle)

        self.summary_box = QFrame()
        self.summary_box.setObjectName('softPanel')
        summary_layout = QVBoxLayout(self.summary_box)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        self.summary = QLabel('')
        self.summary.setWordWrap(True)
        summary_layout.addWidget(self.summary)
        root.addWidget(self.summary_box)

        self.list = QListWidget()
        self.list.itemSelectionChanged.connect(self._show_selected_details)
        root.addWidget(self.list, 1)

        self.details = QLabel('')
        self.details.setObjectName('muted')
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.details)

    def set_book(self, book):
        self.book = book
        self.setEnabled(bool(book))
        self.refresh()

    def adopt_book(self, book):
        """Update the live book reference without an eager history scan.

        Same-book conflict adoption can happen while the writer is on another
        page. Media inventory is intentionally refreshed only when Media is
        opened, so revision handling never pays for a full archive scan.
        """
        self.book = book
        self.setEnabled(bool(book))
        if self.isVisible():
            self.refresh()

    def _item_label(self, item) -> str:
        statuses = {
            'used': tr('media_manager.status.used', 'Gebruikt'),
            'unused': tr('media_manager.status.unused', 'Ongebruikt'),
            'missing': tr('media_manager.status.missing', 'Ontbreekt'),
            'modified': tr('media_manager.status.modified', 'Gewijzigd'),
        }
        status = statuses.get(item.status, item.status)
        name = item.original_name or Path(item.file).name
        dimensions = f'{item.width}×{item.height}' if item.width and item.height else '—'
        references = tr(
            'media_manager.references',
            '{count} verwijzing(en)', count=item.reference_count,
        )
        history = ''
        if item.history_reference_count:
            history = tr(
                'media_manager.history_suffix',
                ' · {count} historisch', count=item.history_reference_count,
            )
        return f'{status} · {name} · {dimensions} · {_size_label(item.size)} · {references}{history}'

    def refresh(self):
        self.list.clear()
        self.details.clear()
        if not self.book:
            self.inventory = None
            self.summary.setText(tr('media_manager.no_book', 'Geen boek geopend.'))
            self.cleanup_button.setEnabled(False)
            return
        try:
            self.inventory = self.manager.inspect(self.book, include_history=True)
        except Exception as exc:
            self.inventory = None
            self.summary.setText(tr('media_manager.read_error', 'Media kon niet worden gelezen: {error}', error=exc))
            self.cleanup_button.setEnabled(False)
            return

        inv = self.inventory
        cleanable = sum(1 for item in inv.items if item.can_cleanup)
        cover = tr('media_manager.cover.present', 'aanwezig') if inv.cover_file else tr('media_manager.cover.none', 'geen')
        self.summary.setText(tr(
            'media_manager.summary',
            'Omslag: {cover} · Afbeeldingen: {total} · gebruikt: {used} · ongebruikt: {unused} · opruimbaar: {cleanable} · aandacht: {problems}',
            cover=cover, total=len(inv.items), used=inv.used_count, unused=inv.unused_count,
            cleanable=cleanable, problems=inv.problem_count,
        ))
        if inv.source_errors:
            self.summary.setText(self.summary.text() + '\n' + tr(
                'media_manager.source_error_guard',
                'Opruimen is geblokkeerd: niet alle Markdownbronnen konden betrouwbaar worden gelezen.'
            ))

        if inv.cover_file:
            row = QListWidgetItem(
                tr('media_manager.cover_row', 'Omslag · {file} · {size}', file=inv.cover_file, size=_size_label(inv.cover_size))
            )
            row.setData(Qt.UserRole, {'kind': 'cover'})
            self.list.addItem(row)

        for media_item in inv.items:
            row = QListWidgetItem(self._item_label(media_item))
            row.setData(Qt.UserRole, {'kind': 'managed', 'id': media_item.id})
            self.list.addItem(row)

        for orphan in inv.untracked_files:
            row = QListWidgetItem(tr(
                'media_manager.untracked_row',
                'Niet geregistreerd · {file} · {size} · {count} verwijzing(en)',
                file=orphan.file, size=_size_label(orphan.size), count=orphan.reference_count,
            ))
            row.setData(Qt.UserRole, {'kind': 'untracked', 'file': orphan.file})
            self.list.addItem(row)

        if not self.list.count():
            row = QListWidgetItem(tr('media_manager.empty', 'Dit boek bevat nog geen media.'))
            row.setFlags(row.flags() & ~Qt.ItemIsSelectable)
            self.list.addItem(row)

        self.cleanup_button.setEnabled(bool(inv.can_cleanup))
        if self.list.count() and self.list.item(0).flags() & Qt.ItemIsSelectable:
            self.list.setCurrentRow(0)

    def _show_selected_details(self):
        if not self.inventory or not self.list.currentItem():
            self.details.clear()
            return
        data = dict(self.list.currentItem().data(Qt.UserRole) or {})
        if data.get('kind') == 'cover':
            self.details.setText(tr(
                'media_manager.cover_details',
                'De omslag wordt hier alleen gecontroleerd. Wijzigen of verwijderen blijft onderdeel van Boekdetails.'
            ))
            return
        if data.get('kind') == 'untracked':
            orphan = next((row for row in self.inventory.untracked_files if row.file == data.get('file')), None)
            if not orphan:
                self.details.clear(); return
            sources = ', '.join(f'{usage.source_file} ({usage.count})' for usage in orphan.usages) or tr('media_manager.none', 'geen')
            self.details.setText(tr(
                'media_manager.untracked_details',
                'Dit bestand staat niet in assets/manifest.json en wordt daarom niet automatisch verwijderd. Verwijzingen: {sources}.',
                sources=sources,
            ))
            return
        item = next((row for row in self.inventory.items if row.id == data.get('id')), None)
        if not item:
            self.details.clear(); return
        sources = ', '.join(f'{usage.source_file} ({usage.count})' for usage in item.usages) or tr('media_manager.none', 'geen')
        history = ', '.join(item.history_versions) or tr('media_manager.none', 'geen')
        safety = tr('media_manager.history_safe', 'herstelkopieën compleet') if item.history_safe else tr('media_manager.history_unsafe', 'historische herstelkopie ontbreekt')
        self.details.setText(tr(
            'media_manager.details',
            'Bestand: {file}\nHuidige verwijzingen: {sources}\nHistorische versies: {history}\nGeschiedeniscontrole: {safety}',
            file=item.file, sources=sources, history=history, safety=safety,
        ))

    def _resolve_external_change(self, exc: ExternalModificationError):
        """Rebase Media on the normal live-book conflict path.

        A clean editor can safely adopt the latest disk book immediately. If
        manuscript/publication text is still pending, delegate to the existing
        editor conflict resolver so Media cleanup can never discard that input.
        """
        editor = self.main.editor_page
        publication_pending = False
        try:
            current = editor.content_stack.currentWidget()
            publication_pending = (
                current is editor.publication_editor and editor.publication_editor.has_pending_changes()
            ) or (
                current is editor.publication_setup and editor.publication_setup.has_pending_changes()
            )
        except Exception:
            publication_pending = False

        if bool(getattr(editor, 'dirty', False)) or publication_pending:
            editor._resolve_external_change(exc)
            # The established conflict flow either adopted a fresh book or kept
            # the local edit intact. In both cases refresh against current state.
            self.book = getattr(self.main, '_active_book', None) or self.book
            self.refresh()
            return

        try:
            latest = self.main.library.load_book(self.book.path)
            self.main.adopt_active_book(
                latest,
                preferred_chapter_id=getattr(getattr(editor, 'chapter', None), 'id', None),
                planning_changed_files=exc.changed_files,
            )
            self.book = latest
            self.refresh()
            QMessageBox.information(
                self,
                tr('media_manager.external_title', 'Boek extern gewijzigd'),
                tr(
                    'media_manager.external_reloaded',
                    'Het boek is op een andere computer gewijzigd. De nieuwste versie en media-inventaris zijn geladen. Controleer de inventaris en probeer daarna opnieuw.'
                ),
            )
        except Exception as reload_error:
            QMessageBox.warning(
                self,
                tr('media_manager.external_title', 'Boek extern gewijzigd'),
                tr(
                    'media_manager.external_reload_failed',
                    'Opruimen is niet uitgevoerd en de nieuwste versie kon niet veilig worden geladen. Er is niets overschreven.\n\n{error}',
                    error=reload_error,
                ),
            )
            self.refresh()

    def cleanup_unused(self):
        if not self.book or not self.inventory:
            return
        candidates = [item for item in self.inventory.items if item.can_cleanup]
        if not candidates:
            return
        if not confirm(
            self,
            tr('media_manager.cleanup_title', 'Ongebruikte media opruimen'),
            tr(
                'media_manager.cleanup_confirm',
                'QuietWriter verwijdert {count} ongebruikte afbeelding(en) uit het live boek. Eerst wordt automatisch een volledig herstelpunt in Versiegeschiedenis gemaakt. Doorgaan?',
                count=len(candidates),
            ),
        ):
            return
        try:
            result = self.manager.cleanup_unused(self.book, asset_ids=[item.id for item in candidates])
        except ExternalModificationError as exc:
            self._resolve_external_change(exc)
            return
        except Exception as exc:
            QMessageBox.warning(
                self,
                tr('media_manager.cleanup_title', 'Ongebruikte media opruimen'),
                tr('media_manager.cleanup_error', 'Opruimen is niet uitgevoerd.\n\n{error}', error=exc),
            )
            self.refresh()
            return

        if result.leftover_files:
            QMessageBox.warning(
                self,
                tr('media_manager.cleanup_title', 'Ongebruikte media opruimen'),
                tr(
                    'media_manager.cleanup_leftovers',
                    '{count} media-item(s) zijn uit het manifest verwijderd, maar {leftovers} bestand(en) konden door een bestandslock niet fysiek worden verwijderd. Ze blijven als niet-geregistreerd zichtbaar.',
                    count=len(result.removed_ids), leftovers=len(result.leftover_files),
                ),
            )
        elif result.removed_ids:
            self.main.status.showMessage(tr(
                'media_manager.cleanup_done',
                '{count} ongebruikte afbeelding(en) opgeruimd; herstelpunt opgeslagen in Versiegeschiedenis.',
                count=len(result.removed_ids),
            ), 5000)
        self.refresh()
