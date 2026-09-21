from __future__ import annotations

from PySide6.QtGui import QFontDatabase

# QuietWriter gebruikt één semantisch designsysteem. Thema's wijzigen alleen de
# tokens; widgets hoeven daardoor nooit thema-specifieke kleuren te kennen.
THEMES = {
    'Helder': {
        'bg': '#f4f5f7', 'panel': '#ffffff', 'panel2': '#eef1f4', 'editor': '#ffffff',
        'text': '#20242a', 'muted': '#707985', 'disabled': '#a8afb8',
        'border': '#dce1e6', 'border_subtle': '#e9edf0',
        'accent': '#4d738f', 'accent_hover': '#3f647f', 'accent_soft': '#e5eef4',
        'select': '#e5eef4', 'hover': '#f2f5f7', 'focus': '#6f95af',
        'success': '#49775c', 'success_soft': '#e9f2ec',
        'warning': '#8a6a2f', 'warning_soft': '#fff6df',
        'danger': '#a75555', 'danger_soft': '#f8eaea',
        'hero': '#263744', 'hero_text': '#ffffff',
        'history': '#465563', 'history_text': '#ffffff',
        'cover1': '#dfe5e9', 'cover2': '#cbd5dc', 'cover3': '#d5dde2',
    },
    'Warm': {
        'bg': '#f4f1ea', 'panel': '#fbf8f1', 'panel2': '#ece5da', 'editor': '#fffdf8',
        'text': '#2c2924', 'muted': '#777066', 'disabled': '#aaa397',
        'border': '#d9d0c2', 'border_subtle': '#e8e1d6',
        'accent': '#7c6954', 'accent_hover': '#685642', 'accent_soft': '#eee3d6',
        'select': '#eee3d6', 'hover': '#f7f1e8', 'focus': '#927a61',
        'success': '#60735a', 'success_soft': '#edf2e9',
        'warning': '#8b6b37', 'warning_soft': '#fff4dc',
        'danger': '#9a5a52', 'danger_soft': '#f7e9e6',
        'hero': '#3c342d', 'hero_text': '#fffaf2',
        'history': '#594f45', 'history_text': '#fffaf2',
        'cover1': '#e3ddd2', 'cover2': '#d3c9ba', 'cover3': '#ddd4c7',
    },
    'Papier': {
        'bg': '#ece9df', 'panel': '#f7f4ea', 'panel2': '#e5dfd2', 'editor': '#fdfaf0',
        'text': '#26231f', 'muted': '#746e64', 'disabled': '#aaa397',
        'border': '#d2cbbc', 'border_subtle': '#e3ddd1',
        'accent': '#6d7764', 'accent_hover': '#586250', 'accent_soft': '#e3e8dc',
        'select': '#e3e8dc', 'hover': '#f1eee5', 'focus': '#7f8a74',
        'success': '#63755d', 'success_soft': '#eaf0e5',
        'warning': '#836b3c', 'warning_soft': '#f7efd9',
        'danger': '#92594f', 'danger_soft': '#f3e6e2',
        'hero': '#394137', 'hero_text': '#fbfaf4',
        'history': '#4f574b', 'history_text': '#fbfaf4',
        'cover1': '#ded9cd', 'cover2': '#cbc4b5', 'cover3': '#d6d0c2',
    },
    'Nacht': {
        'bg': '#17191c', 'panel': '#202328', 'panel2': '#292d33', 'editor': '#1d2024',
        'text': '#e6e8eb', 'muted': '#9ca3ad', 'disabled': '#676e77',
        'border': '#353a42', 'border_subtle': '#2a2e34',
        'accent': '#7ca6c2', 'accent_hover': '#93bad2', 'accent_soft': '#293943',
        'select': '#2d3942', 'hover': '#272b31', 'focus': '#8bb4cf',
        'success': '#79a58a', 'success_soft': '#25362b',
        'warning': '#c8a765', 'warning_soft': '#3b3324',
        'danger': '#d07a7a', 'danger_soft': '#40292b',
        'hero': '#11181e', 'hero_text': '#f4f7f9',
        'history': '#263848', 'history_text': '#f4f7f9',
        'cover1': '#2b3035', 'cover2': '#32383e', 'cover3': '#252a2f',
    },
    'Grafiet': {
        'bg': '#1d1f21', 'panel': '#26292c', 'panel2': '#303438', 'editor': '#232629',
        'text': '#e7e7e7', 'muted': '#a0a4a8', 'disabled': '#6f7478',
        'border': '#3c4146', 'border_subtle': '#303438',
        'accent': '#9ba8b2', 'accent_hover': '#b0bbc3', 'accent_soft': '#353b40',
        'select': '#363a3e', 'hover': '#2e3235', 'focus': '#aab5bd',
        'success': '#86a18e', 'success_soft': '#2e3931',
        'warning': '#c1a16d', 'warning_soft': '#3c3427',
        'danger': '#c87d78', 'danger_soft': '#422d2b',
        'hero': '#181a1c', 'hero_text': '#f2f2f2',
        'history': '#343a3f', 'history_text': '#f5f5f5',
        'cover1': '#303438', 'cover2': '#3a3f44', 'cover3': '#2b2f33',
    },
    'Middernacht': {
        'bg': '#111722', 'panel': '#17202d', 'panel2': '#202b3a', 'editor': '#141c27',
        'text': '#e4e9f0', 'muted': '#97a4b4', 'disabled': '#607087',
        'border': '#2c394a', 'border_subtle': '#202b39',
        'accent': '#7fa2c9', 'accent_hover': '#96b5d7', 'accent_soft': '#21324a',
        'select': '#233247', 'hover': '#1c2735', 'focus': '#90afd1',
        'success': '#78a18b', 'success_soft': '#21352d',
        'warning': '#c3a367', 'warning_soft': '#393122',
        'danger': '#cb777b', 'danger_soft': '#3e292e',
        'hero': '#0c121b', 'hero_text': '#f2f6fb',
        'history': '#24354b', 'history_text': '#f2f6fb',
        'cover1': '#1f2a37', 'cover2': '#283649', 'cover3': '#1a2532',
    },
}

EDITOR_FONTS = ('Merriweather', 'Georgia')


def resolved_editor_font(preferred: str | None = None) -> str:
    preferred = (preferred or 'Merriweather').strip() or 'Merriweather'
    available = {f.casefold(): f for f in QFontDatabase.families()}
    if preferred.casefold() in available:
        return available[preferred.casefold()]
    if 'merriweather' in available:
        return available['merriweather']
    if 'georgia' in available:
        return available['georgia']
    return QFontDatabase.systemFont(QFontDatabase.GeneralFont).family()


def stylesheet(name: str, editor_font: str = 'Merriweather') -> str:
    t = THEMES.get(name, THEMES['Helder'])
    # QSS ondersteunt een CSS-achtige fallbacklijst. Merriweather is de voorkeur;
    # Georgia blijft een veilige Windows-fallback wanneer het font niet aanwezig is.
    font_stack = f'"{editor_font}", "Merriweather", Georgia, serif'
    return f'''
    QWidget {{ background: {t['bg']}; color: {t['text']}; font-family: "Segoe UI Variable", "Segoe UI"; font-size: 13px; }}
    QMainWindow, QDialog {{ background: {t['bg']}; }}
    QToolTip {{ background: {t['panel']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 6px 8px; }}

    QFrame#panel, QWidget#panel {{ background: {t['panel']}; border: 0; }}
    QFrame#toolrail {{ background: {t['panel2']}; border: 0; }}
    QFrame#editorTopbar {{ background: {t['panel']}; border-bottom: 1px solid {t['border_subtle']}; }}
    QFrame#historyBanner {{ background: {t['history']}; border: 0; }}
    QLabel#historyBannerLabel {{ color: {t['history_text']}; background: transparent; font-weight: 600; }}
    QPushButton#restoreButton {{ background: {t['accent']}; color: {t['hero_text']}; border: 0; font-weight: 600; }}
    QPushButton#restoreButton:hover {{ background: {t['accent_hover']}; }}
    QPushButton#historyExitButton {{ background: {t['panel']}; color: {t['text']}; border: 1px solid {t['border']}; font-weight: 600; }}
    QPushButton#historyExitButton:hover {{ background: {t['hover']}; }}
    QLabel#syncWarning {{ background: {t['warning_soft']}; color: {t['warning']}; border: 1px solid {t['warning']}; border-radius: 8px; padding: 9px; }}

    QLabel#muted {{ color: {t['muted']}; }}
    QLabel#title {{ font-size: 24px; font-weight: 600; }}
    QLabel#sectionTitle {{ font-size: 14px; font-weight: 600; }}
    QLabel#bookTitleLabel {{ font-size: 13px; font-weight: 500; color: {t['muted']}; }}
    QLabel#autosaveStatus {{ color: {t['muted']}; font-size: 12px; }}
    QLabel#heroTitle {{ color: {t['hero_text']}; font-size: 30px; font-weight: 700; background: transparent; }}
    QLabel#heroSubtitle {{ color: {t['hero_text']}; font-size: 15px; background: transparent; }}
    QLabel#sectionHeader {{ color: {t['muted']}; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; }}
    QFrame#bookshelfHero {{ background: {t['hero']}; border: 0; min-height: 185px; }}
    QFrame#bookCard, QFrame#newBookCard {{ background: {t['panel']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; }}
    QFrame#bookCard:hover, QFrame#newBookCard:hover {{ border: 1px solid {t['border']}; }}
    QLabel#bookCoverTitle {{ font-family: {font_stack}; font-size: 22px; background: transparent; }}
    QLabel#newBookPlus {{ font-size: 42px; color: {t['accent']}; background: transparent; }}

    QPushButton {{ background: transparent; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 8px 12px; }}
    QPushButton:hover {{ background: {t['hover']}; border-color: {t['focus']}; }}
    QPushButton:pressed {{ background: {t['select']}; }}
    QPushButton:disabled {{ color: {t['disabled']}; border-color: {t['border_subtle']}; background: transparent; }}
    QPushButton#primaryButton {{ background: {t['accent']}; color: {t['hero_text']}; border: 1px solid {t['accent']}; font-weight: 600; }}
    QPushButton#primaryButton:hover {{ background: {t['accent_hover']}; border-color: {t['accent_hover']}; }}
    QPushButton#secondaryButton {{ background: {t['panel']}; }}
    QPushButton#dangerButton {{ color: {t['danger']}; border-color: {t['danger']}; }}
    QPushButton#dangerButton:hover {{ background: {t['danger_soft']}; color: {t['danger']}; }}
    QPushButton#railButton {{ border: 0; border-left: 3px solid transparent; border-radius: 8px; padding: 8px; }}
    QPushButton#railButton:hover {{ background: {t['hover']}; }}
    QPushButton#railButton:checked {{ background: {t['accent_soft']}; border-left: 3px solid {t['accent']}; color: {t['accent']}; }}
    QPushButton#navButton {{ border: 0; border-left: 3px solid transparent; border-radius: 8px; padding: 8px 10px; text-align: left; font-weight: 600; }}
    QPushButton#navButton:hover {{ background: {t['hover']}; }}
    QPushButton#navButton:checked {{ background: {t['accent_soft']}; border-left: 3px solid {t['accent']}; color: {t['accent']}; }}
    QPushButton#compactButton {{ border: 0; padding: 5px; min-width: 28px; }}
    QPushButton#thinkingButton {{ border: 0; color: {t['muted']}; text-align: left; padding: 4px 0; }}
    QPushButton#suggestionButton {{ border: 0; border-radius: 8px; padding: 5px 8px; text-align: left; min-height: 26px; max-height: 32px; }}
    QPushButton#suggestionButton:hover {{ background: {t['hover']}; }}
    QPushButton#suggestionButton:checked {{ background: {t['accent_soft']}; }}
    QPushButton#aiActionButton {{ background: {t['accent']}; color: {t['hero_text']}; border: 0; border-radius: 18px; padding: 0; }}
    QPushButton#aiActionButton:hover {{ background: {t['accent_hover']}; }}

    QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
        background: {t['editor']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 8px; padding: 7px 9px; selection-background-color: {t['accent']};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {t['focus']}; }}
    QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {{ color: {t['disabled']}; background: {t['panel2']}; }}
    QLineEdit#chapterTitle {{ font-family: {font_stack}; font-size: 27px; font-weight: 600; border: 0; border-bottom: 1px solid transparent; padding: 34px 44px 16px 44px; background: {t['editor']}; }}
    QLineEdit#chapterTitle:focus {{ border: 0; border-bottom: 1px solid {t['accent']}; }}
    QTextEdit#editor {{ border: 0; padding: 30px 44px; font-family: {font_stack}; font-size: 17px; font-weight: 300; line-height: 1.6; }}
    QTextEdit#storyReader {{ border: 0; padding: 22px 28px; font-family: {font_stack}; font-size: 16px; font-weight: 300; }}
    QTextEdit#thinkingDetails {{ background: {t['panel2']}; color: {t['muted']}; font-size: 12px; }}
    QTextBrowser#aiChat {{ background: transparent; border: 0; padding: 2px; }}
    QTextEdit#aiInput {{ border-radius: 14px; padding: 10px 12px; background: {t['editor']}; }}

    QListWidget, QTreeWidget {{ background: {t['panel']}; color: {t['text']}; border: 0; outline: 0; }}
    QListWidget::item, QTreeWidget::item {{ padding: 8px 8px; border-radius: 6px; }}
    QListWidget::item:hover, QTreeWidget::item:hover {{ background: {t['hover']}; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: {t['accent_soft']}; color: {t['text']}; }}
    QTreeWidget#manuscriptTree::item:selected {{ border-left: 3px solid {t['accent']}; }}

    QTabWidget::pane {{ border: 1px solid {t['border_subtle']}; border-radius: 8px; background: {t['panel']}; }}
    QTabBar::tab {{ background: transparent; padding: 9px 14px; color: {t['muted']}; border-bottom: 2px solid transparent; }}
    QTabBar::tab:selected {{ color: {t['text']}; border-bottom: 2px solid {t['accent']}; }}
    QTabBar::tab:hover {{ color: {t['text']}; }}

    QSplitter::handle:horizontal {{ width: 7px; background: transparent; border-left: 1px solid {t['border_subtle']}; }}
    QSplitter::handle:horizontal:hover {{ border-left: 2px solid {t['accent']}; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {t['muted']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QStatusBar {{ background: {t['bg']}; color: {t['muted']}; border-top: 1px solid {t['border_subtle']}; }}
    QMenu {{ background: {t['panel']}; border: 1px solid {t['border']}; padding: 6px; }}
    QMenu::item {{ padding: 7px 24px 7px 10px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {t['accent_soft']}; }}
    '''
