from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


FRONT_MATTER = (
    ('title_page', 'Titelpagina', 'structured'),
    ('copyright', 'Copyright', 'structured'),
    ('dedication', 'Opdracht', 'text'),
    ('epigraph', 'Epigraaf', 'structured'),
    ('contents', 'Inhoudsopgave', 'generated'),
    ('foreword', 'Voorwoord', 'text'),
    ('preface', 'Inleiding', 'text'),
)

BACK_MATTER = (
    ('afterword', 'Nawoord', 'text'),
    ('acknowledgements', 'Dankwoord', 'text'),
    ('about_author', 'Over de auteur', 'text'),
)

PUBLICATION_ITEMS = {key: {'key': key, 'label': label, 'kind': kind, 'zone': 'front'} for key, label, kind in FRONT_MATTER}
PUBLICATION_ITEMS.update({key: {'key': key, 'label': label, 'kind': kind, 'zone': 'back'} for key, label, kind in BACK_MATTER})


def item_definition(key: str) -> dict | None:
    return PUBLICATION_ITEMS.get(key)


@dataclass
class PublicationData:
    enabled: list[str] = field(default_factory=list)
    title_page: dict = field(default_factory=dict)
    copyright: dict = field(default_factory=dict)
    epigraph: dict = field(default_factory=dict)
    contents: dict = field(default_factory=lambda: {'depth': 'chapters'})

    @classmethod
    def from_dict(cls, data: dict | None) -> 'PublicationData':
        data = data if isinstance(data, dict) else {}
        enabled = [key for key in data.get('enabled', []) if key in PUBLICATION_ITEMS]
        return cls(
            enabled=enabled,
            title_page=dict(data.get('title_page') or {}),
            copyright=dict(data.get('copyright') or {}),
            epigraph=dict(data.get('epigraph') or {}),
            contents=dict(data.get('contents') or {'depth': 'chapters'}),
        )

    def to_dict(self) -> dict:
        return {
            'version': 1,
            'enabled': list(self.enabled),
            'title_page': dict(self.title_page),
            'copyright': dict(self.copyright),
            'epigraph': dict(self.epigraph),
            'contents': dict(self.contents),
        }

    @staticmethod
    def defaults_for_book(book) -> 'PublicationData':
        author = str((book.metadata or {}).get('author') or '')
        return PublicationData(
            enabled=[],
            title_page={
                'title': book.title,
                'subtitle': '',
                'author': author,
                'publisher': '',
            },
            copyright={
                'author': author,
                'edition': 'Eerste editie',
                'year': str(datetime.now().year),
                'publisher': '',
                'isbn_epub': '',
                'isbn_kindle': '',
                'isbn_paperback': '',
                'isbn_hardcover': '',
                'isbn_pdf': '',
                'clauses': {
                    'rights_reserved': {
                        'enabled': True,
                        'text': 'Alle rechten voorbehouden. Niets uit deze uitgave mag zonder voorafgaande schriftelijke toestemming van de rechthebbende worden verveelvoudigd, opgeslagen of openbaar gemaakt.',
                    },
                    'fiction': {
                        'enabled': False,
                        'text': 'Dit is een werk van fictie. Namen, personages, plaatsen en gebeurtenissen zijn voortgekomen uit de verbeelding van de auteur of fictief gebruikt. Iedere overeenkomst met werkelijke personen of gebeurtenissen berust op toeval.',
                    },
                    'moral_rights': {
                        'enabled': False,
                        'text': f'{author or "De auteur"} behoudt het recht om als auteur van dit werk te worden vermeld.',
                    },
                    'external_content': {
                        'enabled': False,
                        'text': 'De uitgever en auteur zijn niet verantwoordelijk voor de beschikbaarheid of juistheid van externe websites of andere bronnen waarnaar in deze publicatie wordt verwezen.',
                    },
                    'designations': {
                        'enabled': False,
                        'text': 'Productnamen, handelsnamen en merken die in dit werk worden genoemd kunnen eigendom zijn van hun respectieve rechthebbenden.',
                    },
                },
            },
            epigraph={'quote': '', 'source': ''},
            contents={'depth': 'chapters'},
        )
