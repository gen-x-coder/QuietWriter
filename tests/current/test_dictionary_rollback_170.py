"""ChatGPT-review dev15: terugzetten bij een mislukte woordenboekupdate is atomair en eerlijk."""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path

import pytest

from quietwriter import dictionary_download as dd


def _entry(locale, dic, aff, lic=b'Licentie\n'):
    files = tuple(
        dd.RemoteFile(f'xx/{name}', local, hashlib.sha256(data).hexdigest(), len(data))
        for name, local, data in (('xx.dic', f'{locale}.dic', dic), ('xx.aff', f'{locale}.aff', aff),
                                  ('LICENSE', f'LICENSE-{locale}.txt', lic))
    )
    return dd.CatalogDictionary(locale, 'Test', 'MIT', files), {'xx.dic': dic, 'xx.aff': aff, 'LICENSE': lic}


class _Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def _opener(payloads):
    def opener(request, timeout=60):
        for name, data in payloads.items():
            if request.full_url.endswith(name):
                return _Response(data)
        raise OSError('niet gevonden')
    return opener


def _snapshot(folder: Path):
    return {p.name: p.read_bytes() for p in sorted(folder.iterdir())}


@pytest.fixture
def installed(tmp_path, monkeypatch):
    monkeypatch.setattr(dd.time, 'sleep', lambda _s: None)
    root = tmp_path / 'dictionaries'
    old, data = _entry('xx_XX', b'2\nappel\npeer\n', b'SET UTF-8\n')
    dd.install(old, root, opener=_opener(data), staging_parent=tmp_path)
    new, new_data = _entry('xx_XX', b'3\nappel\npeer\nbes\n', b'SET UTF-8\nTRY abc\n', b'Nieuwe licentie\n')
    return root, new, new_data, _snapshot(root / 'xx_XX')


def test_failed_update_puts_every_previous_file_back(installed, monkeypatch, tmp_path):
    root, new, data, before = installed
    real_replace = os.replace

    def failing_replace(src, dst):
        if str(dst).endswith('xx_XX.dic') and '.tmp' in str(src):
            raise PermissionError('vastgehouden')           # .aff staat dan al nieuw op zijn plek
        return real_replace(src, dst)

    monkeypatch.setattr(dd.os, 'replace', failing_replace)
    with pytest.raises(PermissionError):
        dd.install(new, root, opener=_opener(data), staging_parent=tmp_path)
    assert _snapshot(root / 'xx_XX') == before                 # ook geen .tmp of .vorige over


def test_failed_rollback_says_so_and_keeps_the_backup(installed, monkeypatch, tmp_path):
    root, new, data, before = installed
    real_replace = os.replace
    state = {'rolling_back': False}

    def failing_replace(src, dst):
        if str(dst).endswith('xx_XX.dic'):
            state['rolling_back'] = True                 # .dic blijft vastgehouden
            raise PermissionError('vastgehouden')
        if state['rolling_back'] and str(dst).endswith('xx_XX.aff'):
            raise PermissionError('ook terugzetten lukt niet')
        return real_replace(src, dst)

    monkeypatch.setattr(dd.os, 'replace', failing_replace)
    with pytest.raises(dd.RollbackIncomplete) as caught:
        dd.install(new, root, opener=_opener(data), staging_parent=tmp_path)
    backups = caught.value.backups
    assert backups and all(b.exists() for b in backups)
    assert any(b.read_bytes() == before['xx_XX.aff'] for b in backups)   # het oude .aff staat veilig
    assert 'niet helemaal terug' in str(caught.value)


def test_failed_first_install_leaves_nothing_behind(tmp_path, monkeypatch):
    monkeypatch.setattr(dd.time, 'sleep', lambda _s: None)
    root = tmp_path / 'dictionaries'
    entry, data = _entry('yy_YY', b'1\nwoord\n', b'SET UTF-8\n')
    real_replace = os.replace

    def failing_replace(src, dst):
        if str(dst).endswith('yy_YY.dic'):
            raise PermissionError('vastgehouden')
        return real_replace(src, dst)

    monkeypatch.setattr(dd.os, 'replace', failing_replace)
    with pytest.raises(PermissionError):
        dd.install(entry, root, opener=_opener(data), staging_parent=tmp_path)
    assert not any((root / 'yy_YY').iterdir())


def test_successful_update_leaves_no_backups(installed, tmp_path):
    root, new, data, _before = installed
    dd.install(new, root, opener=_opener(data), staging_parent=tmp_path)
    names = {p.name for p in (root / 'xx_XX').iterdir()}
    assert not any(n.endswith(('.vorige', '.tmp')) for n in names)
    assert (root / 'xx_XX' / 'xx_XX.dic').read_bytes() == data['xx.dic']


def test_dialog_tells_the_truth_when_rollback_failed(tmp_path):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from quietwriter.i18n import set_locale
    from quietwriter.ui.dictionary_download_dialog import DictionaryDownloadDialog
    app = QApplication.instance() or QApplication([])
    set_locale('nl')

    def installer(entry, root, **_kwargs):
        raise dd.RollbackIncomplete('kapot', [tmp_path / '.x.vorige'])

    dialog = DictionaryDownloadDialog(tmp_path, installer=installer)
    try:
        dialog.start_download()
        for _ in range(50):
            app.processEvents()
            if dialog.worker is None:
                break
            dialog.worker.thread.join(0.05)
        app.processEvents()
        assert 'niet helemaal worden teruggezet' in dialog.status.text()
        assert 'niets veranderd' not in dialog.status.text()
    finally:
        dialog.close()


def test_half_written_temporary_file_is_cleaned_up(installed, monkeypatch, tmp_path):
    root, new, data, before = installed
    real_copy = dd.shutil.copyfile

    def failing_copy(src, dst):
        if str(dst).endswith('.tmp') and 'xx_XX.dic' in str(dst):
            Path(dst).write_bytes(b'half')                    # half geschreven
            raise OSError('schijf vol')
        return real_copy(src, dst)

    monkeypatch.setattr(dd.shutil, 'copyfile', failing_copy)
    with pytest.raises(OSError):
        dd.install(new, root, opener=_opener(data), staging_parent=tmp_path)
    assert _snapshot(root / 'xx_XX') == before                 # geen .tmp, alles terug
