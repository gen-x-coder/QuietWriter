from __future__ import annotations

from pathlib import Path


# QuietWriter gebruikt één semantisch designsysteem. Thema's wijzigen alleen de
# tokens; widgets hoeven daardoor nooit thema-specifieke kleuren te kennen.
THEMES = {'Helder': {'bg': '#f4f5f7',
            'panel': '#ffffff',
            'panel2': '#eef1f4',
            'editor': '#ffffff',
            'text': '#20242a',
            'muted': '#606b76',
            'disabled': '#a8afb8',
            'border': '#dce1e6',
            'border_subtle': '#e9edf0',
            'accent': '#4d738f',
            'accent_hover': '#3f647f',
            'accent_soft': '#e5eef4',
            'accent_text': '#ffffff',
            'select': '#e5eef4',
            'hover': '#f2f5f7',
            'focus': '#6487a1',
            'success': '#49775c',
            'success_soft': '#e9f2ec',
            'warning': '#8a6a2f',
            'warning_soft': '#fff6df',
            'danger': '#9d4c4c',
            'danger_soft': '#f8eaea',
            'hero': '#263744',
            'hero_text': '#ffffff',
            'history': '#465563',
            'history_text': '#ffffff',
            'cover1': '#dfe5e9',
            'cover2': '#cbd5dc',
            'cover3': '#d5dde2'},
 'Porselein': {'bg': '#f5f7f9',
               'panel': '#ffffff',
               'panel2': '#eef2f5',
               'editor': '#ffffff',
               'text': '#1f2933',
               'muted': '#5f6d7a',
               'disabled': '#98a3ae',
               'border': '#d7dee5',
               'border_subtle': '#e8edf1',
               'accent': '#476f8f',
               'accent_hover': '#385f7d',
               'accent_soft': '#e4eef5',
               'accent_text': '#ffffff',
               'select': '#e4eef5',
               'hover': '#f0f4f7',
               'focus': '#5f88a8',
               'success': '#3f7354',
               'success_soft': '#e8f2ec',
               'warning': '#7a5a1f',
               'warning_soft': '#fff4dc',
               'danger': '#944248',
               'danger_soft': '#f9e9ea',
               'hero': '#243746',
               'hero_text': '#ffffff',
               'history': '#405565',
               'history_text': '#ffffff',
               'cover1': '#dfe6ec',
               'cover2': '#cdd8e0',
               'cover3': '#d6dfe6'},
 'Nevel': {'bg': '#eef3f7',
           'panel': '#f8fbfd',
           'panel2': '#e4ebf1',
           'editor': '#fbfdff',
           'text': '#22303c',
           'muted': '#586977',
           'disabled': '#929eaa',
           'border': '#d0dae3',
           'border_subtle': '#e0e7ed',
           'accent': '#4f7698',
           'accent_hover': '#416785',
           'accent_soft': '#dfeaf3',
           'accent_text': '#ffffff',
           'select': '#dfeaf3',
           'hover': '#edf3f7',
           'focus': '#6488a5',
           'success': '#47745a',
           'success_soft': '#e5f0e9',
           'warning': '#795b26',
           'warning_soft': '#fff3da',
           'danger': '#94484c',
           'danger_soft': '#f8e7e8',
           'hero': '#2a4052',
           'hero_text': '#ffffff',
           'history': '#435d72',
           'history_text': '#ffffff',
           'cover1': '#d7e1e9',
           'cover2': '#c3d1dc',
           'cover3': '#cfdbe4'},
 'Salie': {'bg': '#f1f5f1',
           'panel': '#fbfdfb',
           'panel2': '#e6eee7',
           'editor': '#fdfefd',
           'text': '#243029',
           'muted': '#59685e',
           'disabled': '#94a098',
           'border': '#d2ddd4',
           'border_subtle': '#e3e9e4',
           'accent': '#557562',
           'accent_hover': '#466452',
           'accent_soft': '#e1ece4',
           'accent_text': '#ffffff',
           'select': '#e1ece4',
           'hover': '#eff4f0',
           'focus': '#6b8675',
           'success': '#426f53',
           'success_soft': '#e5f0e8',
           'warning': '#785d28',
           'warning_soft': '#fff3da',
           'danger': '#93474b',
           'danger_soft': '#f8e7e8',
           'hero': '#31443a',
           'hero_text': '#ffffff',
           'history': '#4a6155',
           'history_text': '#ffffff',
           'cover1': '#dce6dd',
           'cover2': '#c8d7cb',
           'cover3': '#d3dfd5'},
 'Lavendel': {'bg': '#f5f3f8',
              'panel': '#fdfcff',
              'panel2': '#ebe7f1',
              'editor': '#fffefe',
              'text': '#2c2933',
              'muted': '#6b6477',
              'disabled': '#9e97a8',
              'border': '#ddd7e5',
              'border_subtle': '#ebe7f0',
              'accent': '#75688f',
              'accent_hover': '#64577f',
              'accent_soft': '#ebe5f3',
              'accent_text': '#ffffff',
              'select': '#ebe5f3',
              'hover': '#f4f0f8',
              'focus': '#8c7da7',
              'success': '#4a7358',
              'success_soft': '#e7f0e9',
              'warning': '#795c27',
              'warning_soft': '#fff3da',
              'danger': '#94454d',
              'danger_soft': '#f8e7ea',
              'hero': '#3c354b',
              'hero_text': '#ffffff',
              'history': '#554c67',
              'history_text': '#ffffff',
              'cover1': '#e4dfea',
              'cover2': '#d3cbdd',
              'cover3': '#ddd7e5'},
 'Nord Licht': {'bg': '#eceff4',
                'panel': '#f7f9fb',
                'panel2': '#e5e9f0',
                'editor': '#ffffff',
                'text': '#2e3440',
                'muted': '#5a6578',
                'disabled': '#8e98a8',
                'border': '#d1d8e2',
                'border_subtle': '#e1e6ed',
                'accent': '#54769f',
                'accent_hover': '#48688f',
                'accent_soft': '#dce7f1',
                'accent_text': '#ffffff',
                'select': '#dce7f1',
                'hover': '#eef3f7',
                'focus': '#6587a8',
                'success': '#55704e',
                'success_soft': '#e4eee2',
                'warning': '#806520',
                'warning_soft': '#fff2cf',
                'danger': '#944c55',
                'danger_soft': '#f7e5e8',
                'hero': '#2e3440',
                'hero_text': '#eceff4',
                'history': '#3b4252',
                'history_text': '#eceff4',
                'cover1': '#d8dee9',
                'cover2': '#c9d1dd',
                'cover3': '#e5e9f0'},
 'Warm': {'bg': '#f4f1ea',
          'panel': '#fbf8f1',
          'panel2': '#ece5da',
          'editor': '#fffdf8',
          'text': '#2c2924',
          'muted': '#696258',
          'disabled': '#aaa397',
          'border': '#d9d0c2',
          'border_subtle': '#e8e1d6',
          'accent': '#7c6954',
          'accent_hover': '#685642',
          'accent_soft': '#eee3d6',
          'accent_text': '#fffaf2',
          'select': '#eee3d6',
          'hover': '#f7f1e8',
          'focus': '#927a61',
          'success': '#60735a',
          'success_soft': '#edf2e9',
          'warning': '#8b6b37',
          'warning_soft': '#fff4dc',
          'danger': '#95524b',
          'danger_soft': '#f7e9e6',
          'hero': '#3c342d',
          'hero_text': '#fffaf2',
          'history': '#594f45',
          'history_text': '#fffaf2',
          'cover1': '#e3ddd2',
          'cover2': '#d3c9ba',
          'cover3': '#ddd4c7'},
 'Papier': {'bg': '#ece9df',
            'panel': '#f7f4ea',
            'panel2': '#e5dfd2',
            'editor': '#fdfaf0',
            'text': '#26231f',
            'muted': '#655f56',
            'disabled': '#aaa397',
            'border': '#d2cbbc',
            'border_subtle': '#e3ddd1',
            'accent': '#68725f',
            'accent_hover': '#555f4d',
            'accent_soft': '#e3e8dc',
            'accent_text': '#ffffff',
            'select': '#e3e8dc',
            'hover': '#f1eee5',
            'focus': '#74806a',
            'success': '#596b54',
            'success_soft': '#eaf0e5',
            'warning': '#786134',
            'warning_soft': '#f7efd9',
            'danger': '#92594f',
            'danger_soft': '#f3e6e2',
            'hero': '#394137',
            'hero_text': '#fbfaf4',
            'history': '#4f574b',
            'history_text': '#fbfaf4',
            'cover1': '#ded9cd',
            'cover2': '#cbc4b5',
            'cover3': '#d6d0c2'},
 'Nacht': {'bg': '#17191c',
           'panel': '#202328',
           'panel2': '#292d33',
           'editor': '#1d2024',
           'text': '#e6e8eb',
           'muted': '#9ca3ad',
           'disabled': '#676e77',
           'border': '#353a42',
           'border_subtle': '#2a2e34',
           'accent': '#7ca6c2',
           'accent_hover': '#93bad2',
           'accent_soft': '#293943',
           'accent_text': '#17191c',
           'select': '#2d3942',
           'hover': '#272b31',
           'focus': '#8bb4cf',
           'success': '#79a58a',
           'success_soft': '#25362b',
           'warning': '#c8a765',
           'warning_soft': '#3b3324',
           'danger': '#dd8989',
           'danger_soft': '#40292b',
           'hero': '#11181e',
           'hero_text': '#f4f7f9',
           'history': '#263848',
           'history_text': '#f4f7f9',
           'cover1': '#2b3035',
           'cover2': '#32383e',
           'cover3': '#252a2f'},
 'Grafiet': {'bg': '#1d1f21',
             'panel': '#26292c',
             'panel2': '#303438',
             'editor': '#232629',
             'text': '#e7e7e7',
             'muted': '#a0a4a8',
             'disabled': '#6f7478',
             'border': '#3c4146',
             'border_subtle': '#303438',
             'accent': '#9ba8b2',
             'accent_hover': '#b0bbc3',
             'accent_soft': '#353b40',
             'accent_text': '#1d1f21',
             'select': '#363a3e',
             'hover': '#2e3235',
             'focus': '#aab5bd',
             'success': '#91ae99',
             'success_soft': '#2e3931',
             'warning': '#c1a16d',
             'warning_soft': '#3c3427',
             'danger': '#dc8a84',
             'danger_soft': '#422d2b',
             'hero': '#181a1c',
             'hero_text': '#f2f2f2',
             'history': '#343a3f',
             'history_text': '#f5f5f5',
             'cover1': '#303438',
             'cover2': '#3a3f44',
             'cover3': '#2b2f33'},
 'Middernacht': {'bg': '#111722',
                 'panel': '#17202d',
                 'panel2': '#202b3a',
                 'editor': '#141c27',
                 'text': '#e4e9f0',
                 'muted': '#97a4b4',
                 'disabled': '#607087',
                 'border': '#2c394a',
                 'border_subtle': '#202b39',
                 'accent': '#7fa2c9',
                 'accent_hover': '#96b5d7',
                 'accent_soft': '#21324a',
                 'accent_text': '#111722',
                 'select': '#233247',
                 'hover': '#1c2735',
                 'focus': '#90afd1',
                 'success': '#78a18b',
                 'success_soft': '#21352d',
                 'warning': '#c3a367',
                 'warning_soft': '#393122',
                 'danger': '#db858b',
                 'danger_soft': '#3e292e',
                 'hero': '#0c121b',
                 'hero_text': '#f2f6fb',
                 'history': '#24354b',
                 'history_text': '#f2f6fb',
                 'cover1': '#1f2a37',
                 'cover2': '#283649',
                 'cover3': '#1a2532'},
 'Inkt': {'bg': '#0b0d10',
          'panel': '#11151a',
          'panel2': '#171c22',
          'editor': '#0f1317',
          'text': '#edf1f5',
          'muted': '#a7b0ba',
          'disabled': '#66717b',
          'border': '#28313a',
          'border_subtle': '#1c242c',
          'accent': '#6f9bb8',
          'accent_hover': '#82abc5',
          'accent_soft': '#1d313f',
          'accent_text': '#0b0d10',
          'select': '#203341',
          'hover': '#171e25',
          'focus': '#85adc7',
          'success': '#7eaa8b',
          'success_soft': '#1d3024',
          'warning': '#d1ad67',
          'warning_soft': '#342b1c',
          'danger': '#d17a7f',
          'danger_soft': '#352126',
          'hero': '#07090b',
          'hero_text': '#f6f8fa',
          'history': '#182630',
          'history_text': '#f6f8fa',
          'cover1': '#171d23',
          'cover2': '#202831',
          'cover3': '#12181e'},
 'Diepblauw': {'bg': '#08111e',
               'panel': '#0d1928',
               'panel2': '#132238',
               'editor': '#0b1624',
               'text': '#e8eff7',
               'muted': '#9cadc1',
               'disabled': '#60738b',
               'border': '#263b54',
               'border_subtle': '#182b41',
               'accent': '#68a0d1',
               'accent_hover': '#7bb0dc',
               'accent_soft': '#193753',
               'accent_text': '#08111e',
               'select': '#1b3a58',
               'hover': '#13253a',
               'focus': '#80b4df',
               'success': '#7fa98f',
               'success_soft': '#173329',
               'warning': '#d0aa65',
               'warning_soft': '#352c1c',
               'danger': '#d27980',
               'danger_soft': '#382129',
               'hero': '#050c16',
               'hero_text': '#f1f6fb',
               'history': '#132b45',
               'history_text': '#f1f6fb',
               'cover1': '#12243a',
               'cover2': '#19304c',
               'cover3': '#0e1d30'},
 'Aurora': {'bg': '#242933',
            'panel': '#2e3440',
            'panel2': '#3b4252',
            'editor': '#282e38',
            'text': '#eceff4',
            'muted': '#b7c0cf',
            'disabled': '#778396',
            'border': '#4c566a',
            'border_subtle': '#3a4250',
            'accent': '#88c0d0',
            'accent_hover': '#8fbcbb',
            'accent_soft': '#3b5360',
            'accent_text': '#242933',
            'select': '#46566b',
            'hover': '#38404d',
            'focus': '#81a1c1',
            'success': '#a3be8c',
            'success_soft': '#344437',
            'warning': '#ebcb8b',
            'warning_soft': '#4a402d',
            'danger': '#d87881',
            'danger_soft': '#38262b',
            'hero': '#20242d',
            'hero_text': '#eceff4',
            'history': '#40394b',
            'history_text': '#eceff4',
            'cover1': '#3b4252',
            'cover2': '#465066',
            'cover3': '#343b49'}}

def stylesheet(name: str) -> str:
    t = THEMES.get(name, THEMES['Helder'])
    icon_dir = (Path(__file__).resolve().parent / 'icons').as_posix()
    spin_up = f'{icon_dir}/spin-up.svg'
    spin_down = f'{icon_dir}/spin-down.svg'
    return f'''
    QWidget {{ background: {t['bg']}; color: {t['text']}; }}
    QMainWindow, QDialog {{ background: {t['bg']}; }}
    QLabel {{ background: transparent; }}
    QToolTip {{ background: {t['panel']}; color: {t['text']}; border: 1px solid {t['border']}; padding: 6px 8px; }}

    QFrame#panel, QWidget#panel {{ background: {t['panel']}; border: 0; }}
    QFrame#toolrail {{ background: {t['panel2']}; border: 0; }}
    QScrollArea#navScroll, QWidget#navScrollContent, QWidget#navProgramHost {{ background: transparent; border: 0; }}
    QScrollArea#navScroll > QWidget > QWidget {{ background: transparent; }}
    QScrollArea#navScroll QScrollBar:vertical {{ width: 5px; margin: 0; }}
    QFrame#editorTopbar {{ background: {t['panel']}; border-bottom: 1px solid {t['border_subtle']}; }}
    QFrame#historyBanner {{ background: {t['history']}; border: 0; }}
    QLabel#historyBannerLabel {{ color: {t['history_text']}; background: transparent; font-weight: 600; }}
    QPushButton#restoreButton {{ background: {t['accent']}; color: {t['accent_text']}; border: 1px solid transparent; font-weight: 600; }}
    QPushButton#restoreButton:hover {{ background: {t['accent_hover']}; }}
    QPushButton#restoreButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#restoreButton:pressed {{ background: {t['accent']}; border-color: {t['focus']}; }}
    QPushButton#historyExitButton {{ background: {t['panel']}; color: {t['text']}; border: 1px solid {t['border']}; font-weight: 600; }}
    QPushButton#historyExitButton:hover {{ background: {t['hover']}; }}
    QPushButton#historyExitButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#historyExitButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
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
    QWidget#centeredMaxWidthHost, QWidget#bookshelfHeroInner {{ background: transparent; }}
    QFrame#bookCard, QFrame#newBookCard {{ background: {t['panel']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; }}
    QFrame#bookCard:hover, QFrame#newBookCard:hover {{ border: 1px solid {t['border']}; }}
    QLabel#bookCoverTitle {{ font-family: "Merriweather", Georgia, serif; font-size: 22px; background: transparent; }}
    QLabel#newBookPlus {{ font-size: 42px; color: {t['accent']}; background: transparent; }}

    QPushButton {{ background: transparent; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 8px 12px; }}
    QPushButton:hover {{ background: {t['hover']}; border-color: {t['focus']}; }}
    QPushButton:focus {{ border-color: {t['focus']}; }}
    QPushButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton:disabled {{ color: {t['disabled']}; border-color: {t['border_subtle']}; background: transparent; }}
    QPushButton#primaryButton {{ background: {t['accent']}; color: {t['accent_text']}; border: 1px solid {t['accent']}; font-weight: 600; }}
    QPushButton#primaryButton:hover {{ background: {t['accent_hover']}; border-color: {t['accent_hover']}; }}
    QPushButton#primaryButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#primaryButton:pressed {{ background: {t['accent']}; border-color: {t['focus']}; }}
    QPushButton#primaryButton:disabled {{ background: {t['panel2']}; color: {t['disabled']}; border-color: {t['border_subtle']}; }}
    QPushButton#secondaryButton {{ background: {t['panel']}; }}
    QPushButton#secondaryButton:hover {{ background: {t['hover']}; border-color: {t['focus']}; }}
    QPushButton#secondaryButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#secondaryButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton#exportFormatCard {{ background: {t['panel']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; padding: 12px 14px; text-align: left; font-weight: 600; }}
    QPushButton#exportFormatCard:hover {{ background: {t['hover']}; border-color: {t['focus']}; }}
    QPushButton#exportFormatCard:focus {{ border-color: {t['focus']}; }}
    QPushButton#exportFormatCard:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton#exportFormatCard:checked {{ background: {t['accent_soft']}; border-color: {t['accent']}; color: {t['text']}; }}
    QPushButton#exportFormatCard:disabled {{ background: {t['panel2']}; color: {t['disabled']}; border-color: {t['border_subtle']}; }}
    QPushButton#dangerButton {{ color: {t['danger']}; border-color: {t['danger']}; }}
    QPushButton#dangerButton:hover, QPushButton#dangerButton:focus {{ background: {t['danger_soft']}; color: {t['danger']}; border-color: {t['focus']}; }}
    QPushButton#dangerButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton#railButton {{ border: 1px solid transparent; border-left: 3px solid transparent; border-radius: 8px; padding: 8px 10px; text-align: left; }}
    QPushButton#railButton:hover {{ background: {t['hover']}; }}
    QPushButton#railButton:focus {{ border-color: {t['focus']}; border-left-color: {t['focus']}; }}
    QPushButton#railButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton#railButton:checked {{ background: {t['accent_soft']}; border-left: 3px solid {t['accent']}; color: {t['accent']}; }}
    QPushButton#railButton:checked:focus {{ border-color: {t['focus']}; border-left-color: {t['accent']}; }}
    QLabel#navGroupLabel {{ color: {t['muted']}; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; background: transparent; }}
    QFrame#navGroupSeparator {{ background: {t['border_subtle']}; border: 0; min-height: 1px; max-height: 1px; margin: 3px 9px; }}
    QPushButton#navButton {{ border: 1px solid transparent; border-left: 3px solid transparent; border-radius: 8px; padding: 8px 10px; text-align: left; font-weight: 600; }}
    QPushButton#navButton:hover {{ background: {t['hover']}; }}
    QPushButton#navButton:focus {{ border-color: {t['focus']}; border-left-color: {t['focus']}; }}
    QPushButton#navButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton#navButton:checked {{ background: {t['accent_soft']}; border-left: 3px solid {t['accent']}; color: {t['accent']}; }}
    QPushButton#navButton:checked:focus {{ border-color: {t['focus']}; border-left-color: {t['accent']}; }}
    QPushButton#compactButton {{ border: 1px solid transparent; padding: 5px; min-width: 28px; }}
    QPushButton#compactButton:hover {{ background: {t['hover']}; border-color: {t['border']}; }}
    QPushButton#compactButton:focus {{ border-color: {t['focus']}; background: {t['hover']}; }}
    QPushButton#compactButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton#thinkingButton {{ border: 1px solid transparent; color: {t['muted']}; text-align: left; padding: 4px 0; }}
    QPushButton#thinkingButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#suggestionButton {{ border: 1px solid transparent; border-radius: 8px; padding: 5px 8px; text-align: left; min-height: 26px; max-height: 32px; }}
    QPushButton#suggestionButton:hover {{ background: {t['hover']}; }}
    QPushButton#suggestionButton:checked {{ background: {t['accent_soft']}; }}
    QPushButton#suggestionButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#suggestionButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QPushButton#aiActionButton {{ background: {t['accent']}; color: {t['accent_text']}; border: 1px solid transparent; border-radius: 18px; padding: 0; }}
    QPushButton#aiActionButton:hover {{ background: {t['accent_hover']}; }}
    QPushButton#aiActionButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#aiActionButton:pressed {{ background: {t['accent']}; border-color: {t['focus']}; }}

    QPushButton#contentsEdgeButton {{ background: {t['panel2']}; color: {t['text']}; border: 1px solid {t['border_subtle']}; border-left: 0; border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 9px; border-bottom-right-radius: 9px; padding: 4px; }}
    QPushButton#contentsEdgeButton:hover, QPushButton#contentsEdgeButton:focus {{ background: {t['hover']}; border-color: {t['focus']}; }}
    QPushButton#contentsEdgeButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QFrame#flyout {{ background: {t['panel']}; border: 1px solid {t['border']}; border-radius: 4px; }}
    QFrame#insertChoiceCard {{ background: {t['panel']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; }}
    QPushButton#flyoutButton {{ background: transparent; border: 1px solid transparent; border-radius: 4px; padding: 10px 14px; text-align: left; font-weight: 600; min-width: 190px; }}
    QPushButton#flyoutButton:hover {{ background: {t['accent_soft']}; color: {t['text']}; }}
    QPushButton#flyoutButton:focus {{ background: {t['accent_soft']}; color: {t['text']}; border-color: {t['focus']}; }}
    QPushButton#flyoutButton:pressed {{ background: {t['select']}; color: {t['text']}; }}
    QFrame#selectionToolbar {{ background: {t['panel2']}; border: 1px solid {t['border']}; border-radius: 10px; }}
    QPushButton#formatButton {{ background: transparent; color: {t['text']}; border: 1px solid transparent; border-radius: 7px; padding: 0; min-width: 44px; min-height: 42px; font-weight: 600; }}
    QPushButton#formatButton:hover {{ background: {t['accent_soft']}; color: {t['text']}; }}
    QPushButton#formatButton:checked {{ background: {t['select']}; color: {t['accent']}; }}
    QPushButton#formatButton:checked:hover {{ background: {t['accent_soft']}; color: {t['accent']}; }}
    QPushButton#formatButton:focus {{ border-color: {t['focus']}; }}
    QPushButton#formatButton:pressed {{ background: {t['select']}; border-color: {t['focus']}; }}
    QToolButton#sceneBreakDelete {{ background: {t['panel2']}; color: {t['muted']}; border: 1px solid {t['border_subtle']}; border-radius: 13px; padding: 0; }}
    QToolButton#sceneBreakDelete:hover {{ background: {t['accent_soft']}; color: {t['danger']}; border-color: {t['border']}; }}
    QToolButton#sceneBreakDelete:pressed {{ background: {t['select']}; }}

    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {{
        background: {t['editor']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 9px; padding: 8px 10px; selection-background-color: {t['accent']};
    }}
    QSpinBox {{
        background: {t['editor']}; color: {t['text']}; border: 1px solid {t['border']};
        border-radius: 9px; padding: 8px 34px 8px 10px; selection-background-color: {t['accent']};
    }}
    QSpinBox::up-button {{
        subcontrol-origin: border; subcontrol-position: top right; width: 28px;
        border-left: 1px solid {t['border_subtle']}; border-bottom: 1px solid {t['border_subtle']};
        border-top-right-radius: 8px; background: {t['panel2']};
    }}
    QSpinBox::down-button {{
        subcontrol-origin: border; subcontrol-position: bottom right; width: 28px;
        border-left: 1px solid {t['border_subtle']};
        border-bottom-right-radius: 8px; background: {t['panel2']};
    }}
    QSpinBox::up-arrow {{ image: url("{spin_up}"); width: 12px; height: 12px; }}
    QSpinBox::down-arrow {{ image: url("{spin_down}"); width: 12px; height: 12px; }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {t['accent_soft']}; }}
    QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{ background: {t['select']}; }}
    QComboBox {{ padding-right: 34px; }}
    QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 30px; border: 0; background: transparent; }}
    QComboBox QAbstractItemView {{ background: {t['panel']}; color: {t['text']}; border: 1px solid {t['border']}; outline: 0; selection-background-color: {t['accent_soft']}; selection-color: {t['text']}; padding: 4px; }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {t['focus']}; }}
    QCheckBox:focus, QRadioButton:focus {{ background: {t['accent_soft']}; border-radius: 6px; }}
    QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {{ color: {t['disabled']}; background: {t['panel2']}; }}
    QLineEdit#chapterTitle {{ border: 0; border-bottom: 1px solid transparent; padding: 34px 44px 16px 44px; background: {t['editor']}; }}
    QLineEdit#chapterTitle:focus {{ border: 0; border-bottom: 1px solid {t['accent']}; }}
    QTextEdit#editor {{ border: 0; padding: 30px 18px; line-height: 1.6; }}
    QTextEdit#thinkingDetails {{ background: {t['panel2']}; color: {t['muted']}; font-size: 12px; }}
    QTextBrowser#aiChat {{ background: transparent; border: 0; padding: 2px; }}
    QTextEdit#aiInput {{ border-radius: 14px; padding: 10px 12px; background: {t['editor']}; }}

    QListWidget, QTreeWidget {{ background: {t['panel']}; color: {t['text']}; border: 1px solid transparent; border-radius: 8px; outline: 0; }}
    QListWidget:focus, QTreeWidget:focus {{ border-color: {t['focus']}; }}
    QListWidget::item, QTreeWidget::item {{ padding: 8px 8px; border-radius: 6px; }}
    QListWidget::item:hover, QTreeWidget::item:hover {{ background: {t['hover']}; }}
    QListWidget::item:selected, QTreeWidget::item:selected {{ background: {t['accent_soft']}; color: {t['text']}; }}
    QListWidget::item:disabled, QTreeWidget::item:disabled {{ color: {t['muted']}; background: transparent; }}
    QTreeWidget#manuscriptTree::item {{ border-radius: 0px; }}


    QFrame#planningSidebar {{ background: {t['panel2']}; border-right: 1px solid {t['border_subtle']}; }}
    QPushButton#planningNavButton {{ border: 1px solid transparent; border-left: 3px solid transparent; border-radius: 8px; padding: 10px 12px; text-align: left; color: {t['muted']}; }}
    QPushButton#planningNavButton:hover {{ background: {t['hover']}; color: {t['text']}; }}
    QPushButton#planningNavButton:focus {{ border-color: {t['focus']}; border-left-color: {t['focus']}; color: {t['text']}; }}
    QPushButton#planningNavButton:pressed {{ background: {t['select']}; color: {t['text']}; }}
    QPushButton#planningNavButton:checked {{ background: {t['accent_soft']}; color: {t['text']}; border-left: 3px solid {t['accent']}; font-weight: 600; }}
    QPushButton#planningNavButton:checked:focus {{ border-color: {t['focus']}; border-left-color: {t['accent']}; }}
    QFrame#planningListPanel {{ background: {t['panel']}; border-right: 1px solid {t['border_subtle']}; }}
    QLabel#planningMicroLabel {{ color: {t['muted']}; font-size: 11px; font-weight: 600; letter-spacing: 0.8px; }}
    QFrame#sceneCard {{ background: {t['panel']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; }}
    QLabel#outlineChapterTitle {{ background: {t['panel2']}; border-radius: 8px; padding: 8px 10px; font-weight: 600; }}
    QPushButton#relationChip {{ background: {t['accent_soft']}; color: {t['text']}; border: 1px solid transparent; border-radius: 12px; padding: 5px 10px; text-align: left; }}
    QPushButton#relationChip:hover {{ color: {t['accent']}; }}
    QPushButton#relationChip:focus {{ border-color: {t['focus']}; color: {t['accent']}; }}
    QPushButton#relationChip:pressed {{ background: {t['select']}; }}
    QTextEdit#planningNotesEditor {{ border: 0; }}

    QLabel#microLabel {{ color: {t['muted']}; font-size: 11px; font-weight: 600; letter-spacing: 0.8px; }}
    QFrame#softPanel {{ background: {t['panel2']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; }}
    QCheckBox#publicationToggle {{ spacing: 9px; padding: 8px 6px; font-size: 14px; border-radius: 7px; }}
    QCheckBox#publicationToggle:hover {{ background: {t['hover']}; }}
    QCheckBox#publicationToggle:focus {{ background: {t['accent_soft']}; }}
    QRadioButton#publicationRadio {{ spacing: 10px; padding: 7px 8px; font-size: 14px; border-radius: 7px; }}
    QRadioButton#publicationRadio:hover {{ background: {t['hover']}; }}
    QRadioButton#publicationRadio:focus {{ background: {t['accent_soft']}; }}
    QRadioButton#publicationRadio::indicator {{ width: 18px; height: 18px; border: 2px solid {t['border']}; border-radius: 9px; background: {t['editor']}; }}
    QRadioButton#publicationRadio::indicator:hover {{ border-color: {t['accent']}; }}
    QRadioButton#publicationRadio::indicator:checked {{ background: {t['accent']}; border: 4px solid {t['editor']}; }}
    QLabel#contentsPreview {{ color: {t['text']}; padding: 2px 0; }}

    QFrame#settingsSidebar {{ background: transparent; border-right: 1px solid {t['border_subtle']}; padding-right: 16px; }}
    QPushButton#settingsNavButton {{ border: 1px solid transparent; border-left: 3px solid transparent; border-radius: 8px; padding: 10px 12px; text-align: left; color: {t['muted']}; }}
    QPushButton#settingsNavButton:hover {{ background: {t['hover']}; color: {t['text']}; }}
    QPushButton#settingsNavButton:focus {{ border-color: {t['focus']}; border-left-color: {t['focus']}; color: {t['text']}; }}
    QPushButton#settingsNavButton:checked {{ background: {t['accent_soft']}; color: {t['text']}; border-left: 3px solid {t['accent']}; font-weight: 600; }}
    QPushButton#settingsNavButton:checked:focus {{ border-color: {t['focus']}; border-left-color: {t['accent']}; }}
    QLabel#settingsPageTitle {{ font-size: 20px; font-weight: 600; }}
    QLabel#settingsPageIntro {{ color: {t['muted']}; padding-top: 4px; }}
    QLabel#settingsSectionTitle {{ color: {t['muted']}; font-size: 11px; font-weight: 700; letter-spacing: 0.8px; }}
    QFrame#settingsRow {{ background: transparent; border-bottom: 1px solid {t['border_subtle']}; }}
    QLabel#settingsFieldLabel {{ font-size: 13px; font-weight: 600; color: {t['text']}; }}
    QLabel#settingsFieldHelp {{ font-size: 12px; color: {t['muted']}; }}
    QWidget#settingsRowInfo, QWidget#settingsRowControl, QWidget#settingsInlineControl, QWidget#settingsFullWidth, QWidget#settingsContent {{ background: transparent; }}
    QStackedWidget#settingsPages {{ background: transparent; }}
    QLabel#settingsToast {{ background: {t['text']}; color: {t['bg']}; border: 1px solid {t['border']}; border-radius: 9px; padding: 9px 14px; font-weight: 600; }}
    QFrame#fontPreviewCard {{ background: {t['editor']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; }}
    QLabel#fontPreviewSample {{ background: transparent; color: {t['text']}; border: 0; font-size: 15px; }}
    QLabel#fontPreviewMeta {{ background: transparent; color: {t['muted']}; border: 0; font-size: 11px; }}
    QScrollArea#settingsContentScroll {{ background: transparent; border: 0; }}
    QScrollArea#settingsContentScroll > QWidget > QWidget {{ background: transparent; }}
    QScrollArea#aboutScroll {{ background: transparent; border: 0; }}
    QScrollArea#aboutScroll > QWidget > QWidget {{ background: transparent; }}
    QFrame#aboutHero {{ background: {t['hero']}; border: 0; border-radius: 12px; }}
    QLabel#aboutHeroTitle {{ color: {t['hero_text']}; font-size: 28px; font-weight: 700; }}
    QLabel#aboutHeroTagline {{ color: {t['hero_text']}; font-size: 14px; }}
    QLabel#aboutVersionChip {{ background: {t['panel']}; color: {t['text']}; border: 1px solid {t['border_subtle']}; border-radius: 9px; padding: 5px 9px; font-size: 11px; font-weight: 600; }}
    QLabel#aboutRuntime {{ color: {t['muted']}; font-size: 11px; }}
    QFrame#licenseCard {{ background: {t['panel']}; border: 1px solid {t['border_subtle']}; border-radius: 10px; }}
    QLabel#licenseTitle {{ font-size: 13px; font-weight: 600; color: {t['text']}; }}
    QLabel#aboutVersion {{ color: {t['accent']}; font-weight: 600; }}
    QPlainTextEdit#licenseText {{ background: {t['editor']}; color: {t['text']}; border: 1px solid {t['border_subtle']}; border-radius: 8px; padding: 9px; font-family: 'Consolas'; font-size: 11px; }}

    QDialog#startupSplash {{ background: {t['bg']}; border: 1px solid {t['border']}; }}
    QFrame#splashCard {{ background: {t['panel']}; border: 0; }}
    QLabel#splashTitle {{ color: {t['text']}; font-size: 34px; font-weight: 700; }}
    QLabel#splashTagline {{ color: {t['muted']}; font-size: 15px; }}
    QLabel#splashStatus {{ color: {t['text']}; font-size: 12px; font-weight: 600; }}
    QLabel#splashFooter {{ color: {t['muted']}; font-size: 10px; }}
    QProgressBar#splashProgress {{ background: {t['panel2']}; border: 0; border-radius: 2px; }}
    QProgressBar#splashProgress::chunk {{ background: {t['accent']}; border-radius: 2px; }}
    QTabWidget::pane {{ border: 1px solid {t['border_subtle']}; border-radius: 8px; background: {t['panel']}; }}
    QTabBar::tab {{ background: transparent; padding: 9px 14px; color: {t['muted']}; border-bottom: 2px solid transparent; }}
    QTabBar::tab:selected {{ color: {t['text']}; border-bottom: 2px solid {t['accent']}; }}
    QTabBar::tab:hover {{ color: {t['text']}; }}
    QTabBar:focus {{ border-bottom: 1px solid {t['focus']}; }}

    QSplitter::handle:horizontal {{ width: 7px; background: transparent; border-left: 1px solid {t['border_subtle']}; }}
    QSplitter::handle:horizontal:hover {{ border-left: 2px solid {t['accent']}; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {t['muted']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QStatusBar {{ background: {t['bg']}; color: {t['muted']}; border-top: 1px solid {t['border_subtle']}; }}
    QMenu {{ background: {t['panel']}; border: 1px solid {t['border']}; padding: 6px; }}
    QMenu::item {{ padding: 7px 24px 7px 10px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {t['accent_soft']}; }}
    QMenu::item:disabled {{ color: {t['disabled']}; }}
    '''
