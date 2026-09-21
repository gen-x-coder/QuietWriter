THEMES = {
    'Helder': {
        'bg': '#f4f5f7', 'panel': '#ffffff', 'panel2': '#eef0f2', 'text': '#20242a',
        'muted': '#727983', 'border': '#d8dde3', 'accent': '#4d738f', 'editor': '#ffffff',
        'hero': '#263744', 'hero_text': '#ffffff', 'select': '#e4eef4',
    },
    'Warm': {
        'bg': '#f4f1ea', 'panel': '#fbf8f1', 'panel2': '#ebe4d8', 'text': '#2c2924',
        'muted': '#777066', 'border': '#d8cfbf', 'accent': '#7c6954', 'editor': '#fffdf8',
        'hero': '#3c342d', 'hero_text': '#fffaf2', 'select': '#ebe1d1',
    },
    'Papier': {
        'bg': '#ece9df', 'panel': '#f7f4ea', 'panel2': '#e3ddd0', 'text': '#26231f',
        'muted': '#746e64', 'border': '#d1cabb', 'accent': '#6d7764', 'editor': '#fdfaf0',
        'hero': '#394137', 'hero_text': '#fbfaf4', 'select': '#e3e7dc',
    },
    'Nacht': {
        'bg': '#17191c', 'panel': '#202328', 'panel2': '#292d33', 'text': '#e6e8eb',
        'muted': '#9ca3ad', 'border': '#343941', 'accent': '#7ca6c2', 'editor': '#1d2024',
        'hero': '#11181e', 'hero_text': '#f4f7f9', 'select': '#2d3942',
    },
    'Grafiet': {
        'bg': '#1d1f21', 'panel': '#26292c', 'panel2': '#303438', 'text': '#e7e7e7',
        'muted': '#a0a4a8', 'border': '#3c4146', 'accent': '#9ba8b2', 'editor': '#232629',
        'hero': '#181a1c', 'hero_text': '#f2f2f2', 'select': '#363a3e',
    },
    'Middernacht': {
        'bg': '#111722', 'panel': '#17202d', 'panel2': '#202b3a', 'text': '#e4e9f0',
        'muted': '#97a4b4', 'border': '#2c394a', 'accent': '#7fa2c9', 'editor': '#141c27',
        'hero': '#0c121b', 'hero_text': '#f2f6fb', 'select': '#233247',
    },
}


def stylesheet(name: str) -> str:
    t = THEMES.get(name, THEMES['Helder'])
    return f'''
    QWidget {{ background: {t['bg']}; color: {t['text']}; font-family: "Segoe UI"; font-size: 13px; }}
    QMainWindow, QDialog {{ background: {t['bg']}; }}
    QFrame#panel, QWidget#panel {{ background: {t['panel']}; border: 0; }}
    QFrame#toolrail {{ background: {t['panel2']}; border: 0; }}
    QFrame#editorTopbar {{ background: {t['panel']}; border-bottom: 1px solid {t['border']}; }}
    QLabel#muted {{ color: {t['muted']}; }}
    QLabel#title {{ font-size: 24px; font-weight: 600; }}
    QLabel#sectionTitle {{ font-size: 14px; font-weight: 600; }}
    QLabel#bookTitleLabel {{ font-size: 14px; font-weight: 500; }}
    QLabel#heroTitle {{ color: {t['hero_text']}; font-size: 30px; font-weight: 700; background: transparent; }}
    QLabel#heroSubtitle {{ color: {t['hero_text']}; font-size: 15px; background: transparent; }}
    QFrame#bookshelfHero {{ background: {t['hero']}; border: 0; min-height: 185px; }}
    QFrame#bookCard, QFrame#newBookCard {{ background: {t['panel']}; border: 1px solid {t['border']}; border-radius: 10px; }}
    QLabel#bookCoverTitle {{ font-family: Georgia; font-size: 22px; background: transparent; }}
    QLabel#newBookPlus {{ font-size: 42px; color: {t['accent']}; background: transparent; }}
    QPushButton {{ background: transparent; border: 1px solid {t['border']}; border-radius: 6px; padding: 7px 10px; }}
    QPushButton:hover {{ background: {t['panel2']}; }}
    QPushButton#railButton {{ border: 0; border-radius: 7px; padding: 8px; }}
    QPushButton#railButton:checked {{ background: {t['select']}; }}
    QPushButton#navButton {{ border: 0; border-radius: 7px; padding: 8px 10px; text-align: left; font-weight: 600; }}
    QPushButton#navButton:hover {{ background: {t['panel']}; }}
    QPushButton#navButton:checked {{ background: {t['select']}; color: {t['text']}; }}
    QPushButton#compactButton {{ border: 0; padding: 5px; min-width: 28px; }}
    QPushButton#thinkingButton {{ border: 0; color: {t['muted']}; text-align: left; padding: 4px 0; }}
    QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
        background: {t['editor']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 6px; padding: 6px;
    }}
    QLineEdit#chapterTitle {{ font-family: "Segoe UI"; font-size: 25px; font-weight: 650; border: 0; padding: 34px 44px 16px 44px; background: {t['editor']}; }}
    QTextEdit#editor {{ border: 0; padding: 28px 44px; font-family: Georgia; font-size: 17px; line-height: 1.5; }}
    QTextEdit#storyReader {{ border: 0; padding: 20px 26px; font-family: Georgia; font-size: 16px; }}
    QTextEdit#thinkingDetails {{ background: {t['panel2']}; color: {t['muted']}; font-size: 12px; }}
    QListWidget, QTreeWidget {{ background: {t['panel']}; color: {t['text']}; border: 0; outline: 0; }}
    QListWidget::item, QTreeWidget::item {{ padding: 8px 7px; border-radius: 4px; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: {t['select']}; color: {t['text']}; }}
    QSplitter::handle {{ background: {t['border']}; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; }}
    QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 5px; min-height: 24px; }}
    '''
