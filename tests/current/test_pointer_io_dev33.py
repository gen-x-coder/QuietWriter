"""No silent older launch on a temporarily unreadable pointer."""
import pytest
from quietwriter import versioned_install as mod
from .test_versioned_install_dev31 import build


def test_pointer_transient_read_error_aborts_instead_of_downgrade(tmp_path, monkeypatch):
    build(tmp_path, '1.5.0')
    mod.initialize(tmp_path, 'app-1.5.0')
    original = mod.Path.read_text
    def blocked(self, *args, **kwargs):
        if self.name == 'current.b.json':
            raise PermissionError('temporarily locked')
        return original(self, *args, **kwargs)
    monkeypatch.setattr(mod.Path, 'read_text', blocked)
    monkeypatch.setattr(mod.time, 'sleep', lambda _: None)
    with pytest.raises(mod.VersionedInstallError, match='unreadable'):
        mod.read_active(tmp_path)
