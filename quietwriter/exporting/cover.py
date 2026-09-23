from __future__ import annotations

from dataclasses import dataclass

from .models import ExportAsset


@dataclass(frozen=True)
class RenderedCover:
    filename: str
    media_type: str
    data: bytes


def render_cover(asset: ExportAsset, title: str, author: str, mode: str) -> RenderedCover:
    """Return an EPUB-safe cover image.

    ``artwork_with_text`` keeps JPEG/PNG artwork untouched. ``artwork_only``
    overlays title and author using Qt, which is already part of QuietWriter.
    WEBP is converted to PNG for broad e-reader compatibility.
    """
    if mode == 'artwork_with_text' and asset.media_type in {'image/jpeg', 'image/png'}:
        ext = '.jpg' if asset.media_type == 'image/jpeg' else '.png'
        return RenderedCover('cover' + ext, asset.media_type, asset.data)

    try:
        from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRect, Qt
        from PySide6.QtGui import QColor, QFont, QImage, QPainter
    except Exception as exc:  # pragma: no cover - application dependency at runtime
        raise RuntimeError('De boekomslag kon niet worden verwerkt omdat Qt-afbeeldingsondersteuning ontbreekt.') from exc

    image = QImage.fromData(asset.data)
    if image.isNull():
        raise ValueError('De boekomslag kon niet worden gelezen.')
    # Work in a predictable ARGB surface for composition/conversion.
    image = image.convertToFormat(QImage.Format_ARGB32)

    if mode == 'artwork_only':
        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            w, h = image.width(), image.height()
            band_top = int(h * 0.58)
            painter.fillRect(QRect(0, band_top, w, h - band_top), QColor(0, 0, 0, 150))

            margin = max(24, int(w * 0.075))
            title_rect = QRect(margin, band_top + int(h * 0.045), w - 2 * margin, int(h * 0.20))
            author_rect = QRect(margin, band_top + int(h * 0.26), w - 2 * margin, int(h * 0.08))

            title_font = QFont('Georgia')
            title_font.setBold(True)
            title_font.setPixelSize(max(34, int(w * 0.070)))
            author_font = QFont('Georgia')
            author_font.setPixelSize(max(22, int(w * 0.038)))

            # A small shadow plus the translucent band keeps the deliberately
            # simple cover treatment readable on both light and dark artwork.
            painter.setFont(title_font)
            painter.setPen(QColor(0, 0, 0, 155))
            painter.drawText(title_rect.translated(2, 3), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, title)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, title)
            if author:
                painter.setFont(author_font)
                painter.setPen(QColor(0, 0, 0, 155))
                painter.drawText(author_rect.translated(1, 2), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, author)
                painter.setPen(QColor(245, 245, 245))
                painter.drawText(author_rect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, author)
        finally:
            painter.end()

    payload = QByteArray()
    buffer = QBuffer(payload)
    buffer.open(QIODevice.WriteOnly)
    if not image.save(buffer, 'PNG'):
        buffer.close()
        raise ValueError('De boekomslag kon niet naar PNG worden omgezet.')
    buffer.close()
    return RenderedCover('cover.png', 'image/png', bytes(payload))
