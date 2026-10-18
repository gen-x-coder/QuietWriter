"""1.7.0-dev14: woordenboeken bijwerken en 23 talen erbij.

De nieuwe bestanden zijn bij het bouwen opgehaald van raw.githubusercontent.com
(vaste commit) en hun SHA-256 en grootte zijn gecontroleerd; de test zelf gaat
niet online.
"""
from __future__ import annotations

import hashlib
import io
import os

import pytest

from quietwriter import dictionary_download as dd
from quietwriter.dictionary_catalog import locale_label
from quietwriter.i18n import set_locale


def _entry(locale, dic=b'2\nappel\npeer\n', aff=b'SET UTF-8\n'):
    lic = b'Licentie\n'
    files = tuple(
        dd.RemoteFile(f'xx/{name}', local, hashlib.sha256(data).hexdigest(), len(data))
        for name, local, data in (('xx.dic', f'{locale}.dic', dic), ('xx.aff', f'{locale}.aff', aff), ('LICENSE', f'LICENSE-{locale}.txt', lic))
    )
    return dd.CatalogDictionary(locale, 'Test', 'MIT', files), {'dic': dic, 'aff': aff, 'lic': lic}


class _Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def _opener(payloads):
    def opener(request, timeout=60):
        for key, data in payloads.items():
            if request.full_url.endswith({'dic': '.dic', 'aff': '.aff', 'lic': 'LICENSE'}[key]):
                return _Response(data)
        raise OSError('niet gevonden')
    return opener


def test_catalog_has_35_unique_languages_with_real_names():
    set_locale('nl')
    locales = [entry.locale for entry in dd.CATALOG]
    assert len(locales) == 35 and len(set(locales)) == 35
    assert {'de_AT', 'de_CH', 'en_AU', 'en_CA', 'en_ZA', 'es_MX', 'es_AR', 'cs_CZ', 'sk_SK', 'ro_RO',
            'ca_ES', 'gl_ES', 'hr_HR', 'sl_SI', 'bg_BG', 'ru_RU', 'uk_UA', 'lt_LT', 'lv_LV', 'et_EE',
            'af_ZA', 'is_IS', 'id_ID'} <= set(locales)
    # Bewust niet: te zwaar voor spylls of onleesbaar.
    assert not {'hu_HU', 'nb_NO', 'nn_NO', 'el_GR', 'tr_TR'} & set(locales)
    for entry in dd.CATALOG:
        assert locale_label(entry.locale) != entry.locale, entry.locale   # nette naam, geen code
    remotes = [f.remote for entry in dd.CATALOG for f in entry.files]
    assert all('..' not in r and not r.startswith('/') for r in remotes)


def test_update_available_only_for_downloaded_and_changed(tmp_path):
    old, old_data = _entry('xx_XX')
    dd.install(old, tmp_path, opener=_opener(old_data), staging_parent=tmp_path)
    assert dd.update_available(tmp_path, old) is False
    # Een nieuwere QuietWriter heeft een nieuwere .dic in de lijst.
    new, new_data = _entry('xx_XX', dic=b'3\nappel\npeer\nbes\n')
    assert dd.update_available(tmp_path, new) is True
    dd.install(new, tmp_path, opener=_opener(new_data), staging_parent=tmp_path)
    assert dd.update_available(tmp_path, new) is False
    assert (tmp_path / 'xx_XX' / 'xx_XX.dic').read_bytes() == new_data['dic']


def test_own_dictionary_without_marker_is_never_updated(tmp_path):
    entry, _data = _entry('yy_YY')
    folder = tmp_path / 'yy_YY'; folder.mkdir()
    (folder / 'yy_YY.dic').write_bytes(b'1\neigen\n'); (folder / 'yy_YY.aff').write_bytes(b'SET UTF-8\n')
    assert dd.update_available(tmp_path, entry) is False
    assert dd.update_available(tmp_path / 'leeg', entry) is False


def test_freshly_installed_catalog_dictionary_has_no_update(tmp_path, monkeypatch):
    real = dd.CATALOG_BY_LOCALE['af_ZA']
    fake = []
    payload = {}
    for remote in real.files:
        data = os.urandom(8)
        payload[remote.local] = data
        fake.append(dd.RemoteFile(remote.remote, remote.local, hashlib.sha256(data).hexdigest(), len(data)))
    entry = dd.CatalogDictionary(real.locale, real.author, real.license, tuple(fake))
    def opener(request, timeout=60):
        local = next(f.local for f in fake if request.full_url.endswith(f.remote))
        return _Response(payload[local])
    dd.install(entry, tmp_path, opener=opener, staging_parent=tmp_path)
    monkeypatch.setattr(dd, 'CATALOG', (entry,))
    assert dd.updates_available(tmp_path) == []
    monkeypatch.setattr(dd, 'CATALOG', (real,))
    assert dd.updates_available(tmp_path) == [real]


@pytest.fixture
def qt():
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def test_dialog_sorts_by_name_and_offers_update(qt, tmp_path, monkeypatch):
    set_locale('nl')
    from quietwriter.ui import dictionary_download_dialog as dialog_module
    old, data = _entry('nl_NL')
    dd.install(old, tmp_path, opener=_opener(data), staging_parent=tmp_path)
    dialog = dialog_module.DictionaryDownloadDialog(tmp_path)
    try:
        labels = [entry.label for entry in dialog.entries]
        assert labels == sorted(labels, key=str.casefold)
        # De echte nl_NL in de lijst heeft andere controlesommen: bijwerken.
        assert dialog.selected().locale == 'nl_NL'
        assert dialog.download_btn.text() == 'Bijwerken'
        row = [e.locale for e in dialog.entries].index('nl_NL')
        assert 'nieuwere versie' in dialog.list.item(row).text()
        dialog.list.setCurrentRow([e.locale for e in dialog.entries].index('af_ZA'))
        assert dialog.download_btn.text() == 'Downloaden'
    finally:
        dialog.close()


def test_settings_spelling_mentions_update(qt, tmp_path):
    set_locale('nl')
    from PySide6.QtCore import QSettings
    from quietwriter.storage import Library
    from quietwriter.ui.main_window import MainWindow
    workspace = tmp_path / 'ws'
    library = Library(workspace)
    old, data = _entry('nl_NL')
    dd.install(old, workspace / 'dictionaries', opener=_opener(data), staging_parent=tmp_path)
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(workspace))
    window = MainWindow(settings, library, [])
    try:
        page = window.settings_page
        page.root.setText(str(workspace))
        page.update_dictionary_info()
        assert 'nieuwere versie van: Nederlands — Nederland' in page.dictionary_info.text()
        assert not page.dictionary_info.isHidden()
    finally:
        window.close()
