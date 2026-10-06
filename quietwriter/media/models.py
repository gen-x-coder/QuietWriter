from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaAsset:
    id: str
    file: str
    media_type: str
    original_name: str
    width: int
    height: int
    sha256: str
    size: int

    @classmethod
    def from_dict(cls, asset_id: str, data: dict) -> 'MediaAsset':
        return cls(
            id=str(asset_id),
            file=str(data.get('file') or ''),
            media_type=str(data.get('media_type') or ''),
            original_name=str(data.get('original_name') or ''),
            width=int(data.get('width') or 0),
            height=int(data.get('height') or 0),
            sha256=str(data.get('sha256') or ''),
            size=int(data.get('size') or 0),
        )

    def to_dict(self) -> dict:
        return {
            'file': self.file,
            'media_type': self.media_type,
            'original_name': self.original_name,
            'width': self.width,
            'height': self.height,
            'sha256': self.sha256,
            'size': self.size,
        }
