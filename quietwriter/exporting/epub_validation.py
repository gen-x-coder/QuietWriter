from __future__ import annotations

import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


OCF_NS = 'urn:oasis:names:tc:opendocument:xmlns:container'
OPF_NS = 'http://www.idpf.org/2007/opf'
DC_NS = 'http://purl.org/dc/elements/1.1/'
XHTML_NS = 'http://www.w3.org/1999/xhtml'
EPUB_NS = 'http://www.idpf.org/2007/ops'
XML_NS = 'http://www.w3.org/XML/1998/namespace'


class EpubValidationError(ValueError):
    """Raised when QuietWriter's generated EPUB fails an internal integrity check."""


@dataclass(frozen=True)
class EpubValidationReport:
    resource_count: int
    xhtml_count: int
    spine_count: int
    navigation_target_count: int


def _fail(message: str) -> None:
    raise EpubValidationError(f'EPUB-interne controle mislukt: {message}')


def _parse_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        data = zf.read(name)
    except KeyError:
        _fail(f'bestand ontbreekt: {name}')
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        _fail(f'ongeldige XML in {name}: {exc}')
    raise AssertionError('unreachable')


def _resolve_local(base_name: str, href: str) -> tuple[str, str] | None:
    """Resolve an EPUB-local URL to ``(archive_path, fragment)``.

    External URLs and data/mail links are deliberately ignored: they are not
    resources QuietWriter packages and are outside this archive-integrity pass.
    """
    raw = str(href or '').strip()
    if not raw:
        return None
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    fragment = unquote(parsed.fragment)
    if not path:
        target = base_name
    else:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(base_name), path))
    if target.startswith('../') or target == '..' or target.startswith('/'):
        _fail(f'onveilige lokale verwijzing in {base_name}: {raw}')
    return target, fragment


def _ids_in(root: ET.Element) -> set[str]:
    ids: set[str] = set()
    for element in root.iter():
        value = element.get('id') or element.get(f'{{{XML_NS}}}id')
        if value:
            ids.add(value)
    return ids


def _validate_target(
    *,
    names: set[str],
    parsed_docs: dict[str, ET.Element],
    base_name: str,
    href: str,
) -> bool:
    resolved = _resolve_local(base_name, href)
    if resolved is None:
        return False
    target, fragment = resolved
    if target not in names:
        _fail(f'verwijzing uit {base_name} wijst naar ontbrekend bestand: {href}')
    if fragment:
        root = parsed_docs.get(target)
        if root is None and target.endswith(('.xhtml', '.html', '.xml', '.opf')):
            # Caller pre-parses the generated XML documents, but stay defensive.
            return True
        if root is not None and fragment not in _ids_in(root):
            _fail(f'verwijzing uit {base_name} wijst naar ontbrekend fragment: {href}')
    return True


def validate_epub_archive(path) -> EpubValidationReport:
    """Validate QuietWriter-specific EPUB 3 archive integrity.

    This intentionally does not replace EPUBCheck. It checks the structural and
    referential invariants QuietWriter itself creates so a broken generated
    archive is rejected before it replaces a previous export.
    """
    try:
        zf = zipfile.ZipFile(path, 'r')
    except (OSError, zipfile.BadZipFile) as exc:
        raise EpubValidationError(f'EPUB-interne controle mislukt: onleesbare ZIP: {exc}') from exc

    with zf:
        infos = zf.infolist()
        if not infos or infos[0].filename != 'mimetype':
            _fail('mimetype is niet het eerste ZIP-item')
        if infos[0].compress_type != zipfile.ZIP_STORED:
            _fail('mimetype is gecomprimeerd')
        if zf.read('mimetype') != b'application/epub+zip':
            _fail('mimetype heeft niet de verplichte waarde application/epub+zip')

        names = set(zf.namelist())
        if 'META-INF/container.xml' not in names:
            _fail('META-INF/container.xml ontbreekt')

        container = _parse_xml(zf, 'META-INF/container.xml')
        rootfiles = container.findall(f'.//{{{OCF_NS}}}rootfile')
        if not rootfiles:
            _fail('container.xml bevat geen package-rootfile')
        package_name = str(rootfiles[0].get('full-path') or '').strip()
        if not package_name or package_name not in names:
            _fail('container.xml verwijst niet naar een bestaand package-document')

        package = _parse_xml(zf, package_name)
        if package.tag != f'{{{OPF_NS}}}package':
            _fail('package-document heeft niet het EPUB OPF package-element als root')
        if str(package.get('version') or '') != '3.0':
            _fail('package-document is geen EPUB 3 package (version="3.0")')

        unique_identifier = str(package.get('unique-identifier') or '').strip()
        identifiers = {
            str(node.get('id') or ''): (node.text or '').strip()
            for node in package.findall(f'.//{{{DC_NS}}}identifier')
            if node.get('id')
        }
        if not unique_identifier or not identifiers.get(unique_identifier):
            _fail('unique-identifier verwijst niet naar een ingevulde dc:identifier')

        manifest_nodes = package.findall(f'.//{{{OPF_NS}}}manifest/{{{OPF_NS}}}item')
        if not manifest_nodes:
            _fail('manifest is leeg')

        manifest_by_id: dict[str, str] = {}
        manifest_hrefs: set[str] = set()
        nav_items: list[str] = []
        cover_items = 0
        for node in manifest_nodes:
            item_id = str(node.get('id') or '').strip()
            href = str(node.get('href') or '').strip()
            media_type = str(node.get('media-type') or '').strip()
            props = set(str(node.get('properties') or '').split())
            if not item_id or not href or not media_type:
                _fail('manifest bevat een item zonder id, href of media-type')
            if item_id in manifest_by_id:
                _fail(f'dubbel manifest-id: {item_id}')
            if href in manifest_hrefs:
                _fail(f'dubbele manifest-href: {href}')
            resolved = _resolve_local(package_name, href)
            if resolved is None:
                _fail(f'manifest bevat een niet-lokale publicatieresource: {href}')
            archive_name, _fragment = resolved
            if archive_name not in names:
                _fail(f'manifest-resource ontbreekt in EPUB: {href}')
            manifest_by_id[item_id] = archive_name
            manifest_hrefs.add(href)
            if 'nav' in props:
                nav_items.append(archive_name)
            if 'cover-image' in props:
                cover_items += 1

        if len(nav_items) != 1:
            _fail(f'manifest moet precies één nav-resource bevatten; gevonden: {len(nav_items)}')
        if cover_items > 1:
            _fail('manifest bevat meer dan één cover-image')

        spine_nodes = package.findall(f'.//{{{OPF_NS}}}spine/{{{OPF_NS}}}itemref')
        if not spine_nodes:
            _fail('spine is leeg')
        spine_ids: list[str] = []
        for node in spine_nodes:
            idref = str(node.get('idref') or '').strip()
            if not idref or idref not in manifest_by_id:
                _fail(f'spine verwijst naar onbekend manifest-id: {idref or "<leeg>"}')
            spine_ids.append(idref)

        # Parse generated XML documents once for link/fragment validation.
        parsed_docs: dict[str, ET.Element] = {}
        for archive_name in names:
            if archive_name.endswith(('.xhtml', '.opf', '.xml')):
                parsed_docs[archive_name] = _parse_xml(zf, archive_name)

        nav_name = nav_items[0]
        nav_root = parsed_docs[nav_name]
        toc_nodes = [
            node for node in nav_root.findall(f'.//{{{XHTML_NS}}}nav')
            if 'toc' in str(node.get(f'{{{EPUB_NS}}}type') or '').split()
        ]
        if len(toc_nodes) != 1:
            _fail(f'navigatiedocument moet precies één toc-nav bevatten; gevonden: {len(toc_nodes)}')

        navigation_targets = 0
        for node in nav_root.findall(f'.//{{{XHTML_NS}}}a'):
            href = str(node.get('href') or '')
            if _validate_target(
                names=names,
                parsed_docs=parsed_docs,
                base_name=nav_name,
                href=href,
            ):
                navigation_targets += 1

        # Validate all local links/assets emitted into XHTML. This catches stale
        # ToC anchors, missing images and bad stylesheet/resource paths.
        for archive_name, root in parsed_docs.items():
            if not archive_name.endswith('.xhtml'):
                continue
            for element in root.iter():
                for attr in ('href', 'src'):
                    href = element.get(attr)
                    if href:
                        _validate_target(
                            names=names,
                            parsed_docs=parsed_docs,
                            base_name=archive_name,
                            href=href,
                        )

        xhtml_count = sum(1 for name in names if name.endswith('.xhtml'))
        return EpubValidationReport(
            resource_count=len(manifest_nodes),
            xhtml_count=xhtml_count,
            spine_count=len(spine_ids),
            navigation_target_count=navigation_targets,
        )
