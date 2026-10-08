from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from .revisions import FileRevision, file_revision
from .storage import _safe_atomic_write_text

SCHEMA_VERSION = 1
DEFAULT_SHELF_NAME = 'Werk in uitvoering'
DEFAULT_SHELF_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, 'quietwriter:default-shelf:v1'))


class ShelfLibraryError(RuntimeError):
    """Base error for workspace-level bookshelf metadata."""


class ShelfLibraryCorruptError(ShelfLibraryError):
    """The canonical bookshelf metadata cannot be trusted."""

    def __init__(self, path: Path, message: str):
        self.path = Path(path)
        super().__init__(f'{self.path.name}: {message}')


class ShelfLibraryFutureVersionError(ShelfLibraryCorruptError):
    """A newer QuietWriter owns this bookshelf format."""


class ShelfLibraryConflictError(ShelfLibraryError):
    """The file kept changing while applying one user operation."""


@dataclass(frozen=True)
class Shelf:
    id: str
    name: str
    private: bool = False


@dataclass(frozen=True)
class ShelfLibraryState:
    schema_version: int
    default_shelf_id: str
    shelves: tuple[Shelf, ...]
    book_shelves: dict[str, str]

    def shelf(self, shelf_id: str) -> Shelf | None:
        return next((s for s in self.shelves if s.id == shelf_id), None)

    def shelf_for_book(self, book_id: str) -> Shelf | None:
        shelf_id = self.book_shelves.get(str(book_id))
        return self.shelf(shelf_id) if shelf_id else None


@dataclass(frozen=True)
class ShelfLibraryLoadResult:
    state: ShelfLibraryState
    source: str  # canonical | last_good | emergency
    problem: str = ''


class ShelfLibraryStore:
    """Canonical workspace-level shelf metadata.

    The relationship lives outside book.json on purpose. Shelf operations are
    replayed on the newest disk revision before an atomic write, so a second
    QuietWriter instance or a sync client cannot be silently overwritten by a
    stale in-memory copy.
    """

    def __init__(self, root: Path, books_dir: Path | None = None, trash_dir: Path | None = None):
        self.root = Path(root)
        self.books_dir = Path(books_dir) if books_dir is not None else self.root / 'books'
        self.trash_dir = Path(trash_dir) if trash_dir is not None else self.root / 'trash'
        self.path = self.root / 'library.json'
        self.last_good_path = self.root / '.cache' / 'library.last-good.json'
        # This lock serializes processes on *this computer* only. Keeping it out
        # of the workspace prevents OneDrive/Dropbox from synchronising an
        # ephemeral lock to another machine.
        lock_key = hashlib.sha1(str(self.root.resolve()).casefold().encode('utf-8')).hexdigest()[:20]
        self.lock_path = Path(tempfile.gettempdir()) / f'quietwriter-library-{lock_key}.lock'

    # ---------- load / migration ----------

    def load(self, *, migrate_if_missing: bool = True) -> ShelfLibraryLoadResult:
        if not self.path.exists():
            # A surviving last-good copy means this is not a pristine 1.2 workspace.
            # Never silently remigrate here: that could make a private book public.
            if self.last_good_path.exists():
                try:
                    state = self._read_state_file(self.last_good_path, strict_mappings=False)
                    return ShelfLibraryLoadResult(state, 'last_good', 'library.json ontbreekt')
                except ShelfLibraryError as exc:
                    emergency = self._initial_state(self._discover_all_book_ids())
                    return ShelfLibraryLoadResult(emergency, 'emergency', str(exc))
            # Missing shelf metadata can also mean that a second computer has
            # only received the book folders so far. Queries therefore never
            # publish a migration. Keep the would-be migration in memory until
            # an explicit user operation needs to write shelf metadata.
            state = self._initial_state(self._discover_all_book_ids())
            source = 'pending_migration' if migrate_if_missing else 'emergency'
            return ShelfLibraryLoadResult(state, source, 'library.json ontbreekt')

        try:
            state = self._read_state_file(self.path, strict_mappings=False)
            return ShelfLibraryLoadResult(state, 'canonical')
        except ShelfLibraryFutureVersionError as exc:
            emergency = self._initial_state(self._discover_all_book_ids())
            return ShelfLibraryLoadResult(emergency, 'future', str(exc))
        except ShelfLibraryCorruptError as exc:
            try:
                state = self._read_state_file(self.last_good_path, strict_mappings=False)
                return ShelfLibraryLoadResult(state, 'last_good', str(exc))
            except ShelfLibraryError:
                emergency = self._initial_state(self._discover_all_book_ids())
                return ShelfLibraryLoadResult(emergency, 'emergency', str(exc))

    def _write_initial_if_still_missing(self, state: ShelfLibraryState) -> None:
        # Migration is the one sanctioned automatic write. Re-check immediately
        # before publishing so another instance that won the race is preserved.
        if self.path.exists():
            return
        self._write_state(state)

    def _initial_state(self, book_ids: Iterable[str] = ()) -> ShelfLibraryState:
        shelf_id = DEFAULT_SHELF_ID
        ids = tuple(dict.fromkeys(str(value).strip() for value in book_ids if str(value).strip()))
        return ShelfLibraryState(
            schema_version=SCHEMA_VERSION,
            default_shelf_id=shelf_id,
            shelves=(Shelf(shelf_id, DEFAULT_SHELF_NAME, False),),
            book_shelves={book_id: shelf_id for book_id in ids},
        )

    def _discover_all_book_ids(self) -> list[str]:
        ids: list[str] = []
        for base in (self.books_dir, self.trash_dir / 'books'):
            if not base.exists():
                continue
            for manifest in base.glob('*/book.json'):
                if manifest.parent.name.startswith('.'):
                    continue
                try:
                    raw = json.loads(manifest.read_text(encoding='utf-8-sig'))
                    book_id = str(raw.get('id') or '').strip() if isinstance(raw, dict) else ''
                    if book_id:
                        ids.append(book_id)
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    continue
        return list(dict.fromkeys(ids))

    # ---------- public queries ----------

    def state(self) -> ShelfLibraryState:
        return self.load().state

    def effective_shelf_id(self, book_id: str, *, demo_mode: bool = False, loaded: ShelfLibraryLoadResult | None = None) -> str | None:
        """Return the effective shelf without repairing/writing missing metadata.

        Normal mode treats an unmapped/invalid book as being on the default shelf
        in memory. Demo mode fails closed and returns None instead.
        """
        loaded = loaded or self.load()
        if demo_mode and loaded.source != 'canonical':
            return None
        state = loaded.state
        mapped = state.book_shelves.get(str(book_id))
        valid_ids = {s.id for s in state.shelves}
        if mapped in valid_ids:
            return mapped
        return None if demo_mode else state.default_shelf_id

    def visible_shelf_ids(self, *, demo_mode: bool = False, loaded: ShelfLibraryLoadResult | None = None) -> tuple[str, ...]:
        loaded = loaded or self.load()
        if demo_mode and loaded.source != 'canonical':
            return ()
        state = loaded.state
        return tuple(s.id for s in state.shelves if not (demo_mode and s.private))

    def visible_book_ids(self, book_ids: Iterable[str], *, demo_mode: bool = False, loaded: ShelfLibraryLoadResult | None = None) -> set[str]:
        loaded = loaded or self.load()
        if demo_mode and loaded.source != 'canonical':
            return set()
        state = loaded.state
        shelves = {s.id: s for s in state.shelves}
        visible: set[str] = set()
        for raw_id in book_ids:
            book_id = str(raw_id)
            mapped = state.book_shelves.get(book_id)
            if mapped not in shelves:
                if demo_mode:
                    continue
                mapped = state.default_shelf_id
            shelf = shelves.get(mapped)
            if shelf is not None and not (demo_mode and shelf.private):
                visible.add(book_id)
        return visible

    # ---------- user operations ----------

    def create_shelf(self, name: str, *, private: bool = False) -> Shelf:
        clean_name = self._clean_name(name)
        new_shelf = Shelf(str(uuid.uuid4()), clean_name, bool(private))

        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            return self._replace(state, shelves=state.shelves + (new_shelf,))

        self._apply_operation(mutate)
        return new_shelf

    def rename_shelf(self, shelf_id: str, name: str) -> ShelfLibraryState:
        clean_name = self._clean_name(name)

        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            self._require_shelf(state, shelf_id)
            shelves = tuple(Shelf(s.id, clean_name if s.id == shelf_id else s.name, s.private) for s in state.shelves)
            return self._replace(state, shelves=shelves)

        return self._apply_operation(mutate)

    def set_private(self, shelf_id: str, private: bool) -> ShelfLibraryState:
        private = bool(private)

        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            self._require_shelf(state, shelf_id)
            if shelf_id == state.default_shelf_id and private:
                raise ValueError('De standaardplank kan niet privé worden gemaakt.')
            shelves = tuple(Shelf(s.id, s.name, private if s.id == shelf_id else s.private) for s in state.shelves)
            return self._replace(state, shelves=shelves)

        return self._apply_operation(mutate)

    def move_book(self, book_id: str, shelf_id: str) -> ShelfLibraryState:
        book_id = self._require_book_id(book_id)

        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            self._require_shelf(state, shelf_id)
            mapping = dict(state.book_shelves)
            mapping[book_id] = shelf_id
            return self._replace(state, book_shelves=mapping)

        return self._apply_operation(mutate)

    def assign_new(self, book_id: str) -> ShelfLibraryState:
        """Assign an imported/created/restored book if it has no valid mapping.

        A retained mapping (notably for trash restore or a re-imported historical
        identity) wins when its shelf still exists.
        """
        book_id = self._require_book_id(book_id)

        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            valid = {s.id for s in state.shelves}
            mapping = dict(state.book_shelves)
            if mapping.get(book_id) not in valid:
                mapping[book_id] = state.default_shelf_id
            return self._replace(state, book_shelves=mapping)

        return self._apply_operation(mutate)

    def forget(self, book_id: str) -> ShelfLibraryState:
        book_id = self._require_book_id(book_id)

        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            mapping = dict(state.book_shelves)
            mapping.pop(book_id, None)
            return self._replace(state, book_shelves=mapping)

        return self._apply_operation(mutate)

    def forget_many(self, book_ids: Iterable[str]) -> ShelfLibraryState:
        ids = {str(value).strip() for value in book_ids if str(value).strip()}

        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            mapping = {book_id: shelf_id for book_id, shelf_id in state.book_shelves.items() if book_id not in ids}
            return self._replace(state, book_shelves=mapping)

        return self._apply_operation(mutate)

    def delete_shelf(self, shelf_id: str) -> ShelfLibraryState:
        def mutate(state: ShelfLibraryState) -> ShelfLibraryState:
            self._require_shelf(state, shelf_id)
            if shelf_id == state.default_shelf_id:
                raise ValueError('De standaardplank kan niet worden verwijderd.')
            shelves = tuple(s for s in state.shelves if s.id != shelf_id)
            mapping = {
                book_id: (state.default_shelf_id if mapped == shelf_id else mapped)
                for book_id, mapped in state.book_shelves.items()
            }
            return self._replace(state, shelves=shelves, book_shelves=mapping)

        return self._apply_operation(mutate)

    # ---------- persistence / validation ----------

    def _apply_operation(self, operation: Callable[[ShelfLibraryState], ShelfLibraryState], *, attempts: int = 3) -> ShelfLibraryState:
        # Shelf edits are explicit user actions. A missing canonical file with a
        # surviving recovery copy must be repaired explicitly before edits. A
        # truly new/1.2 workspace stays in-memory until we are inside this lock.
        if not self.path.exists() and self.last_good_path.exists():
            raise ShelfLibraryCorruptError(self.path, 'library.json ontbreekt; herstel eerst de plankindeling')

        last_revision: FileRevision | None = None
        with self._local_lock():
            for _ in range(max(1, attempts)):
                try:
                    if self.path.exists():
                        state, revision = self._read_canonical()
                    else:
                        state = self._initial_state(self._discover_all_book_ids())
                        revision = None
                    candidate = self._validated(operation(copy.deepcopy(state)), strict_mappings=True)
                    last_revision = revision
                    self._write_state(candidate, expected_revision=revision)
                    # A sync client may have replaced the file immediately after our
                    # atomic write. Verify what is actually on disk before success.
                    written, _ = self._read_canonical()
                    if self._render(written) != self._render(candidate):
                        continue
                    return candidate
                except ShelfLibraryConflictError:
                    continue
        raise ShelfLibraryConflictError(f'{self.path.name} veranderde tijdens de bewerking (laatste revisie: {last_revision}).')

    @contextmanager
    def _local_lock(self, *, timeout: float = 5.0, stale_after: float = 30.0):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + timeout
        fd = None
        while fd is None:
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f'{os.getpid()} {time.time()}\n'.encode('ascii', errors='ignore'))
            except FileExistsError:
                try:
                    age = time.time() - self.lock_path.stat().st_mtime
                    if age > stale_after:
                        self.lock_path.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise ShelfLibraryConflictError('De plankindeling is tijdelijk in gebruik door een andere QuietWriter-instantie.')
                time.sleep(0.02)
        try:
            yield
        finally:
            try:
                if fd is not None:
                    os.close(fd)
            finally:
                try:
                    self.lock_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def _guard_recovery_against_future_schema(self) -> None:
        if not self.path.exists():
            return
        try:
            self._read_state_file(self.path, strict_mappings=False)
        except ShelfLibraryFutureVersionError:
            raise
        except ShelfLibraryCorruptError:
            return

    def restore_from_last_good(self) -> ShelfLibraryState:
        self._guard_recovery_against_future_schema()
        state = self._read_state_file(self.last_good_path, strict_mappings=True)
        with self._local_lock():
            # Explicit recovery action: replacing an absent/corrupt canonical file is intended.
            payload = self._render(state)
            _safe_atomic_write_text(self.path, payload)
            _safe_atomic_write_text(self.last_good_path, payload)
        return state

    def reset_to_default(self, book_ids: Iterable[str] | None = None) -> ShelfLibraryState:
        self._guard_recovery_against_future_schema()
        ids = self._discover_all_book_ids() if book_ids is None else list(book_ids)
        state = self._initial_state(ids)
        with self._local_lock():
            payload = self._render(state)
            _safe_atomic_write_text(self.path, payload)
            _safe_atomic_write_text(self.last_good_path, payload)
        return state

    def describe_problem(self) -> str:
        loaded = self.load()
        return loaded.problem

    def _write_state(self, state: ShelfLibraryState, expected_revision: FileRevision | None = None) -> None:
        state = self._validated(state, strict_mappings=True)
        if expected_revision is not None or self.path.exists():
            if file_revision(self.path) != expected_revision:
                raise ShelfLibraryConflictError(f'{self.path.name} is buiten QuietWriter gewijzigd.')
        payload = self._render(state)
        _safe_atomic_write_text(self.path, payload)
        try:
            _safe_atomic_write_text(self.last_good_path, payload)
        except OSError:
            pass

    def _read_canonical(self) -> tuple[ShelfLibraryState, FileRevision | None]:
        state = self._read_state_file(self.path, strict_mappings=True)
        return state, file_revision(self.path)

    def _read_state_file(self, path: Path, *, strict_mappings: bool = True) -> ShelfLibraryState:
        path = Path(path)
        if not path.exists():
            raise ShelfLibraryCorruptError(path, 'bestand ontbreekt')
        try:
            raw = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ShelfLibraryCorruptError(path, 'ongeldige of onleesbare JSON') from exc
        if not isinstance(raw, dict):
            raise ShelfLibraryCorruptError(path, 'root moet een JSON-object zijn')
        version = raw.get('schema_version')
        if not isinstance(version, int):
            raise ShelfLibraryCorruptError(path, 'schema_version ontbreekt of is ongeldig')
        if version > SCHEMA_VERSION:
            raise ShelfLibraryFutureVersionError(path, f'schema {version} is nieuwer dan ondersteund schema {SCHEMA_VERSION}')
        if version != SCHEMA_VERSION:
            raise ShelfLibraryCorruptError(path, f'schema {version} wordt niet ondersteund')
        shelves_raw = raw.get('shelves')
        mapping_raw = raw.get('book_shelves')
        if not isinstance(shelves_raw, list) or not isinstance(mapping_raw, dict):
            raise ShelfLibraryCorruptError(path, 'shelves of book_shelves heeft een ongeldig type')
        shelves: list[Shelf] = []
        for item in shelves_raw:
            if not isinstance(item, dict):
                raise ShelfLibraryCorruptError(path, 'een plank is geen object')
            shelf_id = str(item.get('id') or '').strip()
            name = str(item.get('name') or '').strip()
            private = item.get('private', False)
            if not shelf_id or not name or not isinstance(private, bool):
                raise ShelfLibraryCorruptError(path, 'plank bevat ongeldige velden')
            shelves.append(Shelf(shelf_id, name, private))
        mapping: dict[str, str] = {}
        for key, value in mapping_raw.items():
            book_id = str(key).strip()
            shelf_id = str(value).strip()
            if not book_id or not shelf_id:
                raise ShelfLibraryCorruptError(path, 'book_shelves bevat een lege sleutel of waarde')
            mapping[book_id] = shelf_id
        state = ShelfLibraryState(version, str(raw.get('default_shelf_id') or '').strip(), tuple(shelves), mapping)
        try:
            return self._validated(state, strict_mappings=strict_mappings)
        except ValueError as exc:
            raise ShelfLibraryCorruptError(path, str(exc)) from exc

    def _validated(self, state: ShelfLibraryState, *, strict_mappings: bool = True) -> ShelfLibraryState:
        if state.schema_version != SCHEMA_VERSION:
            raise ValueError(f'Onverwacht schema {state.schema_version}.')
        if not state.shelves:
            raise ValueError('Er moet minimaal één plank bestaan.')
        ids = [s.id for s in state.shelves]
        if len(ids) != len(set(ids)):
            raise ValueError('Plank-id komt meer dan één keer voor.')
        if any(not s.id.strip() or not s.name.strip() for s in state.shelves):
            raise ValueError('Plank-id en planknaam mogen niet leeg zijn.')
        default = next((s for s in state.shelves if s.id == state.default_shelf_id), None)
        if default is None:
            raise ValueError('De standaardplank bestaat niet.')
        if default.private:
            raise ValueError('De standaardplank mag niet privé zijn.')
        valid_ids = set(ids)
        if strict_mappings and any(shelf_id not in valid_ids for shelf_id in state.book_shelves.values()):
            raise ValueError('Een boek verwijst naar een onbekende plank.')
        return state

    def _replace(self, state: ShelfLibraryState, *, shelves=None, book_shelves=None, default_shelf_id=None) -> ShelfLibraryState:
        return ShelfLibraryState(
            schema_version=state.schema_version,
            default_shelf_id=state.default_shelf_id if default_shelf_id is None else default_shelf_id,
            shelves=state.shelves if shelves is None else tuple(shelves),
            book_shelves=state.book_shelves if book_shelves is None else dict(book_shelves),
        )

    @staticmethod
    def _render(state: ShelfLibraryState) -> str:
        payload = {
            'schema_version': state.schema_version,
            'default_shelf_id': state.default_shelf_id,
            'shelves': [
                {'id': shelf.id, 'name': shelf.name, 'private': shelf.private}
                for shelf in state.shelves
            ],
            'book_shelves': dict(sorted(state.book_shelves.items())),
        }
        return json.dumps(payload, ensure_ascii=False, indent=2) + '\n'

    @staticmethod
    def _clean_name(name: str) -> str:
        value = str(name or '').strip()
        if not value:
            raise ValueError('Een planknaam mag niet leeg zijn.')
        if len(value) > 120:
            raise ValueError('Een planknaam mag maximaal 120 tekens bevatten.')
        return value

    @staticmethod
    def _require_book_id(book_id: str) -> str:
        value = str(book_id or '').strip()
        if not value:
            raise ValueError('Boek-id ontbreekt.')
        return value

    @staticmethod
    def _require_shelf(state: ShelfLibraryState, shelf_id: str) -> Shelf:
        shelf = state.shelf(str(shelf_id))
        if shelf is None:
            raise KeyError(f'Onbekende plank: {shelf_id}')
        return shelf
