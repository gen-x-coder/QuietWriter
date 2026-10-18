"""Woordenboeken installeren zonder handwerk (1.7).

Een vaste, in QuietWriter ingebouwde lijst Hunspell-woordenboeken uit de
LibreOffice-woordenboekbibliotheek op GitHub, vastgezet op één commit. Per
bestand staan grootte en SHA-256 in de code: wat binnenkomt, moet daar
precies mee kloppen, anders wordt er niets geïnstalleerd.

Veiligheid en rust:
- Alleen na een klik van de gebruiker; nooit stil op de achtergrond.
- Er gaat niets van je tekst mee: het is een gewone download.
- Eerst downloaden naar de tijdelijke map van het systeem (buiten een
  eventuele Dropbox-werkmap) en controleren. Pas als alles klopt, worden de
  bestanden één voor één atomair op hun plek gezet (tijdelijk bestand +
  ``os.replace``), met een reservekopie van elk vorig bestand. Mislukt dat
  halverwege, dan worden de vorige bestanden atomair teruggezet; lukt ook dat
  niet, dan blijven de reservekopieën staan en zegt de melding dat.
- Vaste bestandsnamen uit de lijst; nooit paden uit de download.
- Office-woordenboeken (ONLYOFFICE, LibreOffice, OpenOffice) worden nooit
  aangeraakt.
"""
from __future__ import annotations

import hashlib
import json
import time
import tempfile
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from .dictionary_catalog import locale_label

SOURCE_REPO = 'https://github.com/LibreOffice/dictionaries'
SOURCE_COMMIT = '67032ee957631908098a72edf48dc81cac27e369'
RAW_BASE = f'https://raw.githubusercontent.com/LibreOffice/dictionaries/{SOURCE_COMMIT}/'
MARKER = 'quietwriter-download.json'
CHUNK = 64 * 1024


class DownloadCancelled(Exception):
    pass


class DownloadFailed(Exception):
    pass


class RollbackIncomplete(DownloadFailed):
    """Installeren mislukte én het vorige woordenboek kon niet helemaal terug.

    ``backups`` zijn de reservekopieën die zijn blijven staan (niets wordt dan
    weggegooid); de melding zegt dat er wél iets veranderd is.
    """

    def __init__(self, message: str, backups: list[Path]):
        super().__init__(message)
        self.backups = list(backups)


@dataclass(frozen=True)
class RemoteFile:
    remote: str
    local: str
    sha256: str
    size: int


@dataclass(frozen=True)
class CatalogDictionary:
    locale: str
    author: str
    license: str
    files: tuple[RemoteFile, ...]

    @property
    def label(self) -> str:
        return locale_label(self.locale)

    @property
    def size(self) -> int:
        return sum(f.size for f in self.files)


CATALOG: tuple[CatalogDictionary, ...] = (
    CatalogDictionary('nl_NL', 'OpenTaal', 'BSD-3-Clause / CC BY 3.0', (
        RemoteFile('nl_NL/nl_NL.dic', 'nl_NL.dic', 'bc28af45307700a9927ad5719184da44dfd7eed4f707b8c1477f6d8a21b586a6', 2488246),
        RemoteFile('nl_NL/nl_NL.aff', 'nl_NL.aff', 'f0233d4f721f4661cf5f4d05ed2739549322bf3b6b66764b55a38257e1e16e6f', 46557),
        RemoteFile('nl_NL/LICENSE.txt', 'LICENSE-nl_NL.txt', '2189c248cbc054445aeac6cd65b87eebd0a115efeb55ed498b0f2a73441805dd', 25820),
    )),
    CatalogDictionary('en_GB', 'Marco A.G. Pinto', 'LGPL', (
        RemoteFile('en/en_GB.dic', 'en_GB.dic', '04e90f34f5263bf26780e9c4a442e9ad16584e227af49ddd1b3b21b01df5b29c', 1230571),
        RemoteFile('en/en_GB.aff', 'en_GB.aff', '0fd6ed120ef28957847d98ba5149b117e27116cf81b5aa36208453f6755a36fd', 44158),
        RemoteFile('en/README_en_GB.txt', 'LICENSE-en_GB.txt', '18b5833de60a52ffcb6e5b6b5048bb5a5d910acfecd5b096985b77058223880c', 10644),
    )),
    CatalogDictionary('en_US', 'SCOWL (Kevin Atkinson)', 'BSD-achtig (SCOWL)', (
        RemoteFile('en/en_US.dic', 'en_US.dic', 'f0b1a234bd178bdd01875b2a392a9647f888b8fe879f79c52aae62c2759b3647', 551762),
        RemoteFile('en/en_US.aff', 'en_US.aff', 'e746c882dd6f303c2c46e7452804b9201115a6942cfeb15f18f8edf774d2e24e', 3205),
        RemoteFile('en/README_en_US.txt', 'LICENSE-en_US.txt', '168b4c01cb841f766a72f310b065c04d09cff46376c37a81d799593ce751c371', 15732),
    )),
    CatalogDictionary('de_DE', 'Franz Michael Baumann (igerman98)', 'GPL 2 of 3', (
        RemoteFile('de/de_DE_frami.dic', 'de_DE.dic', '4ca3c958b0e5545910999bc246f668840bf8ede3df8e5e6790d05edd5a586c38', 4356903),
        RemoteFile('de/de_DE_frami.aff', 'de_DE.aff', '646bf3333ac69c23e9d794533ee5241d6f755c359e8fe10a648f87613743d594', 19067),
        RemoteFile('de/README_de_DE_frami.txt', 'LICENSE-de_DE.txt', 'c141f4f79c428b7348b5012836f4ad3db4d124f288f15effc22696dc876512ae', 752),
    )),
    CatalogDictionary('fr_FR', 'Grammalecte (Olivier R.)', 'MPL 2.0', (
        RemoteFile('fr_FR/dictionaries/fr.dic', 'fr_FR.dic', 'b78a868e31dd6e373b6c3217969afb898a9acde828a5e7ef97308da42218c88c', 1236490),
        RemoteFile('fr_FR/dictionaries/fr.aff', 'fr_FR.aff', 'c176610cd5dc4846806a65ddd029f422d87978bf58f224aa44222662a16a2de5', 199870),
        RemoteFile('fr_FR/package-description.txt', 'LICENSE-fr_FR.txt', '35da6b033d87660b81c6ca17633676beecda93c2ad917048ac133aaa58be4206', 434),
    )),
    CatalogDictionary('es_ES', 'RLA-ES', 'GPL 3 / LGPL 3 / MPL 1.1', (
        RemoteFile('es/es_ES.dic', 'es_ES.dic', '6975dddec3d5d2c676069537bc67b4b5f786c65c5d4cf6703a82acf779ac9ec1', 715989),
        RemoteFile('es/es_ES.aff', 'es_ES.aff', 'e73a9bf8e1383f4986a5dc9e2fbed49371c0c61f511c626d15586bd433c1cad9', 169202),
        RemoteFile('es/README_hunspell_es.txt', 'LICENSE-es_ES.txt', '0b5c39a863ecb61f5c5631ec1cd977667ef9bda6da6f90e80e9fc0edcbfadd97', 2615),
    )),
    CatalogDictionary('it_IT', 'LibreItalia', 'GPL 3', (
        RemoteFile('it_IT/it_IT.dic', 'it_IT.dic', 'bae1e3501dcd2a923669592493b3fde6c02aae7c7aab83bf5e5b49077e73dd64', 1295083),
        RemoteFile('it_IT/it_IT.aff', 'it_IT.aff', '951afaa19272f13555b8823e8bcf9ccf78f8fe1a07835bdfb912ab3e4d537c2b', 70054),
        RemoteFile('it_IT/README_it_IT.txt', 'LICENSE-it_IT.txt', '34c3e93595cf3cf5f3afc9bc0d98eea12593750383f1e82ed1d3ca29f9681283', 38902),
    )),
    CatalogDictionary('pt_PT', 'Natura (Projecto Natura)', 'GPL 2 / LGPL 2.1 / MPL 1.1', (
        RemoteFile('pt_PT/pt_PT.dic', 'pt_PT.dic', 'e29ba2d7aa8a2ad43e9cb46ac6473064b661545c87002aea90e18899d98d3cc9', 1485977),
        RemoteFile('pt_PT/pt_PT.aff', 'pt_PT.aff', '975a209fcc892cb382fa5f34a28c391a39668661ce373ae071287809c5fcae24', 95089),
        RemoteFile('pt_PT/README_pt_PT.txt', 'LICENSE-pt_PT.txt', '36de7d88a406a4947bf646a64145f00827566808988632e3df969aa95776060c', 1106),
    )),
    CatalogDictionary('pt_BR', 'VERO (Raimundo Moura)', 'LGPL 3 / MPL', (
        RemoteFile('pt_BR/pt_BR.dic', 'pt_BR.dic', 'a38bfb26b68ece2834e79fe83e48d5792652970ace12db89d1b9674bf9933183', 4477695),
        RemoteFile('pt_BR/pt_BR.aff', 'pt_BR.aff', '21d8ad2a769a60e17e2b5ea4ef11d4d593a58b9e2a82d642ef82d6a4c5523865', 979792),
        RemoteFile('pt_BR/README_pt_BR.txt', 'LICENSE-pt_BR.txt', '9974ce691fdc1fe731717d7a2dc668244405fdc2bf9bf3367eb9b29e85177c88', 16348),
    )),
    CatalogDictionary('da_DK', 'Stavekontrolden', 'GPL 2 / LGPL 2.1 / MPL 1.1', (
        RemoteFile('da_DK/da_DK.dic', 'da_DK.dic', '298aabeca362ee2c71836c5c7748d22080a460bd7193e6fbd2471f27a70d0fd3', 3894244),
        RemoteFile('da_DK/da_DK.aff', 'da_DK.aff', 'ee4fe193d19b72aa64bc0d2b9bcdf44ee44f11d9b4e7dcf6da36fd0e91528561', 82864),
        RemoteFile('da_DK/README_da_DK.txt', 'LICENSE-da_DK.txt', '9508f4ec9e14a3d2a3360dd694881440d0d73fe1fe076e547639e5fe33c7b42d', 787),
    )),
    CatalogDictionary('sv_SE', 'Göran Andersson', 'LGPL 3', (
        RemoteFile('sv_SE/dictionaries/sv_SE.dic', 'sv_SE.dic', '384a2126eff333f5f6f9790ae892554546f53948d2988c600397cb5ad6ce66e8', 2344202),
        RemoteFile('sv_SE/dictionaries/sv_SE.aff', 'sv_SE.aff', 'b721c9d44bee912feb182b601a1bc2ae3e7dffef660f4130cf2751867488a9dd', 18583),
        RemoteFile('sv_SE/LICENSE_en_US.txt', 'LICENSE-sv_SE.txt', '1314b6004bff32053ca25aca5fc419e905d75a6d49f9f9825baf4f02298af6d9', 378),
    )),
    CatalogDictionary('pl_PL', 'sjp.pl', 'GPL / LGPL / MPL / Apache 2.0 / CC SA', (
        RemoteFile('pl_PL/pl_PL.dic', 'pl_PL.dic', 'c0848440599eb88e5aca500418d5f389e562ec2c157b63dbe39d354658ffba49', 5252096),
        RemoteFile('pl_PL/pl_PL.aff', 'pl_PL.aff', '82973651651aa930335c865b339b98db376ca3dbf3a661b70b9eeb71fdf41dca', 257542),
        RemoteFile('pl_PL/README_en.txt', 'LICENSE-pl_PL.txt', 'fb5f9b4a0643821cf88775c0932810c1cd05f236136c913e3eaf1e24806f3f44', 2282),
    )),
    # 1.7.0-dev14: 23 talen erbij, elk getest met spylls (laden < 5 s, < 400 MB).
    # Niet opgenomen: hu_HU (spylls kan het niet lezen), nb_NO, nn_NO, el_GR en
    # tr_TR (5–9 s laden en 500–870 MB geheugen).
    CatalogDictionary('de_AT', 'Franz Michael Baumann (igerman98)', 'GPL 2 of 3', (
        RemoteFile('de/de_AT_frami.dic', 'de_AT.dic', 'd821e0a5a029b66df696c982a4cd55eb792139c33716ccbde364941db2448cbb', 4359309),
        RemoteFile('de/de_AT_frami.aff', 'de_AT.aff', '8b428f6215e36e145626e3d150cd0ffe273e1ad9a9ec0a1bbd31ee468ee39edc', 19068),
        RemoteFile('de/README_de_DE_frami.txt', 'LICENSE-de_AT.txt', 'c141f4f79c428b7348b5012836f4ad3db4d124f288f15effc22696dc876512ae', 752),
    )),
    CatalogDictionary('de_CH', 'Franz Michael Baumann (igerman98)', 'GPL 2 of 3', (
        RemoteFile('de/de_CH_frami.dic', 'de_CH.dic', '80a4df38cdc3e16d2f042f8eba4a99668ab9c075662e4262c62f8bba46c7bd16', 4358308),
        RemoteFile('de/de_CH_frami.aff', 'de_CH.aff', 'd86884be4c3f07e5e08057884856feabf2872b4e2f90a587a11376082bc4126b', 19068),
        RemoteFile('de/README_de_DE_frami.txt', 'LICENSE-de_CH.txt', 'c141f4f79c428b7348b5012836f4ad3db4d124f288f15effc22696dc876512ae', 752),
    )),
    CatalogDictionary('en_AU', 'SCOWL (Kevin Atkinson)', 'BSD-achtig (SCOWL)', (
        RemoteFile('en/en_AU.dic', 'en_AU.dic', 'aa07c46571f306b79fc1bc534357ed357af15687381b26f891ba66e8a2caed89', 554336),
        RemoteFile('en/en_AU.aff', 'en_AU.aff', 'e746c882dd6f303c2c46e7452804b9201115a6942cfeb15f18f8edf774d2e24e', 3205),
        RemoteFile('en/README_en_AU.txt', 'LICENSE-en_AU.txt', 'f0897dcfdf058bcfc93fbc8e7e1b5da4c27ae9e175ee3a9242e887f02eb84a8b', 15732),
    )),
    CatalogDictionary('en_CA', 'SCOWL (Kevin Atkinson)', 'BSD-achtig (SCOWL)', (
        RemoteFile('en/en_CA.dic', 'en_CA.dic', '53096689870246a78fa408b1e7a8c49bc140bd466a84a384cfb509445fff7173', 551583),
        RemoteFile('en/en_CA.aff', 'en_CA.aff', 'e746c882dd6f303c2c46e7452804b9201115a6942cfeb15f18f8edf774d2e24e', 3205),
        RemoteFile('en/README_en_CA.txt', 'LICENSE-en_CA.txt', '86700e39b2307dda4c087ad3505a1e634a5b4d518ab808c398a16d21ebe957e2', 15732),
    )),
    CatalogDictionary('en_ZA', 'Marco A.G. Pinto', 'LGPL', (
        RemoteFile('en/en_ZA.dic', 'en_ZA.dic', 'a438af6c6bfa9b25208d72c6ebf53507e178d6e6d285895e97870c36193433b1', 998279),
        RemoteFile('en/en_ZA.aff', 'en_ZA.aff', '5ddaf2bd123df16cbb887adf7dd835593200d0454703c461714886833c9ddec9', 43842),
        RemoteFile('en/README_en_ZA.txt', 'LICENSE-en_ZA.txt', '116ade99dd4a92715b21ae5b358a1a8cc814c76c0d6e582fdba4870835d1a6e2', 35563),
    )),
    CatalogDictionary('es_MX', 'RLA-ES', 'GPL 3 / LGPL 3 / MPL 1.1', (
        RemoteFile('es/es_MX.dic', 'es_MX.dic', '44ce35af220962c68f97962776639bef271f7d90a85ba924b539a36e33315f82', 723507),
        RemoteFile('es/es_MX.aff', 'es_MX.aff', 'd966cb748e4a688ed75ec84b50c0835ac438e5325ee4fce703a093794f9cba7e', 160081),
        RemoteFile('es/README_hunspell_es.txt', 'LICENSE-es_MX.txt', '0b5c39a863ecb61f5c5631ec1cd977667ef9bda6da6f90e80e9fc0edcbfadd97', 2615),
    )),
    CatalogDictionary('es_AR', 'RLA-ES', 'GPL 3 / LGPL 3 / MPL 1.1', (
        RemoteFile('es/es_AR.dic', 'es_AR.dic', '4fe3e193425bb3841ee218d36a9fc95d85b8daa8909363bdbba55a2f9f4e3d1d', 707817),
        RemoteFile('es/es_AR.aff', 'es_AR.aff', 'e9a96514295f8664db270d024c345700ccb9410a384eb71aec0fe5f0931d8c70', 171527),
        RemoteFile('es/README_hunspell_es.txt', 'LICENSE-es_AR.txt', '0b5c39a863ecb61f5c5631ec1cd977667ef9bda6da6f90e80e9fc0edcbfadd97', 2615),
    )),
    CatalogDictionary('cs_CZ', 'Miroslav Pošta (op basis van Petr Kolář)', 'GPL', (
        RemoteFile('cs_CZ/cs_CZ.dic', 'cs_CZ.dic', 'd8e8c88c006fdae72dac8c85df11b0c99a773e05a4ab0fcbe92244876668ca74', 3656362),
        RemoteFile('cs_CZ/cs_CZ.aff', 'cs_CZ.aff', '7ecb20620ecd46ebd9c36f3f33e69dd4eda385cba5b2bb4e6bc396d910e297f7', 111575),
        RemoteFile('cs_CZ/README_en.txt', 'LICENSE-cs_CZ.txt', '0fe6d017aa91ffb58146d19160f8207900cc0c49d5fffef0b1a7d3a364cb29bd', 13105),
    )),
    CatalogDictionary('sk_SK', 'sk-spell', 'GPL 2 / LGPL 2.1 / MPL 1.1', (
        RemoteFile('sk_SK/sk_SK.dic', 'sk_SK.dic', '3e3dbd5c6af8431a3a47652c69692f3f86d0cd82deb4418e49a057a33ef56063', 3362212),
        RemoteFile('sk_SK/sk_SK.aff', 'sk_SK.aff', 'af67bbe8ea9dea74968ec01acd266b3f74177ca087ee6eb7898c576e0aef7a3d', 225271),
        RemoteFile('sk_SK/README_en.txt', 'LICENSE-sk_SK.txt', 'a36af75654ae6e65614f7821b2c401ea1f3b4adfdcba9b59efcb1a06c96df14d', 2027),
    )),
    CatalogDictionary('ro_RO', 'Rospell', 'GPL 2 / LGPL 2.1 / MPL 1.1', (
        RemoteFile('ro/ro_RO.dic', 'ro_RO.dic', 'c26a9356f598a0ae89e7be650f6bdd9ba70acce66b41d7ab14c0c68639b6ed33', 2202394),
        RemoteFile('ro/ro_RO.aff', 'ro_RO.aff', '0c83a02f0ac5202c068e60e1aef5ce99e13d7f6c92ae8e68ca8b9e06829edfd1', 55195),
        RemoteFile('ro/README_EN.txt', 'LICENSE-ro_RO.txt', '854c3b7e6575da37d066d5a09945af336a8ecc62c5e3c1049e97504dc67cbd81', 1633),
    )),
    CatalogDictionary('ca_ES', 'Softcatalà', 'GPL / LGPL', (
        RemoteFile('ca/dictionaries/ca.dic', 'ca_ES.dic', '4838bb46776f5d82a3823aa7abb17cd00b9dc0c301d1b6d002e1ab6558fa07ca', 3086130),
        RemoteFile('ca/dictionaries/ca.aff', 'ca_ES.aff', 'abcca353b16af2d91be51d68899f47e5076a47489d08f696717fbac44074ddb8', 52471),
        RemoteFile('ca/LICENSES-en.txt', 'LICENSE-ca_ES.txt', 'e1931218994ce97e1d92fe57173838cd8a2c4de78fc4687f7e58bd2b3218272d', 85),
    )),
    CatalogDictionary('gl_ES', 'Proxecto Trasno (Hunspell-gl)', 'GPL', (
        RemoteFile('gl/gl_ES.dic', 'gl_ES.dic', '9c0b9128a73473fde3199e807a78252c39a3885db1d0db161a2b0fcd286c7a4b', 8325262),
        RemoteFile('gl/gl_ES.aff', 'gl_ES.aff', '76c848fc7704be8ea035926fb524b6379d572212f10eb8cb8e847e98442b2f3a', 1163541),
        RemoteFile('gl/README', 'LICENSE-gl_ES.txt', '1cf732806d5e30c414c72034cc9ab07a56e4525fb76a31adefc7a3aa22bd05f8', 992),
    )),
    CatalogDictionary('hr_HR', 'Krunoslav Šebetić e.a.', 'GPL 2 / LGPL 2.1 / MPL 1.1', (
        RemoteFile('hr_HR/hr_HR.dic', 'hr_HR.dic', '9c517653968a69389ee240b658b12c9db3ea00ce5415086ab76ade5a725e469d', 731819),
        RemoteFile('hr_HR/hr_HR.aff', 'hr_HR.aff', 'b33461b41ec30851f901af70dc44a2be6d3ad90196ff2d5b01e60695d8182465', 95802),
        RemoteFile('hr_HR/README_hr_HR.txt', 'LICENSE-hr_HR.txt', 'b850923a46efe6acb7d7fa5c314e9d413bcf0b039c67168266351936aa2d976f', 464),
    )),
    CatalogDictionary('sl_SI', 'Amebis, Tomaž Erjavec e.a.', 'GPL / LGPL', (
        RemoteFile('sl_SI/sl_SI.dic', 'sl_SI.dic', 'e157aabf1a20d21f639d04cf79f019ff1a3eb623c6780a726ffa4293787fa0ab', 2967766),
        RemoteFile('sl_SI/sl_SI.aff', 'sl_SI.aff', '3cb3e84824959928c8004e07b37b9d2bcb84176095f514e134f006dbb14a0beb', 14730),
        RemoteFile('sl_SI/README_sl_SI.txt', 'LICENSE-sl_SI.txt', '80e3fb8a78bf7c3cf1c76679ff1f11d4cb100440c9362553636b02edca005eb8', 2076),
    )),
    CatalogDictionary('bg_BG', 'BGOffice', 'GPL 2', (
        RemoteFile('bg_BG/bg_BG.dic', 'bg_BG.dic', '416f956a6e8f607565113eafc8bd35a4a5720df28c100b20e023845868b963cb', 1566331),
        RemoteFile('bg_BG/bg_BG.aff', 'bg_BG.aff', 'cb6bfc56d6b1e70c812061086d7ec5ad6aaf6d35acd927a035f1cee0188ea477', 58189),
        RemoteFile('bg_BG/COPYING', 'LICENSE-bg_BG.txt', '100035c1d3964e5528165e539619e2c5c01a421771daa43329809e06d779d692', 17979),
    )),
    CatalogDictionary('ru_RU', 'Alexander I. Lebedev', 'BSD-achtig', (
        RemoteFile('ru_RU/ru_RU.dic', 'ru_RU.dic', 'f6047416a0204adbecf3a451b874ec8a97ee37e2cbc714466ef04d8dbcc0d6fc', 3473191),
        RemoteFile('ru_RU/ru_RU.aff', 'ru_RU.aff', '38ce7d4af78e211e9bafe4bf7e3d6a2c420591136cb738ec6648f8fdf6524cd7', 71236),
        RemoteFile('ru_RU/README_ru_RU.txt', 'LICENSE-ru_RU.txt', '262af2f6ad70a61e5ee1332ff44fa8ee50edca819cf33207d8ad6ba6a0c9be52', 1886),
    )),
    CatalogDictionary('uk_UA', 'dict_uk (Andriy Rysin)', 'MPL 1.1', (
        RemoteFile('uk_UA/uk_UA.dic', 'uk_UA.dic', '2e5a9e67be63bdb089b3459addb5d71113319d13768e277bcae20f3cc1ad5a93', 8919324),
        RemoteFile('uk_UA/uk_UA.aff', 'uk_UA.aff', '2219dd15e9802adebc45722c60943b1472640260491af38dd3e43b07e75585e6', 211759),
        RemoteFile('uk_UA/README_uk_UA.txt', 'LICENSE-uk_UA.txt', '664436fee625b4a3e712483947d1711a2f467670f4c389bcf10abca2a564e1dc', 362),
    )),
    CatalogDictionary('lt_LT', 'Albertas Agejevas e.a.', 'BSD-achtig', (
        RemoteFile('lt_LT/lt.dic', 'lt_LT.dic', 'a751750b040623cf408cf1a3b6f6336141b55ac9519e54068dbeaa52eb395ccd', 1181184),
        RemoteFile('lt_LT/lt.aff', 'lt_LT.aff', '79c6f8304490d1c8b27ec93e509b2f635d9bb21d45a2d41c15162b18c8ff897c', 99714),
        RemoteFile('lt_LT/COPYING', 'LICENSE-lt_LT.txt', 'c5c73b4e3743ed2b959c70e886c4acee20d8654002ccdabac0a51af977ee2a17', 1520),
    )),
    CatalogDictionary('lv_LV', 'Dicollecte-LV', 'LGPL 2.1', (
        RemoteFile('lv_LV/lv_LV.dic', 'lv_LV.dic', 'bf7d054e28bc5e44df19410f3ed9d5fd8d6a4d8c051676650388c4e8d65c3148', 1844831),
        RemoteFile('lv_LV/lv_LV.aff', 'lv_LV.aff', 'a11f646c6905d6c96f3218ada4a6cf84129c9e6169720ac1a17f1707940a2890', 130475),
        RemoteFile('lv_LV/license.txt', 'LICENSE-lv_LV.txt', 'bb117c0fbd7f57f64170b690285d7df07c2371b578e3b3cd3aa2e1155ef461a0', 24390),
    )),
    CatalogDictionary('et_EE', 'Jaak Pruulmann', 'LGPL', (
        RemoteFile('et_EE/et_EE.dic', 'et_EE.dic', 'cd1378434aefeaa8a31f49369dbf71caf4e6340badb5c2cf7a55820933ed4f13', 4383841),
        RemoteFile('et_EE/et_EE.aff', 'et_EE.aff', '2fa53b7853762ec8c63ffa14b2d96d23433e3f2c2d3d218ad7c2461673099f95', 236336),
        RemoteFile('et_EE/README_et_EE.txt', 'LICENSE-et_EE.txt', '4cff6a48ea9168d545316ab96bac24eff4745bf198cbdd9f57eb10a9d8f93f0d', 55978),
    )),
    CatalogDictionary('af_ZA', 'Translate.org.za', 'LGPL', (
        RemoteFile('af_ZA/af_ZA.dic', 'af_ZA.dic', '8d806f90146059ea18b49c2352d188bd27dcc571a06815794facaa176aa5a5de', 1214886),
        RemoteFile('af_ZA/af_ZA.aff', 'af_ZA.aff', 'fdfcdd04d700fc4ac94be63930167fa942ee5ffb471b52a6f4e0c68362dd63d2', 4969),
        RemoteFile('af_ZA/README_af_ZA.txt', 'LICENSE-af_ZA.txt', 'e00c86cb0a1c0499380770750f545b5d0308d6cb35d25014cef6891c2fe5f255', 31492),
    )),
    CatalogDictionary('is_IS', 'hunspell-is', 'Publiek domein / CC BY-SA 3.0', (
        RemoteFile('is/is.dic', 'is_IS.dic', '8447594fd7eb1d6d43725c4ca49b00d3f00c4c4f3ac2f2b6dfe3f56eb211d280', 2454138),
        RemoteFile('is/is.aff', 'is_IS.aff', '0168050c64a369c55b5aeb61f9dfe484d2aa7512d78bb3fa36779ea24b467c50', 309734),
        RemoteFile('is/license.txt', 'LICENSE-is_IS.txt', 'a852be66ff244eb15563a39631e7d4663811ee8e5d66682e653a989e57cd13fe', 34802),
    )),
    CatalogDictionary('id_ID', 'hunspell-id', 'LGPL 3', (
        RemoteFile('id/id_ID.dic', 'id_ID.dic', '775ff17a52801f3d2ee80120952fb44cc9bac6c3cf61740de775e439851a5803', 453700),
        RemoteFile('id/id_ID.aff', 'id_ID.aff', 'c625d5b237a489c452cf1f9c666600103e8093667dff89e7030a24217995dc79', 15274),
        RemoteFile('id/LICENSE-dict', 'LICENSE-id_ID.txt', '97628afebc60f026f5c2b25d7491c46a5c4ee61f693e7cfa07fbd2c03605979b', 7652),
    )),
)
CATALOG_BY_LOCALE = {entry.locale: entry for entry in CATALOG}


def installed_marker(root: Path, locale: str) -> dict | None:
    path = Path(root) / locale / MARKER
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def is_installed(root: Path, locale: str) -> bool:
    folder = Path(root) / locale
    return (folder / f'{locale}.dic').is_file() and (folder / f'{locale}.aff').is_file()


_HASH_CACHE: dict[str, tuple[int, int, str]] = {}


def _file_sha256(path: Path) -> str | None:
    """SHA-256 van een bestand; onthouden zolang wijzigtijd en grootte gelijk blijven."""
    try:
        stat = os.stat(path)
    except OSError:
        return None
    key = str(path)
    cached = _HASH_CACHE.get(key)
    if cached is not None and cached[:2] == (stat.st_mtime_ns, stat.st_size):
        return cached[2]
    digest = hashlib.sha256()
    try:
        with open(path, 'rb') as handle:
            for chunk in iter(lambda: handle.read(CHUNK), b''):
                digest.update(chunk)
    except OSError:
        return None
    _HASH_CACHE[key] = (stat.st_mtime_ns, stat.st_size, digest.hexdigest())
    return digest.hexdigest()


def update_available(root: Path, entry: CatalogDictionary) -> bool:
    """Is er een nieuwere versie van een woordenboek dat QuietWriter zelf downloadde?

    Alleen woordenboeken met ons downloadbriefje (``MARKER``): een zelf
    toegevoegd .dic-bestand wordt nooit "bijgewerkt". Een nieuwere versie
    betekent: de .dic of .aff op schijf wijkt af van de controlesom in de
    lijst van deze QuietWriter (nieuwere woordenboeken komen met een nieuwe
    QuietWriter; er wordt nooit online gekeken).
    """
    root = Path(root)
    if not is_installed(root, entry.locale) or installed_marker(root, entry.locale) is None:
        return False
    folder = root / entry.locale
    for remote in entry.files:
        if remote.local.endswith(('.dic', '.aff')):
            if _file_sha256(folder / remote.local) != remote.sha256:
                return True
    return False


def updates_available(root: Path) -> list[CatalogDictionary]:
    return [entry for entry in CATALOG if update_available(root, entry)]


def _download(url: str, target: Path, expected: RemoteFile, progress, done_before: int, total: int,
              cancelled, opener) -> int:
    request = Request(url, headers={'User-Agent': 'QuietWriter dictionary download'})
    digest = hashlib.sha256()
    received = 0
    with opener(request, timeout=60) as response, open(target, 'wb') as out:
        while True:
            if cancelled is not None and cancelled():
                raise DownloadCancelled()
            chunk = response.read(CHUNK)
            if not chunk:
                break
            received += len(chunk)
            if received > expected.size:
                raise DownloadFailed(f'{expected.local}: groter dan verwacht')
            digest.update(chunk)
            out.write(chunk)
            if progress is not None:
                progress(int((done_before + received) * 100 / max(1, total)))
    if received != expected.size or digest.hexdigest() != expected.sha256:
        raise DownloadFailed(f'{expected.local}: controle mislukt')
    return received


def _retry(action, attempts: int = 12, delay: float = 0.25):
    """Probeer een bestandsactie opnieuw als Windows hem even weigert.

    Dropbox, OneDrive of een virusscanner houdt een net geschreven bestand soms
    een moment vast ("Toegang geweigerd", WinError 5/32). Na een korte pauze lukt
    het dan meestal wel.
    """
    for attempt in range(attempts):
        try:
            return action()
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)


def install(entry: CatalogDictionary, root: Path, *, progress=None, cancelled=None, opener=urlopen,
            staging_parent: Path | None = None) -> Path:
    """Download, controleer en plaats één woordenboek in ``root/<locale>/``.

    1.7: er wordt gedownload in de tijdelijke map van het systeem, dus buiten een
    eventuele Dropbox-werkmap, en er wordt geen map hernoemd. Elk bestand wordt
    apart en atomair op zijn plek gezet (``os.replace``, met herpogingen). Gaat
    dat mis, dan komen de vorige bestanden terug (``_place_with_backups``).
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'quietwriter-{entry.locale}-', dir=staging_parent))
    target = root / entry.locale
    try:
        done = 0
        for remote in entry.files:
            done += _download(RAW_BASE + remote.remote, staging / remote.local, remote, progress, done,
                              entry.size, cancelled, opener)
        (staging / MARKER).write_text(json.dumps({
            'source': SOURCE_REPO, 'commit': SOURCE_COMMIT, 'locale': entry.locale,
            'author': entry.author, 'license': entry.license,
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        if cancelled is not None and cancelled():
            raise DownloadCancelled()
        target.mkdir(parents=True, exist_ok=True)
        # Eerst .aff en de bijlagen, dan .dic (de catalogus ziet een woordenboek pas
        # als de .dic er is), het downloadbriefje als allerlaatste.
        order = sorted((staging / name for name in os.listdir(staging)),
                       key=lambda path: (path.name == MARKER, path.suffix == '.dic', path.name))
        _place_with_backups(order, target)
        if progress is not None:
            progress(100)
        return target
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _atomic_copy(source: Path, final: Path) -> None:
    """Kopieer naar een tijdelijk bestand naast ``final`` en zet het in één keer op zijn plek."""
    temporary = final.parent / f'.{final.name}.{uuid.uuid4().hex[:8]}.tmp'
    try:
        # Kopiëren ook binnen try: een half geschreven .tmp wordt dan ook opgeruimd
        # (ChatGPT-herreview dev16).
        shutil.copyfile(source, temporary)
        _retry(lambda: os.replace(temporary, final))
    except BaseException:
        try:
            _retry(lambda: temporary.unlink(missing_ok=True), attempts=3)
        except OSError:
            pass
        raise


def _place_with_backups(order: list[Path], target: Path) -> None:
    """Zet de bestanden één voor één atomair neer; bij een fout komt alles terug.

    ChatGPT-review dev15: het vorige bestand wordt eerst als reservekopie naast
    het origineel gezet (``.naam.<id>.vorige``) en bij terugzetten weer atomair
    teruggeplaatst, nooit rechtstreeks overschreven. Lukt terugzetten niet
    helemaal, dan blijven de reservekopieën staan en volgt ``RollbackIncomplete``.
    """
    placed: list[tuple[Path, Path | None]] = []   # (doel, reservekopie of None als het nieuw was)
    try:
        for source in order:
            final = target / source.name
            backup = None
            if final.exists():
                backup = target / f'.{source.name}.{uuid.uuid4().hex[:8]}.vorige'
                shutil.copyfile(final, backup)
            try:
                _atomic_copy(source, final)
            except BaseException:
                if backup is not None:
                    backup.unlink(missing_ok=True)   # het origineel staat er nog
                raise
            placed.append((final, backup))
    except BaseException as exc:
        left_behind = []
        for final, backup in reversed(placed):
            try:
                if backup is None:
                    _retry(lambda: final.unlink(missing_ok=True), attempts=4)
                else:
                    _atomic_copy(backup, final)
                    if _file_sha256(final) != _file_sha256(backup):
                        raise OSError(f'{final.name}: terugzetten klopt niet')
                    backup.unlink(missing_ok=True)
            except OSError:
                if backup is not None:
                    left_behind.append(backup)
                else:
                    left_behind.append(final)
        if left_behind:
            raise RollbackIncomplete(
                f'{exc}; het vorige woordenboek kon niet helemaal terug. Reservekopie: '
                + ', '.join(str(path) for path in left_behind), left_behind) from exc
        raise
    for _final, backup in placed:
        if backup is not None:
            try:
                _retry(lambda: backup.unlink(missing_ok=True), attempts=4)
            except OSError:
                pass   # een vergeten reservekopie is onschuldig; de catalogus negeert hem


def remove_extras(folder: Path, locale: str) -> None:
    """Ruim de bijlagen van een gedownload woordenboek op (na verwijderen van .dic/.aff)."""
    for name in (MARKER, f'LICENSE-{locale}.txt'):
        try:
            (Path(folder) / name).unlink(missing_ok=True)
        except OSError:
            pass
