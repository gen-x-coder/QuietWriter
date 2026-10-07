from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .migrations import CURRENT_BOOK_FORMAT, FutureBookFormatError, MigrationError, detected_book_format, validate_manifest_structure
from .storage import _safe_atomic_write_text, _safe_atomic_write_bytes, CorruptSourceError
from .planning_validation import FuturePlanningFormatError, validate_planning_payload
from .manuscript_profile import (CURRENT_MANUSCRIPT_SYNTAX_VERSION, FutureManuscriptSyntaxError,
                                 ManuscriptSyntaxError, profile_from_manifest)


@dataclass(frozen=True)
class IntegrityIssue:
    code: str
    severity: str
    path: str
    message: str
    recoverable: bool = False


@dataclass
class IntegrityReport:
    book_path: Path
    issues: list[IntegrityIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == 'error' for i in self.issues)

    @property
    def errors(self) -> tuple[IntegrityIssue, ...]:
        return tuple(i for i in self.issues if i.severity == 'error')

    @property
    def warnings(self) -> tuple[IntegrityIssue, ...]:
        return tuple(i for i in self.issues if i.severity == 'warning')


def _safe_relative(value: str) -> bool:
    p = PurePosixPath(str(value).replace('\\', '/'))
    return bool(value) and not p.is_absolute() and '..' not in p.parts


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


class BookIntegrityChecker:
    """Read-only integrity audit for a QuietWriter book folder."""

    JSON_FILES = ('planning/characters.json', 'planning/outline.json', 'planning/open_points.json', 'publication/publication.json', 'export/settings.json')
    UTF8_FILES = ('planning/notes.md', 'ai/boekprofiel.md', 'ai/memory.md')

    def audit_folder(self, folder: Path) -> IntegrityReport:
        folder = Path(folder)
        report = IntegrityReport(folder)
        manifest_path = folder / 'book.json'
        if not manifest_path.is_file():
            report.issues.append(IntegrityIssue('book_manifest_missing', 'error', 'book.json', 'book.json ontbreekt.'))
            return report
        try:
            data = _read_json(manifest_path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            report.issues.append(IntegrityIssue('book_manifest_invalid', 'error', 'book.json', f'book.json is niet leesbaar: {exc}'))
            return report
        if not isinstance(data, dict):
            report.issues.append(IntegrityIssue('book_manifest_shape', 'error', 'book.json', 'book.json bevat geen JSON-object.'))
            return report
        try:
            fmt = detected_book_format(data)
            if fmt > CURRENT_BOOK_FORMAT:
                raise FutureBookFormatError('toekomstig formaat')
            if fmt < CURRENT_BOOK_FORMAT:
                report.issues.append(IntegrityIssue('migration_required', 'warning', 'book.json', f'Boekformaat {fmt} kan worden gemigreerd naar {CURRENT_BOOK_FORMAT}.'))
        except FutureBookFormatError:
            report.issues.append(IntegrityIssue('future_format', 'error', 'book.json', f'Boekformaat is nieuwer dan ondersteund ({CURRENT_BOOK_FORMAT}).'))
        except MigrationError as exc:
            report.issues.append(IntegrityIssue('book_format_invalid', 'error', 'book.json', str(exc)))

        try:
            validate_manifest_structure(data, allow_legacy=True)
        except FutureBookFormatError:
            pass  # already reported above as future_format
        except MigrationError as exc:
            report.issues.append(IntegrityIssue('book_structure_invalid', 'error', 'book.json', str(exc)))

        try:
            syntax = profile_from_manifest(data)
            if not syntax.explicit:
                report.issues.append(IntegrityIssue(
                    'manuscript_syntax_unversioned', 'warning', 'book.json',
                    'Dit boek heeft nog geen expliciete manuscriptsyntaxversie; QuietWriter laat het boek ongewijzigd.'
                ))
        except FutureManuscriptSyntaxError as exc:
            report.issues.append(IntegrityIssue('future_manuscript_syntax', 'error', 'book.json', str(exc)))
        except ManuscriptSyntaxError as exc:
            report.issues.append(IntegrityIssue('manuscript_syntax_invalid', 'error', 'book.json', str(exc)))

        if not str(data.get('id') or '').strip():
            report.issues.append(IntegrityIssue('book_id_missing', 'error', 'book.json', 'Boek-id ontbreekt.'))
        if not str(data.get('title') or '').strip():
            report.issues.append(IntegrityIssue('book_title_missing', 'error', 'book.json', 'Boektitel ontbreekt.'))

        seen_ids: set[str] = set(); seen_files: set[str] = set()
        sections = data.get('sections')
        if not isinstance(sections, list):
            report.issues.append(IntegrityIssue('sections_invalid', 'error', 'book.json', 'sections is geen lijst.'))
            sections = []
        for section in sections:
            if not isinstance(section, dict):
                report.issues.append(IntegrityIssue('section_invalid', 'error', 'book.json', 'Een sectie heeft een ongeldig formaat.'))
                continue
            chapters = section.get('chapters', [])
            if not isinstance(chapters, list):
                report.issues.append(IntegrityIssue('chapters_invalid', 'error', 'book.json', 'Een hoofdstuklijst heeft een ongeldig formaat.'))
                continue
            for chapter in chapters:
                if not isinstance(chapter, dict):
                    report.issues.append(IntegrityIssue('chapter_invalid', 'error', 'book.json', 'Een hoofdstuk heeft een ongeldig formaat.'))
                    continue
                cid = str(chapter.get('id') or ''); rel = str(chapter.get('file') or '')
                if not cid or cid in seen_ids:
                    report.issues.append(IntegrityIssue('chapter_id_invalid', 'error', 'book.json', f'Ontbrekende of dubbele hoofdstuk-id: {cid or "<leeg>"}.'))
                seen_ids.add(cid)
                if not _safe_relative(rel) or not rel.startswith('chapters/'):
                    report.issues.append(IntegrityIssue('chapter_path_unsafe', 'error', 'book.json', f'Ongeldig hoofdstukpad: {rel or "<leeg>"}.'))
                    continue
                normalized = PurePosixPath(rel).as_posix()
                normalized = '/'.join(part for part in normalized.split('/') if part not in ('', '.')).casefold()
                if normalized in seen_files:
                    report.issues.append(IntegrityIssue('chapter_file_duplicate', 'error', 'book.json', f'Hoofdstukbestand dubbel gekoppeld: {rel}.'))
                seen_files.add(normalized)
                path = folder / rel
                if not path.is_file():
                    report.issues.append(IntegrityIssue('chapter_missing', 'error', rel, 'Hoofdstukbestand ontbreekt.', True))
                else:
                    try: path.read_text(encoding='utf-8-sig')
                    except (OSError, UnicodeError) as exc:
                        report.issues.append(IntegrityIssue('chapter_unreadable', 'error', rel, f'Hoofdstuk is niet als UTF-8 leesbaar: {exc}', True))

        for rel in self.JSON_FILES:
            path = folder / rel
            if not path.exists():
                continue
            try:
                value = _read_json(path)
                if not isinstance(value, dict):
                    raise ValueError('verwacht JSON-object')
                if rel == 'planning/characters.json':
                    validate_planning_payload('characters', value, path)
                elif rel == 'planning/outline.json':
                    validate_planning_payload('scenes', value, path)
            except FuturePlanningFormatError as exc:
                report.issues.append(IntegrityIssue(
                    'aux_json_newer', 'error', rel,
                    f'Gemaakt met een nieuwere QuietWriter (Planning-formaat {exc.version}). Werk QuietWriter bij; herstellen zou nieuwere Planning-gegevens terugdraaien.',
                    False,
                ))
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError, CorruptSourceError) as exc:
                report.issues.append(IntegrityIssue('aux_json_invalid', 'error', rel, f'Bestand is ongeldig: {exc}', True))
        for rel in self.UTF8_FILES:
            path = folder / rel
            if not path.exists(): continue
            try: path.read_text(encoding='utf-8-sig')
            except (OSError, UnicodeError) as exc:
                report.issues.append(IntegrityIssue('aux_text_invalid', 'error', rel, f'Bestand is niet als UTF-8 leesbaar: {exc}', True))

        publication_texts = folder / 'publication' / 'texts'
        if publication_texts.is_dir():
            for path in sorted(publication_texts.glob('*.md')):
                rel = path.relative_to(folder).as_posix()
                try:
                    path.read_text(encoding='utf-8-sig')
                except (OSError, UnicodeError) as exc:
                    report.issues.append(IntegrityIssue('aux_text_invalid', 'error', rel, f'Bestand is niet als UTF-8 leesbaar: {exc}', True))

        self._audit_media(folder, report)
        return report

    def _audit_media(self, folder: Path, report: IntegrityReport):
        rel = 'assets/manifest.json'; path = folder / rel
        if not path.exists():
            report.issues.append(IntegrityIssue('media_manifest_missing', 'warning', rel, 'Mediamanifest ontbreekt; dit kan een ouder boek zijn.'))
            return
        try: data = _read_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            report.issues.append(IntegrityIssue('media_manifest_invalid', 'error', rel, f'Mediamanifest is ongeldig: {exc}', True)); return
        if not isinstance(data, dict) or not isinstance(data.get('images', {}), dict):
            report.issues.append(IntegrityIssue('media_manifest_shape', 'error', rel, 'Mediamanifest heeft een ongeldig formaat.', True)); return
        for asset_id, row in data.get('images', {}).items():
            if not isinstance(row, dict):
                report.issues.append(IntegrityIssue('media_record_invalid', 'error', rel, f'Mediarecord {asset_id} is ongeldig.', True)); continue
            asset_rel = str(row.get('file') or '')
            if not _safe_relative(asset_rel) or not asset_rel.startswith('assets/images/'):
                report.issues.append(IntegrityIssue('media_path_unsafe', 'error', rel, f'Ongeldig mediapad voor {asset_id}: {asset_rel}.')); continue
            asset_path = folder / asset_rel
            if not asset_path.is_file():
                report.issues.append(IntegrityIssue('media_missing', 'error', asset_rel, 'Mediabestand ontbreekt.', True)); continue
            expected = str(row.get('sha256') or '')
            try: actual = _sha256(asset_path)
            except OSError as exc:
                report.issues.append(IntegrityIssue('media_unreadable', 'error', asset_rel, f'Mediabestand kan niet worden gelezen: {exc}', True)); continue
            if expected and actual != expected:
                report.issues.append(IntegrityIssue('media_hash_mismatch', 'error', asset_rel, 'SHA-256 wijkt af van het mediamanifest.', True))

    def _valid_recovery_candidate(self, library, book, relative: str, candidate: Path) -> bool:
        try:
            if relative.startswith('assets/images/'):
                live_manifest = _read_json(Path(book.path) / 'assets/manifest.json')
                images = live_manifest.get('images', {}) if isinstance(live_manifest, dict) else {}
                expected = next((str(row.get('sha256') or '') for row in images.values()
                                 if isinstance(row, dict) and str(row.get('file') or '') == relative), '')
                return bool(expected) and _sha256(candidate) == expected
            if candidate.suffix.lower() == '.json':
                return isinstance(_read_json(candidate), dict)
            candidate.read_text(encoding='utf-8')
            return True
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            return False

    def latest_recovery_candidate(self, library, book, relative: str) -> dict | None:
        """Newest valid history candidate, including provenance for transparent repair UI."""
        for version in library.list_versions(book):
            if version.get('kind') == 'pre_integrity_repair':
                continue
            candidate = Path(version['path']) / relative
            if candidate.is_file() and self._valid_recovery_candidate(library, book, relative, candidate):
                return {'path': candidate, 'kind': version.get('kind', 'manual'),
                        'created_at': version.get('created_at', ''), 'id': version.get('id', '')}
        return None

    def latest_recovery_file(self, library, book, relative: str) -> Path | None:
        """Newest history copy that passes the same content rule used by repair."""
        candidate = self.latest_recovery_candidate(library, book, relative)
        return candidate['path'] if candidate else None

    @staticmethod
    def _atomic_write_bytes(target: Path, data: bytes):
        _safe_atomic_write_bytes(target, data)

    def restore_file_from_history(self, library, book, relative: str) -> str:
        """Restore one file byte-exactly, then prove the restored copy is valid."""
        if not _safe_relative(relative) or relative == 'book.json':
            raise ValueError('Dit bestand kan niet met bestandsherstel worden teruggezet.')
        library.verify_book_unchanged(book)
        source = self.latest_recovery_file(library, book, relative)
        if source is None:
            raise FileNotFoundError(f'Geen bruikbare herstelkopie voor {relative}.')
        payload = source.read_bytes()
        checkpoint = library.create_version(book, kind='pre_integrity_repair')
        library.verify_book_unchanged(book)
        target = Path(book.path) / relative
        self._atomic_write_bytes(target, payload)
        if not self._valid_recovery_candidate(library, book, relative, target):
            library.refresh_book_revision(book)
            raise IOError(f'Herstelcontrole mislukt voor {relative}; herstel is niet als geslaagd gemarkeerd.')
        library.refresh_book_revision(book)
        return checkpoint['id']
