import hashlib
import json
import pytest
from quietwriter.update_install_readiness import audit_portable_install, InstallReadinessError


def fixture(tmp_path):
    root = tmp_path / 'portable'
    (root / '_internal').mkdir(parents=True)
    contents = {'QuietWriter.exe': b'MZ code', '_internal/qw.bin': b'build'}
    for name, data in contents.items():
        (root / name).write_bytes(data)
    spec = {'schema': 1, 'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in contents.items()}}
    (root / 'qw-release-files.json').write_text(json.dumps(spec), encoding='utf-8')
    return root


def test_valid_audit_is_read_only(tmp_path):
    root = fixture(tmp_path)
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert audit_portable_install(root)['verified_files'] == 2
    assert before == {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}

@pytest.mark.parametrize('change', ['unknown', 'book', 'changed', 'missing', 'tampered', 'extra_inventory', 'duplicate_case', 'bad_digest'])
def test_untrusted_install_refused(tmp_path, change):
    root = fixture(tmp_path)
    inventory = root / 'qw-release-files.json'
    if change == 'unknown': (root / 'strange.txt').write_text('x')
    if change == 'book': (root / 'Mijn boeken').mkdir(); (root / 'Mijn boeken' / 'boek.json').write_text('{}')
    if change == 'changed': (root / '_internal/qw.bin').write_bytes(b'evil!')
    if change == 'missing': (root / '_internal/qw.bin').unlink()
    if change in ('tampered','extra_inventory','duplicate_case','bad_digest'):
        data = json.loads(inventory.read_text())
        if change == 'tampered': data['files']['QuietWriter.exe']['size'] = 999
        if change == 'extra_inventory': data['files']['missing.txt'] = {'size':0, 'sha256':'0'*64}
        if change == 'duplicate_case': data['files']['quietwriter.EXE'] = data['files']['QuietWriter.exe']
        if change == 'bad_digest': data['files']['QuietWriter.exe']['sha256'] = 'Z'*64
        inventory.write_text(json.dumps(data))
    with pytest.raises(InstallReadinessError): audit_portable_install(root)


def test_directory_symlink_refused_if_supported(tmp_path):
    root = fixture(tmp_path)
    try: (root / 'link').symlink_to(root / '_internal', target_is_directory=True)
    except (OSError, NotImplementedError): pytest.skip('Directory symlinks unavailable')
    with pytest.raises(InstallReadinessError, match='Linked'): audit_portable_install(root)
