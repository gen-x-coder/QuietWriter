THEMES = {
    'Helder': {
        'bg': '#f4f5f7', 'panel': '#ffffff', 'panel2': '#eef0f2', 'text': '#20242a',
        'muted': '#727983', 'border': '#d8dde3', 'accent': '#4d738f', 'editor': '#ffffff',
    },
    'Warm': {
        'bg': '#f4f1ea', 'panel': '#fbf8f1', 'panel2': '#ebe4d8', 'text': '#2c2924',
        'muted': '#777066', 'border': '#d8cfbf', 'accent': '#7c6954', 'editor': '#fffdf8',
    },
    'Papier': {
        'bg': '#ece9df', 'panel': '#f7f4ea', 'panel2': '#e3ddd0', 'text': '#26231f',
        'muted': '#746e64', 'border': '#d1cabb', 'accent': '#6d7764', 'editor': '#fdfaf0',
    },
    'Nacht': {
        'bg': '#17191c', 'panel': '#202328', 'panel2': '#292d33', 'text': '#e6e8eb',
        'muted': '#9ca3ad', 'border': '#343941', 'accent': '#7ca6c2', 'editor': '#1d2024',
    },
    'Grafiet': {
        'bg': '#1d1f21', 'panel': '#26292c', 'panel2': '#303438', 'text': '#e7e7e7',
        'muted': '#a0a4a8', 'border': '#3c4146', 'accent': '#9ba8b2', 'editor': '#232629',
    },
    'Middernacht': {
        'bg': '#111722', 'panel': '#17202d', 'panel2': '#202b3a', 'text': '#e4e9f0',
        'muted': '#97a4b4', 'border': '#2c394a', 'accent': '#7fa2c9', 'editor': '#141c27',
    },
}


def stylesheet(name: str) -> str:
    t = THEMES.get(name, THEMES['Helder'])
    return f'''
    QWidget {{ background: {t['bg']}; color: {t['text']}; font-size: 13px; }}
    QMainWindow, QDialog {{ background: {t['bg']}; }}
    QFrame#panel, QWidget#panel {{ background: {t['panel']}; border: 0; }}
    QFrame#toolrail {{ background: {t['panel2']}; border: 0; }}
    QLabel#muted {{ color: {t['muted']}; }}
    QLabel#title {{ font-size: 24px; font-weight: 600; }}
    QLabel#sectionTitle {{ font-size: 14px; font-weight: 600; }}
    QPushButton {{ background: transparent; border: 1px solid {t['border']}; border-radius: 6px; padding: 7px 10px; }}
    QPushButton:hover {{ background: {t['panel2']}; }}
    QPushButton#railButton {{ border: 0; border-radius: 6px; padding: 9px; font-size: 16px; }}
    QPushButton#railButton:checked {{ background: {t['panel']}; }}
    QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
        background: {t['editor']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 6px; padding: 6px;
    }}
    QTextEdit#editor {{ border: 0; padding: 28px 44px; font-size: 17px; }}
    QListWidget, QTreeWidget {{ background: {t['panel']}; color: {t['text']}; border: 0; outline: 0; }}
    QListWidget::item, QTreeWidget::item {{ padding: 6px; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: {t['panel2']}; color: {t['text']}; }}
    QTabWidget::pane {{ border: 0; }}
    QTabBar::tab {{ padding: 8px 12px; border: 0; }}
    QTabBar::tab:selected {{ background: {t['panel2']}; }}
    QSplitter::handle {{ background: {t['border']}; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; }}
    QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 5px; min-height: 24px; }}
    '''
