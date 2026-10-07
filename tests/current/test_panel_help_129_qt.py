import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
PySide6 = pytest.importorskip('PySide6')
pytestmark = pytest.mark.qt

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quietwriter.ui.panel_help import PanelHelp, panel_help_key


def _app():
    return QApplication.instance() or QApplication([])


def test_panel_help_persists_dismiss_and_question_reopens(tmp_path):
    _app()
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    help_widget = PanelHelp(settings, 'search', 'Zoeken', 'Uitleg voor zoeken.')
    help_widget.show(); QApplication.processEvents()
    assert help_widget.block.isVisible()
    QTest.mouseClick(help_widget.ok, PySide6.QtCore.Qt.LeftButton)
    assert settings.value(panel_help_key('search'), False, bool) is True
    assert not help_widget.block.isVisible()
    QTest.mouseClick(help_widget.toggle, PySide6.QtCore.Qt.LeftButton)
    assert help_widget.block.isVisible()
    assert settings.value(panel_help_key('search'), True, bool) is False


def test_panel_help_wraps_at_narrow_width(tmp_path):
    _app()
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    widget = PanelHelp(settings, 'search', 'Zoeken', 'Een langere uitleg die op een smal paneel over meerdere regels moet lopen zonder afgekapt te worden.')
    widget.resize(300, 300); widget.show(); QApplication.processEvents(); QTest.qWait(20)
    assert widget.text.height() >= widget.text.heightForWidth(widget.text.width())


def test_panel_help_recomputes_wrapped_height_after_narrow_resize(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.IniFormat)
    text = ('Posez une question sur votre texte, ou sélectionnez un passage et choisissez une action rapide. '
            'La réponse s’affiche ici ; votre manuscrit ne change que si vous le modifiez vous-même. '
            'Sous Contexte, vous voyez ce qui est envoyé.')
    widget = PanelHelp(settings, 'ai', 'Assistant de lecture', text)
    widget.resize(300, 500)
    widget.show()
    app.processEvents()
    QTest.qWait(20)
    assert widget.text.height() >= widget.text.heightForWidth(widget.text.width())
    widget.close()


def test_ai_panel_help_and_notice_fit_when_opened_narrow(tmp_path):
    from quietwriter.i18n import current_locale, set_locale
    from quietwriter.storage import Library
    from quietwriter.ui.main_window import MainWindow

    app = _app()
    original = current_locale()
    try:
        for language in ('nl', 'en', 'de', 'fr', 'es'):
            set_locale(language)
            root = tmp_path / language
            library = Library(root / 'library')
            book = library.create_book('Testboek')
            settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
            settings.setValue('ai_enabled', True)
            window = MainWindow(settings, library, [])
            window.open_book(book)
            window.resize(1024, 683)
            window.show(); app.processEvents()
            window.editor_page.show_ai(); app.processEvents(); QTest.qWait(20)
            ai = window.editor_page.ai
            assert ai.panel_help.text.height() >= ai.panel_help.text.heightForWidth(ai.panel_help.text.width())
            ai.context_panel.show(); app.processEvents(); QTest.qWait(20)
            assert ai.chapter_planning_notice.height() >= ai.chapter_planning_notice.heightForWidth(ai.chapter_planning_notice.width())
            window.close()
    finally:
        set_locale(original)
