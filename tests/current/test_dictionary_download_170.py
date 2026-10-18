"""1.7.0: woordenboeken installeren zonder handwerk.

Niet getest: de echte download van GitHub vanuit de app en de snelheid op een
trage verbinding. De bestanden in de lijst zijn bij het bouwen wel echt
opgehaald en hun SHA-256 is gecontroleerd tegen raw.githubusercontent.com.
"""
from __future__ import annotations

import hashlib
import io
import os
import time
from pathlib import Path

import pytest

from quietwriter import dictionary_download as dd
from quietwriter.dictionary_catalog import DictionaryCatalog


def _entry(locale='xx_XX', payloads=None):
    payloads = payloads or {'dic': b'2\nappel\npeer\n', 'aff': b'SET UTF-8\n', 'lic': b'Licentie\n'}
    files = (
        dd.RemoteFile('xx/xx.dic', f'{locale}.dic', hashlib.sha256(payloads['dic']).hexdigest(), len(payloads['dic'])),
        dd.RemoteFile('xx/xx.aff', f'{locale}.aff', hashlib.sha256(payloads['aff']).hexdigest(), len(payloads['aff'])),
        dd.RemoteFile('xx/LICENSE', f'LICENSE-{locale}.txt', hashlib.sha256(payloads['lic']).hexdigest(), len(payloads['lic'])),
    )
    return dd.CatalogDictionary(locale, 'Test', 'MIT', files), payloads


class _Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def _opener(served: dict[str, bytes], calls=None):
    def opener(request, timeout=60):
        url = request.full_url
        if calls is not None:
            calls.append(url)
        for suffix, data in served.items():
            if url.endswith(suffix):
                return _Response(data)
        raise OSError('niet gevonden')
    return opener


def test_catalog_is_pinned_https_and_uses_safe_local_names():
    assert len(dd.SOURCE_COMMIT) == 40 and dd.RAW_BASE.startswith('https://raw.githubusercontent.com/LibreOffice/dictionaries/')
    for entry in dd.CATALOG:
        names = {f.local for f in entry.files}
        assert names == {f'{entry.locale}.dic', f'{entry.locale}.aff', f'LICENSE-{entry.locale}.txt'}
        assert all(len(f.sha256) == 64 and f.size > 0 for f in entry.files)
        assert entry.license and entry.author
    assert {'nl_NL', 'en_GB', 'en_US', 'de_DE', 'fr_FR', 'es_ES'} <= set(dd.CATALOG_BY_LOCALE)


def test_install_verifies_and_places_files(tmp_path):
    entry, data = _entry()
    seen = []
    target = dd.install(entry, tmp_path, progress=seen.append,
                        opener=_opener({'xx.dic': data['dic'], 'xx.aff': data['aff'], 'LICENSE': data['lic']}))
    assert target == tmp_path / 'xx_XX'
    assert (target / 'xx_XX.dic').read_bytes() == data['dic']
    assert dd.installed_marker(tmp_path, 'xx_XX')['commit'] == dd.SOURCE_COMMIT
    assert seen[-1] == 100 and dd.is_installed(tmp_path, 'xx_XX')
    assert [p.name for p in tmp_path.iterdir()] == ['xx_XX']               # geen tijdelijke mappen over


@pytest.mark.parametrize('bad', ['changed', 'too_big'])
def test_wrong_download_installs_nothing_and_keeps_the_old_one(tmp_path, bad):
    entry, data = _entry()
    good = _opener({'xx.dic': data['dic'], 'xx.aff': data['aff'], 'LICENSE': data['lic']})
    dd.install(entry, tmp_path, opener=good)
    wrong = data['dic'].replace(b'peer', b'paer') if bad == 'changed' else data['dic'] + b'x' * 10
    with pytest.raises(dd.DownloadFailed):
        dd.install(entry, tmp_path, opener=_opener({'xx.dic': wrong, 'xx.aff': data['aff'], 'LICENSE': data['lic']}))
    assert (tmp_path / 'xx_XX' / 'xx_XX.dic').read_bytes() == data['dic']   # oude blijft
    assert [p.name for p in tmp_path.iterdir()] == ['xx_XX']


def test_cancel_and_network_error_leave_nothing_behind(tmp_path):
    entry, data = _entry()
    with pytest.raises(dd.DownloadCancelled):
        dd.install(entry, tmp_path, cancelled=lambda: True,
                   opener=_opener({'xx.dic': data['dic'], 'xx.aff': data['aff'], 'LICENSE': data['lic']}))
    with pytest.raises(OSError):
        dd.install(entry, tmp_path, opener=_opener({}))
    assert list(tmp_path.iterdir()) == []


def test_dropbox_holding_a_file_briefly_is_retried(tmp_path, monkeypatch):
    # 1.7.0-dev10: in een Dropbox-werkmap gaf de eerste start "WinError 5 Toegang geweigerd"
    # bij het hernoemen van de downloadmap. Nu: downloaden buiten de werkmap, per bestand
    # plaatsen, en een korte blokkade opnieuw proberen.
    entry, data = _entry()
    real_replace = dd.os.replace
    refusals = {'left': 3}

    def flaky(src, dst):
        if refusals['left']:
            refusals['left'] -= 1
            raise PermissionError(5, 'Toegang geweigerd')
        return real_replace(src, dst)
    monkeypatch.setattr(dd.os, 'replace', flaky)
    monkeypatch.setattr(dd.time, 'sleep', lambda s: None)
    staging = tmp_path / 'systeemtemp'; staging.mkdir()
    root = tmp_path / 'Dropbox' / 'dictionaries'
    dd.install(entry, root, staging_parent=staging,
               opener=_opener({'xx.dic': data['dic'], 'xx.aff': data['aff'], 'LICENSE': data['lic']}))
    assert (root / 'xx_XX' / 'xx_XX.dic').read_bytes() == data['dic']
    assert sorted(p.name for p in (root / 'xx_XX').iterdir()) == ['LICENSE-xx_XX.txt', dd.MARKER, 'xx_XX.aff', 'xx_XX.dic']
    assert list(staging.iterdir()) == []      # niets in de werkmap of tijdelijke map achtergebleven


def test_permanent_refusal_puts_the_old_dictionary_back(tmp_path, monkeypatch):
    entry, data = _entry()
    good = _opener({'xx.dic': data['dic'], 'xx.aff': data['aff'], 'LICENSE': data['lic']})
    dd.install(entry, tmp_path, opener=good)
    newer = data['dic'] + b'appel\n'
    import hashlib as _h
    files = list(entry.files)
    files[0] = dd.RemoteFile('xx/xx.dic', 'xx_XX.dic', _h.sha256(newer).hexdigest(), len(newer))
    entry2 = dd.CatalogDictionary('xx_XX', 'Test', 'MIT', tuple(files))
    real_replace = dd.os.replace

    def refuse_dic(src, dst):
        if str(dst).endswith('.dic'):
            raise PermissionError(5, 'Toegang geweigerd')
        return real_replace(src, dst)
    monkeypatch.setattr(dd.os, 'replace', refuse_dic)
    monkeypatch.setattr(dd.time, 'sleep', lambda s: None)
    with pytest.raises(PermissionError):
        dd.install(entry2, tmp_path, opener=_opener({'xx.dic': newer, 'xx.aff': data['aff'], 'LICENSE': data['lic']}))
    folder = tmp_path / 'xx_XX'
    assert (folder / 'xx_XX.dic').read_bytes() == data['dic']
    assert not [p for p in folder.iterdir() if p.name.endswith('.tmp')]


def test_catalog_scan_ignores_partial_downloads_and_remove_cleans_up(tmp_path):
    entry, data = _entry('nl_NL')
    dd.install(entry, tmp_path, opener=_opener({'xx.dic': data['dic'], 'xx.aff': data['aff'], 'LICENSE': data['lic']}))
    partial = tmp_path / '.download-de_DE-1234'; partial.mkdir()
    (partial / 'de_DE.dic').write_text('1\nhalb\n', encoding='utf-8')
    catalog = DictionaryCatalog(tmp_path, extra_roots=[])
    locales = {e.locale for e in catalog.entries() if e.source == 'Werkmap'}
    assert locales == {'nl_NL'}
    assert catalog.remove_custom('nl_NL')
    assert not (tmp_path / 'nl_NL').exists()


@pytest.mark.qt
def test_dialog_downloads_in_background_and_reports(tmp_path):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.dictionary_download_dialog import DictionaryDownloadDialog
    app = QApplication.instance() or QApplication([])
    calls = []

    def fake_install(entry, root, progress=None, cancelled=None):
        calls.append(entry.locale)
        progress(50)
        (Path(root) / entry.locale).mkdir(parents=True, exist_ok=True)
        (Path(root) / entry.locale / f'{entry.locale}.dic').write_text('1\nx\n', encoding='utf-8')
        (Path(root) / entry.locale / f'{entry.locale}.aff').write_text('SET UTF-8\n', encoding='utf-8')
        return Path(root) / entry.locale

    dialog = DictionaryDownloadDialog(tmp_path, installer=fake_install, preselect='de_DE')
    assert dialog.selected().locale == 'de_DE'
    dialog.start_download()
    end = time.monotonic() + 5
    while dialog.installed_locale is None and time.monotonic() < end:
        app.processEvents(); time.sleep(0.01)
    assert dialog.installed_locale == 'de_DE' and calls == ['de_DE']
    assert dialog.download_btn.isEnabled() and dialog.download_btn.text() != ''
    assert '✓' in dialog.list.currentItem().text()

    def failing(entry, root, progress=None, cancelled=None):
        raise dd.DownloadFailed('controle mislukt')
    dialog.installer = failing
    dialog.start_download()
    end = time.monotonic() + 5
    while dialog.worker is not None and time.monotonic() < end:
        app.processEvents(); time.sleep(0.01)
    assert 'controle mislukt' in dialog.status.text()


# --- Instellingen > Spelling na de feedback van Lucas (dev8) ---------------------------

def test_language_and_country_names_follow_the_app_language():
    from quietwriter import i18n
    from quietwriter.dictionary_catalog import locale_label
    before = i18n.current_locale() if hasattr(i18n, 'current_locale') else None
    try:
        i18n.set_locale('en')
        assert locale_label('de_DE') == 'German — Germany'
        assert locale_label('pt_BR') == 'Portuguese — Brazil'
        i18n.set_locale('de')
        assert locale_label('nl_NL') == 'Niederländisch — Niederlande'
        i18n.set_locale('nl')
        assert locale_label('en_GB') == 'Engels — Verenigd Koninkrijk'
        assert locale_label('xx_YY') == 'xx_YY'
    finally:
        i18n.set_locale(before or 'nl')


def _dic(folder: Path, locale: str):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{locale}.dic').write_text('1\nx\n', encoding='utf-8')
    (folder / f'{locale}.aff').write_text('SET UTF-8\n', encoding='utf-8')


@pytest.mark.qt
def test_settings_choose_dictionary_first_then_its_languages(tmp_path, monkeypatch):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from quietwriter.storage import Library
    from quietwriter.ui import settings_page as sp
    from quietwriter.ui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    office = tmp_path / 'office'
    _dic(office / 'fr_FR', 'fr_FR'); _dic(office / 'nl_NL', 'nl_NL')
    monkeypatch.setattr(sp, 'DictionaryCatalog', lambda ws: DictionaryCatalog(ws, extra_roots=[(office, 'ONLYOFFICE')]))
    lib = Library(tmp_path / 'workspace')
    _dic(lib.root / 'dictionaries' / 'de_DE', 'de_DE')
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(lib.root))
    settings.setValue('spell_language', 'nl_NL'); settings.setValue('spell_dictionary_source', 'ONLYOFFICE')
    window = MainWindow(settings, lib, [])
    window.open_settings()
    page = window.settings_page
    page.refresh_dictionaries()
    sources = [page.spell_dictionary_source.itemData(i) for i in range(page.spell_dictionary_source.count())]
    assert sources == ['Werkmap', 'ONLYOFFICE']
    assert page.spell_dictionary_source.currentData() == 'ONLYOFFICE'
    languages = [page.spell_language.itemData(i) for i in range(page.spell_language.count())]
    assert sorted(languages) == ['fr_FR', 'nl_NL'] and page.spell_language.currentData() == 'nl_NL'
    page.spell_dictionary_source.setCurrentIndex(0)
    assert [page.spell_language.itemData(i) for i in range(page.spell_language.count())] == ['de_DE']
    # Geen technische regel met bron, code en bestandspad meer.
    assert page.dictionary_info.isHidden() and page.dictionary_info.text() == ''
    window.close()
    assert app is not None


@pytest.mark.qt
def test_remove_dialog_lists_only_quietwriter_dictionaries(tmp_path):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.dictionary_remove_dialog import DictionaryRemoveDialog
    app = QApplication.instance() or QApplication([])
    _dic(tmp_path / 'de_DE', 'de_DE'); _dic(tmp_path / 'sv_SE', 'sv_SE')
    (tmp_path / 'sv_SE' / dd.MARKER).write_text('{"author": "Göran", "license": "LGPL"}', encoding='utf-8')
    dialog = DictionaryRemoveDialog(tmp_path, preselect='sv_SE')
    texts = [dialog.list.item(i).text() for i in range(dialog.list.count())]
    assert len(texts) == 2 and any('Göran' in t for t in texts)
    assert dialog.selected_locale() == 'sv_SE'
    dialog.remove_selected()
    assert dialog.removed == ['sv_SE'] and not (tmp_path / 'sv_SE').exists()
    assert (tmp_path / 'de_DE' / 'de_DE.dic').exists() and dialog.list.count() == 1
    dialog.remove_selected()
    assert dialog.list.isHidden() and not dialog.empty.isHidden() and not dialog.remove_btn.isEnabled()
    assert app is not None


@pytest.mark.qt
def test_first_run_offers_found_dictionaries_or_a_download(tmp_path, monkeypatch):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui import first_run_wizard as frw
    from quietwriter.ui import dictionary_download_dialog as ddd
    app = QApplication.instance() or QApplication([])
    office = tmp_path / 'office'
    roots = []
    monkeypatch.setattr(frw, 'DictionaryCatalog', lambda ws, create=True: DictionaryCatalog(ws, extra_roots=list(roots), create=create))
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(tmp_path / 'ws'))

    # Niets op deze computer: geen lege keuzelijsten, wel de uitleg en de downloadknop.
    wizard = frw.FirstRunWizard(settings, tmp_path / 'ws')
    assert wizard.spell_found.isHidden() and not wizard.spell_none.isHidden()
    assert not wizard.spell_enabled.isEnabled() and not wizard.spell_enabled.isChecked()

    class FakeDownload:
        def __init__(self, root, parent=None, preselect=None):
            self.root = Path(root); self.preselect = preselect; self.installed_locale = None
        def exec(self):
            _dic(self.root / self.preselect, self.preselect); self.installed_locale = self.preselect
    monkeypatch.setattr(ddd, 'DictionaryDownloadDialog', FakeDownload)
    wizard._download_dictionary()
    assert not wizard.spell_found.isHidden() and wizard.spell_enabled.isChecked()
    assert wizard.spell_source.currentData() == 'Werkmap' and wizard.spell_language.currentData() == 'nl_NL'

    # Office-woordenboeken gevonden: eerst het woordenboek, dan de talen daarin.
    _dic(office / 'en_GB', 'en_GB'); _dic(office / 'fr_FR', 'fr_FR')
    roots.append((office, 'LibreOffice'))
    wizard._populate_dictionaries('fr_FR', '')
    assert [wizard.spell_source.itemData(i) for i in range(wizard.spell_source.count())] == ['Werkmap', 'LibreOffice']
    assert wizard.spell_source.currentData() == 'LibreOffice' and wizard.spell_language.currentData() == 'fr_FR'
    assert wizard._commit(tour_seen=False)
    assert settings.value('spell_dictionary_source') == 'LibreOffice' and settings.value('spell_language') == 'fr_FR'
    assert app is not None
