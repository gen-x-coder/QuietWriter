from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from ..i18n import tr
from ..integrity import BookIntegrityChecker
from ..migrations import FutureBookFormatError, MigrationError
from ..revisions import ExternalModificationError
from ..storage import BookBlockedError, StorageWriteError


class IntegrityPage(QWidget):
    """Thin, explicit UI over the read-only integrity checker and safe repair API."""

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.library = main.library
        self.book = None
        self.checker = BookIntegrityChecker()
        self.report = None
        self._central_reload_in_progress = False
        self._recovery_cache = {}
        self._recovery_meta_cache = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(42, 34, 42, 34)
        root.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel(tr('integrity.title', 'Integriteit & herstel'))
        title.setObjectName('title')
        self.refresh_button = QPushButton(tr('integrity.refresh', 'Opnieuw controleren'))
        self.refresh_button.setObjectName('secondaryButton')
        self.refresh_button.clicked.connect(self.refresh)
        self.migrate_button = QPushButton(tr('integrity.migrate', 'Boekformaat bijwerken'))
        self.migrate_button.setObjectName('secondaryButton')
        self.migrate_button.clicked.connect(self.migrate_book)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.refresh_button)
        top.addWidget(self.migrate_button)
        root.addLayout(top)

        subtitle = QLabel(tr(
            'integrity.subtitle',
            'Controleert de boekstructuur zonder iets te wijzigen. Herstel gebeurt alleen na jouw expliciete keuze en maakt eerst een herstelpunt.'
        ))
        subtitle.setObjectName('muted')
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        self.summary_box = QFrame()
        self.summary_box.setObjectName('softPanel')
        summary_layout = QVBoxLayout(self.summary_box)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        self.summary = QLabel('')
        self.summary.setWordWrap(True)
        summary_layout.addWidget(self.summary)
        root.addWidget(self.summary_box)

        self.list = QListWidget()
        self.list.itemSelectionChanged.connect(self._selection_changed)
        root.addWidget(self.list, 1)

        self.details = QLabel('')
        self.details.setObjectName('muted')
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextSelectableByMouse)
        root.addWidget(self.details)

        actions = QHBoxLayout()
        actions.addStretch()
        self.repair_button = QPushButton(tr('integrity.repair', 'Herstel geselecteerd bestand'))
        self.repair_button.clicked.connect(self.repair_selected)
        actions.addWidget(self.repair_button)
        root.addLayout(actions)

        self.set_book(None)

    def set_book(self, book):
        self.book = book
        self.setEnabled(bool(book))
        if book:
            self.refresh()
        else:
            self.report = None
            self.list.clear()
            self.summary.setText(tr('integrity.no_book', 'Geen boek geopend.'))
            self.details.clear()
            self.repair_button.setEnabled(False)
            self.migrate_button.setEnabled(False)
            self.migrate_button.setVisible(False)

    def adopt_book(self, book):
        self.book = book
        self.setEnabled(bool(book))
        # adopt_active_book() calls every page. During our own pre/post-audit
        # reload that must not recursively start another integrity refresh.
        if self.isVisible() and not self._central_reload_in_progress:
            self.refresh()

    def _adopt_latest_disk_state(self):
        """Reload the current book centrally without saving anything.

        Integrity is entered only after all editable pages have been saved. A
        fresh adoption therefore makes the disk state authoritative and resets
        revision tracking to exactly the state that is about to be audited.
        Future-format/corrupt manifests are intentionally left to the read-only
        checker, which can explain them without trying to adopt them.
        """
        if not self.book or self.library.is_book_blocked(self.book):
            return self.book
        preferred_chapter_id = getattr(getattr(self.main, 'editor_page', None), 'chapter', None)
        preferred_chapter_id = getattr(preferred_chapter_id, 'id', None)
        try:
            latest = self.library.load_book(self.book.path)
        except (FutureBookFormatError, MigrationError, OSError, ValueError, TypeError):
            return self.book
        self._central_reload_in_progress = True
        try:
            try:
                self.main.adopt_active_book(latest, preferred_chapter_id=preferred_chapter_id)
            except Exception:
                # A damaged UTF-8 text file may make one of the ordinary UI
                # loaders reject the book. Integrity must remain reachable in
                # exactly that situation: keep the existing live state and let
                # the read-only checker describe/recover the damaged file.
                return self.book
            self.book = latest
        finally:
            self._central_reload_in_progress = False
        return latest

    def refresh(self):
        self.list.clear()
        self.details.clear()
        self.repair_button.setEnabled(False)
        self.migrate_button.setEnabled(False)
        self._recovery_cache = {}
        self._recovery_meta_cache = {}
        if not self.book:
            self.report = None
            self.summary.setText(tr('integrity.no_book', 'Geen boek geopend.'))
            return
        self._adopt_latest_disk_state()
        try:
            self.report = self.checker.audit_folder(Path(self.book.path))
        except Exception as exc:
            self.report = None
            self.summary.setText(tr('integrity.audit_failed', 'Controle kon niet worden uitgevoerd: {error}', error=exc))
            return

        errors = len(self.report.errors)
        warnings = len(self.report.warnings)
        if not self.report.issues:
            self.summary.setText(tr('integrity.ok', 'Geen integriteitsproblemen gevonden.'))
        else:
            self.summary.setText(tr(
                'integrity.summary',
                'Controle voltooid · {errors} fout(en) · {warnings} waarschuwing(en). Er wordt niets automatisch hersteld.',
                errors=errors, warnings=warnings,
            ))

        for issue in self.report.issues:
            prefix = tr('integrity.error', 'Fout') if issue.severity == 'error' else tr('integrity.warning', 'Waarschuwing')
            row = QListWidgetItem(f'{prefix} · {issue.path} · {issue.message}')
            row.setData(Qt.UserRole, issue)
            self.list.addItem(row)

        migration = any(issue.code == 'migration_required' for issue in self.report.issues)
        self.migrate_button.setEnabled(migration)
        self.migrate_button.setVisible(migration)
        if self.list.count():
            self.list.setCurrentRow(0)

    def _selection_changed(self):
        item = self.list.currentItem()
        if not item:
            self.details.clear()
            self.repair_button.setEnabled(False)
            return
        issue = item.data(Qt.UserRole)
        if issue is None:
            self.details.clear()
            self.repair_button.setEnabled(False)
            return

        recovery = None
        recovery_meta = None
        if issue.recoverable and issue.path != 'book.json':
            if issue.path not in self._recovery_cache:
                recovery_meta = self.checker.latest_recovery_candidate(self.library, self.book, issue.path)
                self._recovery_meta_cache[issue.path] = recovery_meta
                self._recovery_cache[issue.path] = recovery_meta['path'] if recovery_meta else None
            recovery = self._recovery_cache[issue.path]
            recovery_meta = self._recovery_meta_cache.get(issue.path)
        if issue.recoverable and recovery is not None:
            recovery_text = tr('integrity.recovery_available', 'Er is een geldige herstelkopie in Versiegeschiedenis beschikbaar.')
            if recovery_meta:
                kind_key = {
                    'conflict_local': 'integrity.recovery_kind.conflict_local',
                    'manual': 'integrity.recovery_kind.manual',
                    'daily': 'integrity.recovery_kind.daily',
                    'pre_restore': 'integrity.recovery_kind.pre_restore',
                }.get(recovery_meta.get('kind'), 'integrity.recovery_kind.version')
                kind = tr(kind_key, 'versie')
                stamp = str(recovery_meta.get('created_at') or '').replace('T', ' ')[:16]
                recovery_text += '\n' + tr('integrity.recovery_source', 'Herstelkopie: {kind} van {time}.', kind=kind, time=stamp)
        elif issue.recoverable:
            recovery_text = tr('integrity.recovery_missing', 'Er is geen geldige herstelkopie in Versiegeschiedenis gevonden.')
        else:
            recovery_text = tr('integrity.not_automatic', 'Dit probleem wordt niet automatisch gewijzigd door QuietWriter.')
        self.details.setText(f'{issue.message}\n\n{recovery_text}')
        self.repair_button.setEnabled(bool(issue.recoverable and recovery is not None and issue.path != 'book.json'))

    def repair_selected(self):
        item = self.list.currentItem()
        issue = item.data(Qt.UserRole) if item else None
        if not issue or not issue.recoverable or issue.path == 'book.json':
            return
        source = self._recovery_cache.get(issue.path)
        if source is None:
            source = self.checker.latest_recovery_file(self.library, self.book, issue.path)
        if source is None:
            QMessageBox.information(self, tr('integrity.no_recovery_title', 'Geen herstelkopie'), tr('integrity.no_recovery', 'Voor dit bestand is geen geldige herstelkopie beschikbaar.'))
            self.refresh()
            return
        answer = QMessageBox.question(
            self,
            tr('integrity.confirm_title', 'Bestand herstellen'),
            tr('integrity.confirm', 'Herstel {path} vanuit de nieuwste geldige kopie in Versiegeschiedenis?\n\nQuietWriter maakt eerst een extra herstelpunt van de huidige toestand.', path=issue.path),
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.checker.restore_file_from_history(self.library, self.book, issue.path)
        except BookBlockedError as exc:
            QMessageBox.warning(self, tr('integrity.blocked_title', 'Boek is geblokkeerd'), str(exc))
            return
        except ExternalModificationError:
            QMessageBox.warning(self, tr('integrity.external_title', 'Boek extern gewijzigd'), tr('integrity.external', 'Het boek is sinds de controle extern gewijzigd. Er is niets hersteld. Open of laad het boek opnieuw en controleer daarna opnieuw.'))
            return
        except (StorageWriteError, OSError, ValueError) as exc:
            QMessageBox.critical(self, tr('integrity.repair_failed_title', 'Herstel mislukt'), tr('integrity.repair_failed', 'Het bestand kon niet veilig worden hersteld.\n\n{error}', error=exc))
            return
        # The repair changed disk state behind every page. Reload centrally
        # before the editor can become active again, otherwise stale editor text
        # could overwrite the just-restored chapter on its next autosave.
        self._adopt_latest_disk_state()
        self.main.status.showMessage(tr('integrity.repaired_status', 'Bestand hersteld en opnieuw gecontroleerd'), 4000)
        self.refresh()

    def migrate_book(self):
        if not self.book:
            return
        answer = QMessageBox.question(
            self,
            tr('integrity.migrate_title', 'Boekformaat bijwerken'),
            tr('integrity.migrate_confirm', 'Werk dit oudere boekformaat bij naar de huidige QuietWriter-versie?\n\nVooraf wordt een volledige herstelversie gemaakt.'),
        )
        if answer != QMessageBox.Yes:
            return
        try:
            migrated, result, _checkpoint = self.library.migrate_book_format(self.book)
        except (BookBlockedError, ExternalModificationError, StorageWriteError, MigrationError, OSError) as exc:
            QMessageBox.critical(self, tr('integrity.migrate_failed_title', 'Migratie mislukt'), tr('integrity.migrate_failed', 'Het boekformaat kon niet veilig worden bijgewerkt.\n\n{error}', error=exc))
            return
        self.main.adopt_active_book(migrated)
        self.book = migrated
        if result.changed:
            self.main.status.showMessage(tr('integrity.migrated_status', 'Boekformaat bijgewerkt'), 4000)
        self.refresh()
